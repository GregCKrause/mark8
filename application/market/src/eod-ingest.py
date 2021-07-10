# Standard library
import argparse
from datetime import datetime as dt
import json
import os

# Third party
from pymongo import MongoClient
import quandl

username=os.getenv("MONGO_INITDB_ROOT_USERNAME")
password=os.getenv("MONGO_INITDB_ROOT_PASSWORD")
quandl_api_key=os.getenv("QUANDL_API_KEY")

if __name__=="__main__":

  parser = argparse.ArgumentParser(description='Ingests Quandl EOD data to MongoDB')
  parser.add_argument('--symbol', help='Stock symbol/ticker for which to ingest EOD data')
  args = parser.parse_args()
  symbol = args.symbol.upper()

  quandl.ApiConfig.api_key = quandl_api_key

  client = MongoClient(
    'mongodb://127.0.0.1:27018',
    username=username,
    password=password
  )

  db = client['eod']

  print("Requesting Quandl EOD set for symbol", symbol)
  eod = quandl.get('EOD/' + symbol)
  print(eod.count().max(), "records obtained")

  eod["_id"] = eod.index.strftime("%Y-%m-%d")
  eod["last_updated"] = dt.strftime(dt.now(), "%Y-%m-%d")

  print("Loading records to Mongo")
  records = json.loads(eod.T.to_json()).values()
  db[symbol].insert_many(records)
  print("Records loaded.", symbol)
