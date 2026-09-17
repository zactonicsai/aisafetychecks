# Docker + Kubernetes + Python Hello World

A small local Kubernetes learning project with:

- Docker containers
- a local **kind** Kubernetes cluster
- `kubectl` for cluster inspection and an alternate raw-manifest deployment
- Helm for the main deployment
- Python/Flask web service
- Python/Flask REST API


## Student tutorial

A detailed beginner tutorial using school and grocery-store examples is available here:

```text
docs/KUBERNETES-FOR-MIDDLE-SCHOOL-STUDENTS.md
```

It explains Docker images, Pods, Deployments, Services, `kubectl`, Helm, health probes, resource controls, Secrets, NetworkPolicies, manual scaling, HPA, troubleshooting, and each project script step by step.

## Architecture

```text
Docker Desktop / Docker Engine
        |
        v
kind Kubernetes cluster
  +-------------------------------+
  | namespace: python-demo        |
  |                               |
  | python-web Deployment         |
  |   -> Service python-web :80   |
  |                               |
  | python-api Deployment         |
  |   -> Service python-api :80   |
  +-------------------------------+
        |                 |
 kubectl port-forward  kubectl port-forward
 localhost:8080        localhost:8081
```

## Prerequisites

Install and start Docker, then install:

- `kind`
- `kubectl`
- `helm`
- `curl`

On macOS with Homebrew:

```bash
brew install kind kubectl helm
```

Docker Desktop can provide the Docker engine.

## Fastest start

```bash
chmod +x scripts/*.sh
./scripts/run-all.sh
```

The script performs these steps:

1. Checks Docker, kind, kubectl, Helm, and curl.
2. Creates a two-node kind cluster named `python-demo`.
3. Builds the Python Docker images.
4. Loads the local images into kind.
5. Uses Helm to install the applications.
6. Uses kubectl port-forward and curl to run health/API tests.

## Step-by-step

### 1. Check tools

```bash
./scripts/00-check-prereqs.sh
```

### 2. Create the cluster

```bash
./scripts/01-create-cluster.sh
```

Useful checks:

```bash
kubectl config current-context
kubectl get nodes
kubectl cluster-info
```

### 3. Build Docker images

```bash
./scripts/02-build-images.sh
```

This creates:

```text
python-demo-web:1.0.0
python-demo-api:1.0.0
```

### 4. Load images into kind

A kind cluster runs its Kubernetes nodes inside Docker containers. Loading the images puts your locally built application images where those nodes can use them.

```bash
./scripts/03-load-images.sh
```

### 5A. Deploy with Helm — recommended path

```bash
./scripts/04-deploy-helm.sh
```

Equivalent Helm command:

```bash
helm upgrade --install python-demo ./helm/python-demo \
  --namespace python-demo \
  --create-namespace \
  --wait
```

Inspect it:

```bash
helm list -n python-demo
helm status python-demo -n python-demo
kubectl get all -n python-demo
```

### 5B. Alternate deployment with raw kubectl YAML

Do not use this at the same time as the Helm release unless you first remove the Helm release, because both methods manage objects with the same names.

```bash
helm uninstall python-demo -n python-demo
./scripts/04-deploy-kubectl.sh
```

Raw commands:

```bash
kubectl create namespace python-demo --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f k8s/web.yaml
kubectl apply -f k8s/api.yaml
```

### 6. Test automatically

```bash
./scripts/05-test.sh
```

Expected API GET response is similar to:

```json
{"message":"Hello, Kubernetes!","pod":"python-api-..."}
```

### 7. Open the web service

Terminal 1:

```bash
kubectl -n python-demo port-forward svc/python-web 8080:80
```

Browser:

```text
http://localhost:8080
```

Terminal 2:

```bash
kubectl -n python-demo port-forward svc/python-api 8081:80
```

Test GET:

```bash
curl 'http://localhost:8081/api/hello?name=Zach'
```

Test POST:

```bash
curl -X POST http://localhost:8081/api/hello \
  -H 'Content-Type: application/json' \
  -d '{"name":"Kubernetes"}'
```

## kubectl troubleshooting cheat sheet

```bash
kubectl get nodes -o wide
kubectl get namespaces
kubectl get pods -n python-demo -o wide
kubectl get services -n python-demo
kubectl describe pod -n python-demo <pod-name>
kubectl logs -n python-demo deployment/python-web
kubectl logs -n python-demo deployment/python-api
kubectl get events -n python-demo --sort-by=.metadata.creationTimestamp
```

If a pod shows `ImagePullBackOff`, confirm the images were loaded:

```bash
./scripts/03-load-images.sh
kubectl rollout restart deployment/python-web -n python-demo
kubectl rollout restart deployment/python-api -n python-demo
```

## Change the Python code

After editing an app, rebuild and reload the images:

```bash
./scripts/02-build-images.sh
./scripts/03-load-images.sh
kubectl rollout restart deployment/python-web -n python-demo
kubectl rollout restart deployment/python-api -n python-demo
kubectl rollout status deployment/python-web -n python-demo
kubectl rollout status deployment/python-api -n python-demo
```

For real development, use unique image tags instead of repeatedly replacing `1.0.0`.

## Helm changes

Preview generated YAML:

```bash
helm template python-demo ./helm/python-demo
```

Validate chart structure:

```bash
helm lint ./helm/python-demo
```

Upgrade after changing the chart:

```bash
helm upgrade python-demo ./helm/python-demo -n python-demo --wait
```

Rollback:

```bash
helm history python-demo -n python-demo
helm rollback python-demo 1 -n python-demo
```

## Remove only the applications

For Helm deployment:

```bash
helm uninstall python-demo -n python-demo
kubectl delete namespace python-demo --ignore-not-found
```

For raw kubectl deployment:

```bash
kubectl delete -f k8s/web.yaml --ignore-not-found
kubectl delete -f k8s/api.yaml --ignore-not-found
kubectl delete namespace python-demo --ignore-not-found
```

## Destroy the entire local cluster

```bash
./scripts/99-destroy.sh
```

This removes the kind Kubernetes cluster. It does not remove Docker itself.

## Optional load-balancer lab

The base project starts with internal `ClusterIP` Services so it works without an
extra local cloud provider. To learn Kubernetes `LoadBalancer` Services with kind:

```bash
./scripts/07-install-loadbalancer-helper.sh
```

In a second terminal, run:

```bash
cloud-provider-kind --enable-lb-port-mapping
```

Then:

```bash
./scripts/08-enable-loadbalancer.sh
./scripts/09-test-loadbalancer.sh
```

The lab exposes **python-web** with `type: LoadBalancer` and deliberately keeps
**python-api** as `ClusterIP` so the API remains internal.

Read the student lesson:

```text
docs/LOAD-BALANCER-LESSON.md
```
