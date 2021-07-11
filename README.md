# Quick start

```sh
## Uncomment to use minikube
# minikube --memory max --cpus max start

# Create Mongo namespace
kubectl create namespace mark8

# Create Mongo username and password as k8 secret
kubectl create secret generic --namespace mark8 mongo \
  --from-literal=RootUser="<password>" \
  --from-literal=RootPassword="<password>"

# Create Quandl API key as k8 secret
kubectl create secret generic --namespace mark8 quandl \
  --from-literal=APIKey="<quandl-api-token>"

# Create Mongo persistent volume
kubectl -n mark8 apply -f ./application/mongo/mongo-pv.yaml

# Create Mongo deployment
kubectl -n mark8 apply -f ./application/mongo/mongo-deployment.yaml

# Check deployment status
kubectl -n mark8 describe deployment mongo

# Create Redis service
kubectl -n mark8 apply -f ./application/redis/redis-service.yaml

# Create Redis pod
kubectl -n mark8 apply -f ./application/redis/redis-pod.yaml

# Check pod status
kubectl -n mark8 describe pod redis

# Build & push ingest-eod image
docker build -t gregckrause/ingest-eod . -f Dockerfile.ingest.eod
docker push gregckrause/ingest-eod:latest

# Run ingest job
kubectl -n mark8 apply -f ./application/market/ingest-eod.yaml
```
