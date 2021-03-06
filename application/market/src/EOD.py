# Standard library
from datetime import datetime as dt
from datetime import timedelta

# Third party
from gluonts.model import deepar
from gluonts.mx.trainer import Trainer
from gluonts.dataset.common import ListDataset
import numpy as np
import pandas as pd
from pymongo import MongoClient, ReplaceOne, UpdateOne
import quandl

PERIODS = 7
DAY = 24*60*60
WEEK = 7*DAY
YEAR = (365.2425)*DAY

class EOD(object):
  def __init__(
    self,
    quandl_api_key,
    mongo_username=None,
    mongo_password=None,
    mongo_host="host.minikube.internal",
    mongo_port=27017
  ):
    self._mongo_db = MongoClient(
      'mongodb://%s:%s' % (mongo_host, mongo_port),
      username=mongo_username,
      password=mongo_password
    )['eod']
    self._quandl_api_key = quandl_api_key
    quandl.ApiConfig.api_key = self._quandl_api_key


  # Forces document update: _to_batch_updates can be used to patch documents
  def _to_batch_replacements(self, records):
    replacements = [
      ReplaceOne(
        {'_id': record["_id"]},
        record,
        upsert=True
      ) for record in records
    ]

    return replacements


  def _to_batch_updates(self, records):
    updates = [
      UpdateOne(
        {'_id': record["_id"]},
        {"$set": record},
        upsert=True
      ) for record in records
    ]

    return updates


  def set_symbols(self, symbols):
    """Upserts mongo db[symbols] collection using symbols list"""
    updates = self._to_batch_updates(symbols)

    result = self._mongo_db["symbols"].bulk_write(updates)
    print("Records loaded")

    return result


  def get_symbols(self, filter={}):
    """Returns mongo db[symbols] collection"""
    return list(self._mongo_db["symbols"].find(filter))


  def update_symbol_collection(self, symbol):
    """Upserts mongo db[<symbol>] collection"""
    print("Requesting Quandl EOD set for symbol", symbol)
    eod = quandl.get('EOD/' + symbol)
    print(eod.count().max(), "records obtained")

    eod["_id"] = eod.index.strftime("%Y-%m-%d")
    eod["last_updated"] = dt.strftime(dt.now(), "%Y-%m-%d")

    print("Loading records to Mongo")
    records = eod.to_dict("records")

    updates = self._to_batch_replacements(records)

    result = self._mongo_db[symbol].bulk_write(updates)
    print("Records loaded")

    return result


  def get_symbol_df(self, symbol):
    """Returns all documents in mongo db[<symbol>] collection as dataframe"""
    print("Loading Mongo EOD collection for symbol", symbol)
    try:
      df = pd.DataFrame.from_records(self._mongo_db[symbol].find({}))
      print(df.count().max(), "documents found")

      # Assign row GUID's, retain symbol
      df["symbol"] = symbol
      df["date"] = df["_id"]
      df["_id"] = df["_id"] + "-" + df["symbol"]
    except KeyError:
      print(
        "_id not found. %s collection is malformed or non-existent" % symbol
      )
      print("Returning empty dataframe")
      df = pd.DataFrame()

    return df


  def get_symbols_df(self, filter={"status": "ACTIVE"}):
    """Returns symbol documents for all symbols matching db[symbols] filter"""
    symbols = self.get_symbols(filter)

    return pd.concat(
      [self.get_symbol_df(symbol["_id"]) for symbol in symbols]
    )


  def update_symbol_forecasts(self, periods=PERIODS):
    """Upserts mongo db[forecasts] collection using gluonts"""
    def _resample_groups(_df):
      dfc = _df.copy()
      dfc.index = pd.to_datetime(dfc.date)
      dfc = dfc.groupby(["symbol"]).resample("D").pad()
      dfc = dfc.drop(columns=["date", "symbol"])
      dfc = dfc.reset_index()
      dfc.date = dfc.date.apply(lambda x: x.strftime("%Y-%m-%d"))

      return dfc


    def _to_list_dataset(_df):
        dfc = _df.copy()
        dfc.index = dfc.date
        datasets = [
            {
              'start': group.index[0],
              'target': group.Adj_Close,
              "cat": hash(symbol)
            } for symbol, group in dfc.groupby(["symbol"])
        ]

        return ListDataset(datasets, freq="D")


    # Pull all symbols to pandas dataframe
    df = self.get_symbols_df()

    # Resample each symbol to fill in missing dates
    df = _resample_groups(df)

    split_date = dt.strftime(
      dt.strptime(
        df.date.max(),
        "%Y-%m-%d"
      ) - timedelta(periods),
      "%Y-%m-%d"
    )

    train_df = df[df.date < split_date]
    forecast_df = df.copy()

    train_dataset = _to_list_dataset(train_df)
    forecast_dataset = _to_list_dataset(forecast_df)

    trainer = Trainer()
    estimator = deepar.DeepAREstimator(
        freq="D",
        prediction_length=periods,
        trainer=trainer
    )

    predictor = estimator.train(train_dataset)

    predictions = pd.DataFrame.from_records([
        prediction.mean
        for prediction in predictor.predict(forecast_dataset)
    ])

    predictions.columns = [
      dt.strftime(
        dt.strptime(df.date.max(), "%Y-%m-%d") + timedelta(i+1),
        "%Y-%m-%d"
      ) for i in range(periods)
    ]
    predictions["symbol"] = forecast_df.groupby(["symbol"]).groups
    predictions = predictions.set_index(
      ["symbol"]
    ).unstack().sort_index(level=1).reset_index()
    predictions = predictions.rename(columns={"level_0": "date", 0: "y_hat"})
    predictions["_id"] = predictions["date"] + "-" + predictions["symbol"]
    predictions["last_updated"] = dt.strftime(dt.now(), "%Y-%m-%d")
    predictions["type"] = "gluonts"

    print("Loading records to Mongo")
    records = predictions.to_dict("records")

    updates = self._to_batch_replacements(records)

    result = self._mongo_db["forecasts"].bulk_write(updates)
    print("Records loaded")

    return result
