# Quick start

```sh
# Uncomment to use minikube
# minikube --memory max --cpus max start
```

## MySQL
[mysql-pv.yaml](./application/mysql/mysql-pv.yaml)
[mysql-deployment.yaml](./application/mysql/mysql-deployment.yaml)

```sh
# Create MySQL namespace
kubectl create namespace mysql

# Create MySQL root password as k8 secret
kubectl create secret generic --namespace mysql mysql \
  --from-literal=RootPassword="<password>"

# Create MySQL persistent volume
kubectl apply -n mysql -f ./application/mysql/mysql-pv.yaml

# Create MySQL deployment
kubectl apply -n mysql -f ./application/mysql/mysql-deployment.yaml

# Check deployment status
kubectl describe -n mysql deployment mysql

## Uncomment to port-forward host port 3307 to k8 3306
# kubectl port-forward -n mysql deployment/mysql 3307:3306
```
