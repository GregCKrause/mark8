# Standard library
import os

# Local
from EOD import EOD

MONGO_USERNAME=os.getenv("MONGO_INITDB_ROOT_USERNAME")
MONGO_PASSWORD=os.getenv("MONGO_INITDB_ROOT_PASSWORD")
QUANDL_API_KEY=os.getenv("QUANDL_API_KEY")

if __name__=="__main__":
  updater = EOD(QUANDL_API_KEY, MONGO_USERNAME, MONGO_PASSWORD)

  print("Running forecast-eod.py")
  try:
    updater.update_symbol_tf_forecasts()
    updater.update_symbol_gluonts_forecasts()
  except Exception as e:
    print("Exception thrown during update forecasts", e)
