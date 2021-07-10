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
kubectl apply -n mark8 -f ./application/mongo/mongo-pv.yaml

# Create Mongo deployment
kubectl apply -n mark8 -f ./application/mongo/mongo-deployment.yaml

# Check deployment status
kubectl describe -n mark8 deployment mongo
```
