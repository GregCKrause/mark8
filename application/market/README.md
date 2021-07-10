# Running locally

```sh
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Forward MySQL
kubectl port-forward -n mysql deployment/mysql 3307:3306

# Requires <brew install jq>
export MYSQL_ROOT_PASSWORD=$(kubectl get secrets --namespace mysql mysql -o json | jq -r ".data.RootPassword" | base64 --decode)

python eod-ingest.py
```
