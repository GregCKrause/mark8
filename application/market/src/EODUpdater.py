# Standard library
import argparse
from datetime import datetime as dt
import os

# Third party
from pymongo import MongoClient, UpdateOne
import quandl

class EODUpdater(object):
  def __init__(self, mongo_username, mongo_password, quandl_api_key):
    self._mongo_db = MongoClient(
      'mongodb://mongo:27017',
      username=mongo_username,
      password=mongo_password
    )['eod']
    self._quandl_api_key = quandl_api_key
    quandl.ApiConfig.api_key = self._quandl_api_key

  def update_symbol(self, symbol):
    """Upserts mongo db[symbol] collection"""
    print("Requesting Quandl EOD set for symbol", symbol)
    eod = quandl.get('EOD/' + symbol)
    print(eod.count().max(), "records obtained")

    eod["_id"] = eod.index.strftime("%Y-%m-%d")
    eod["last_updated"] = dt.strftime(dt.now(), "%Y-%m-%d")

    print("Loading records to Mongo")
    records = eod.to_dict("records")

    updates = [
      UpdateOne(
        {'_id': record["_id"]},
        {"$set": record},
        upsert=True
      ) for record in records
    ]

    result = self._mongo_db[symbol].bulk_write(updates)
    print("Records loaded")

    return result
