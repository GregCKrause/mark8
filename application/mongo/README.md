# Mongo quick start
```sh
# Create Mongo persistent volume
kubectl apply -n <namespace> -f ./mongo-pv.yaml

# Create Mongo deployment
kubectl apply -n <namespace> -f ./mongo-deployment.yaml

# Check deployment status
kubectl describe -n <namespace> deployment mongo
```

# Debug
```sh
# Port-forward host's port 27018 to k8's port 27017
kubectl port-forward -n mongo deployment/mongo 27018:27017
```