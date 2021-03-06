# Quick start

```sh
## (Optional) Start minikube cluster
minikube start --memory max --cpus max

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

# Create queue-ingest-eod cronjob
kubectl -n mark8 apply -f ./application/market/queue-ingest-eod.yaml

# (Optional) Verify redis queue was populated
kubectl -n mark8 run -i --tty temp --image redis --command "/bin/sh"
## From shell
redis-cli -h redis
## In redis-cli
lrange ingesteod 0 -1
## After exiting
kubectl -n mark8 delete pod temp

# Build & push ingest-eod image
cd ./application/market
docker build -t gregckrause/ingest-eod . -f Dockerfile.ingest.eod
docker push gregckrause/ingest-eod:latest
cd -

# Create ingest cronjob
kubectl -n mark8 apply -f ./application/market/ingest-eod.yaml

# Build & push forecast-eod image
cd ./application/market
docker build -t gregckrause/forecast-eod . -f Dockerfile.forecast.eod
docker push gregckrause/forecast-eod:latest
cd -

# Create forecast cronjob
kubectl -n mark8 apply -f ./application/market/forecast-eod.yaml
```
