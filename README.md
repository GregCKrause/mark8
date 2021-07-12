# Quick start

```sh
## Can also set --memory max --cpus max
minikube start

# Create Mongo namespace
kubectl create namespace mark8

# Create Mongo username and password as k8 secret
kubectl create secret generic --namespace mark8 mongo \
  --from-literal=RootUser="<password>" \
  --from-literal=RootPassword="<password>"

# Create Quandl API key as k8 secret
kubectl create secret generic --namespace mark8 quandl \
  --from-literal=APIKey="<quandl-api-token>"

# Ensure mongo is running locally
mongotop

# Create Redis service
kubectl -n mark8 apply -f ./application/redis/redis-service.yaml

# Create Redis pod
kubectl -n mark8 apply -f ./application/redis/redis-pod.yaml

# Check pod status
kubectl -n mark8 describe pod redis

# Build & push queue-eod image
cd ./application/market
docker build -t gregckrause/queue-eod . -f Dockerfile.queue.eod
docker push gregckrause/queue-eod:latest
cd -

# Run queue-ingest-eod job
kubectl -n mark8 apply -f ./application/market/queue-ingest-eod.yaml

# Build & push ingest-eod image
cd ./application/market
docker build -t gregckrause/ingest-eod . -f Dockerfile.ingest.eod
docker push gregckrause/ingest-eod:latest
cd -

# Run ingest job
kubectl -n mark8 apply -f ./application/market/ingest-eod.yaml

# Build & push forecast-eod image
cd ./application/market
docker build -t gregckrause/forecast-eod . -f Dockerfile.forecast.eod
docker push gregckrause/forecast-eod:latest
cd -

# Run queue-forecast-eod job
kubectl -n mark8 apply -f ./application/market/queue-forecast-eod.yaml

# Run forecast job
kubectl -n mark8 apply -f ./application/market/forecast-eod.yaml
```
