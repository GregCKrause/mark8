# Running locally

```sh
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Forward Mongo
kubectl port-forward -n mark8 deployment/mongo 27017:27017

# Requires <brew install jq>
export MONGO_INITDB_ROOT_USERNAME=$(kubectl get secrets --namespace mark8 mongo -o json | jq -r ".data.RootUser" | base64 --decode)
export MONGO_INITDB_ROOT_PASSWORD=$(kubectl get secrets --namespace mark8 mongo -o json | jq -r ".data.RootPassword" | base64 --decode)
export QUANDL_API_KEY=$(kubectl get secrets --namespace mark8 quandl -o json | jq -r ".data.APIKey" | base64 --decode)

python -i src/eod-ingest.py --symbol GOOG
```
