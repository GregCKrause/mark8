# Standard library
import os

# Third party
import redis

# Local
from EOD import EOD
from symbols import symbols as default_symbols

# One of ["ingesteod", "forecasteod"]
QUEUE=os.getenv("QUEUE")
MONGO_USERNAME=os.getenv("MONGO_INITDB_ROOT_USERNAME")
MONGO_PASSWORD=os.getenv("MONGO_INITDB_ROOT_PASSWORD")
QUANDL_API_KEY=os.getenv("QUANDL_API_KEY")

updater = EOD(MONGO_USERNAME, MONGO_PASSWORD, QUANDL_API_KEY)
r = redis.StrictRedis(host="redis")

symbols = updater.get_symbols()

if len(symbols) == 0:
    updater.set_symbols(default_symbols)
    symbols = updater.get_symbols()

for symbol in symbols:
    r.rpush(QUEUE, symbol["_id"])
