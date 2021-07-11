# Standard library
from datetime import datetime as dt

# Third party
import pandas as pd
from prophet import Prophet
from pymongo import MongoClient, ReplaceOne, UpdateOne
import quandl

class EOD(object):
  def __init__(self, mongo_username, mongo_password, quandl_api_key):
    self._mongo_db = MongoClient(
      'mongodb://mongo:27017',
      username=mongo_username,
      password=mongo_password
    )['eod']
    self._quandl_api_key = quandl_api_key
    quandl.ApiConfig.api_key = self._quandl_api_key


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


  def update_symbol(self, symbol):
    """Upserts mongo db[symbol] collection"""
    print("Requesting Quandl EOD set for symbol", symbol)
    eod = quandl.get('EOD/' + symbol)
    print(eod.count().max(), "records obtained")

    eod["_id"] = eod.index.strftime("%Y-%m-%d")
    eod["last_updated"] = dt.strftime(dt.now(), "%Y-%m-%d")

    print("Loading records to Mongo")
    records = eod.to_dict("records")

    # Forces document update
    #   _to_batch_updates can be use to patch documents
    updates = self._to_batch_replacements(self, records)

    result = self._mongo_db[symbol].bulk_write(updates)
    print("Records loaded")

    return result


  def forecast_symbol(self, symbol, periods=7):
    """Upserts mongo db[<symbol>-forecast] collection"""
    print("Loading Mongo EOD collection for symbol", symbol)
    df = pd.DataFrame.from_records(self._mongo_db[symbol].find({}))
    print(df.count().max(), "documents found")

    df = df.rename(columns={"_id": "ds", "Adj_Close": "y"})

    print("Training forecast model")
    m = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=True
    ).add_country_holidays(country_name='US')
    m.fit(df)

    print("Generating forecasts")
    future = m.make_future_dataframe(periods, "D", include_history=False)
    predictions = m.predict(future)
  
    predictions["_id"] = dt.strftime(dt.now(), "%Y-%m-%d") \
      + "-" \
      + predictions["ds"].astype("string")

    print("Loading records to Mongo")
    records = predictions.to_dict("records")

    updates = self._to_batch_replacements(self, records)

    result = self._mongo_db[symbol + "-forecasts"].bulk_write(updates)
    print("Records loaded")

    return result
