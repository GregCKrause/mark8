# Based on https://github.com/kubernetes/website/blob/main/content/en/examples/application/job/redis/worker.py
# Licensed under Creative Commons Attribution 4.0 International

# Standard library
import os

# Local
from EOD import EOD
from RedisQueueWorker import RedisQueueWorker

MONGO_USERNAME=os.getenv("MONGO_INITDB_ROOT_USERNAME")
MONGO_PASSWORD=os.getenv("MONGO_INITDB_ROOT_PASSWORD")
QUANDL_API_KEY=os.getenv("QUANDL_API_KEY")

if __name__=="__main__":

  updater = EOD(MONGO_USERNAME, MONGO_PASSWORD, QUANDL_API_KEY)

  queue = RedisQueueWorker(name="forecasteod")
  print("Worker with sessionID: " +  queue.sessionID())
  print("Initial queue state: empty=" + str(queue.empty()))

  while not queue.empty():
    item = queue.lease(lease_secs=60, block=True, timeout=2) 
    if item is not None:
      symbol = item.decode("utf-8").upper()
      print("Working on " + symbol)
      try:
        updater.forecast_symbol(symbol)
      except Exception as e:
        print("Exception thrown during forecast_symbol", symbol, e)
      queue.complete(item)
    else:
      print("Waiting for work")

  print("Queue empty, exiting")
