# Standard library
from datetime import datetime as dt
from datetime import timedelta

# Third party
from gluonts.model import deepar
from gluonts.mx.trainer import Trainer
from gluonts.dataset.common import ListDataset
import pandas as pd
from pymongo import MongoClient, ReplaceOne, UpdateOne
import quandl

PERIODS = 21
DYNAMIC_FEATS = [
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
    "Dividend",
    "Split",
    "Adj_Open",
    "Adj_High",
    "Adj_Low",
    "Adj_Volume"
]

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
    """Upserts mongo db[forecasts] collection"""
    df = self.get_symbols_df()

    split_date = dt.strftime(
      dt.strptime(
        df.date.max(),
        "%Y-%m-%d"
      ) - timedelta(periods),
      "%Y-%m-%d"
    )

    train_df = df[df.date < split_date]
    test_df = df[df.date >= split_date]


    def _to_list_dataset(_df):
        dfc = _df.copy()
        dfc.index = dfc.date
        datasets = [
            {
              'start': group.index[0],
              'target': group.Adj_Close,
              "dynamic_feat": group[DYNAMIC_FEATS].values,
              "cat": hash(symbol)
            } for symbol, group in dfc.groupby(["symbol"])
        ]
        return ListDataset(datasets, freq="D")

    train_dataset = _to_list_dataset(train_df)
    test_dataset = _to_list_dataset(test_df)

    trainer = Trainer(epochs=5)
    estimator = deepar.DeepAREstimator(
        freq="D",
        prediction_length=periods*2,
        trainer=trainer,
        context_length=365 
    )

    predictor = estimator.train(train_dataset)

    predictions = pd.DataFrame.from_records(
        [prediction.mean for prediction in predictor.predict(test_dataset)]
    )

    predictions.columns = [
        dt.strftime(dt.strptime(split_date, "%Y-%m-%d") + timedelta(i), "%Y-%m-%d")
        for i in range(periods*2)
    ]
    predictions["symbol"] = test_df.groupby(["symbol"]).groups
    predictions = predictions.set_index(["symbol"]).unstack().sort_index(level=1).reset_index()
    predictions = predictions.rename(columns={"level_0": "date", 0: "y_hat"})
    predictions["_id"] = predictions["date"] + "-" + predictions["symbol"]
    predictions["last_updated"] = dt.strftime(dt.now(), "%Y-%m-%d")

    print("Loading records to Mongo")
    records = predictions.to_dict("records")

    updates = self._to_batch_replacements(records)

    result = self._mongo_db["forecasts"].bulk_write(updates)
    print("Records loaded")

    return result
