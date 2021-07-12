# Standard library
from datetime import datetime as dt

# Third party
import pandas as pd
from pymongo import MongoClient, ReplaceOne, UpdateOne
import quandl

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


  def forecast_symbol(self, symbol, periods=7):
    """Upserts mongo db[<symbol>-forecast] collection"""
    df = self.get_symbols_df()

    # TODO
    # predictions = predict(df)

    # print("Loading records to Mongo")
    # records = predictions.to_dict("records")

    # updates = self._to_batch_replacements(self, records)

    # result = self._mongo_db[symbol + "-forecasts"].bulk_write(updates)
    # print("Records loaded")

    # return result

    return
