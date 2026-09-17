# Kubernetes Class: kubectl + Helm (Middle School Edition)

Think of **Kubernetes (K8s)** as a giant school kitchen that runs lots of apps at once.

- A **pod** is one lunch box (one running app).
- A **deployment** is the recipe that says, “Always keep 3 of these lunch boxes ready.”
- A **service** is the window where people pick up the food.
- A **namespace** is a separate kitchen (like “6th grade kitchen” vs “8th grade kitchen”).

**kubectl** is the walkie-talkie you use to talk to the kitchen.

**Helm** is a cookbook. Instead of writing every recipe yourself, you install a whole meal with one command.

---

## Part 1: Common kubectl Commands

### 1. Check that your tools work
**What it does:** Shows the kubectl version (and often the cluster version).

```bash
kubectl version
```

---

### 2. See the cluster
**What it does:** Tells you if Kubernetes is awake and where the control room is.

```bash
kubectl cluster-info
```

**See the computers (nodes) doing the work:**

```bash
kubectl get nodes
```

---

### 3. List stuff (`get` is your best friend)
**What it does:** Shows a simple table of things that exist.

```bash
kubectl get pods
kubectl get deployments
kubectl get services
kubectl get namespaces
```

**Helpful extras:**

```bash
kubectl get pods -A              # all kitchens (all namespaces)
kubectl get pods -o wide         # extra details, like which computer the pod is on
kubectl get pods -n my-app       # only look in one kitchen
```

Short names you will see a lot:
- `po` = pods
- `deploy` = deployments
- `svc` = services
- `ns` = namespaces

Example: `kubectl get po -A`

---

### 4. Get the full story (`describe`)
**What it does:** Opens the “report card” for one thing. Super useful when something is broken.

```bash
kubectl describe pod my-pod
kubectl describe deployment my-app
kubectl describe node worker-1
```

Look here for events at the bottom. Events often say *why* a pod is stuck.

---

### 5. Create or update from a file (`apply`)
**What it does:** Reads a YAML file and makes the cluster match it.  
If the thing is new, it creates it. If it already exists, it updates it.

```bash
kubectl apply -f app.yaml
```

This is the command most teams use every day.

`create` is similar, but it usually fails if the thing already exists. Prefer `apply`.

---

### 6. Delete things
**What it does:** Removes a resource.

```bash
kubectl delete pod my-pod
kubectl delete deployment my-app
kubectl delete -f app.yaml
```

Be careful: deleting a namespace can delete *everything* inside it.

---

### 7. Read the app’s diary (`logs`)
**What it does:** Prints what the app printed inside the container.

```bash
kubectl logs my-pod
kubectl logs -f my-pod
```

`-f` means “follow,” like watching a live chat.

If a pod has more than one container:

```bash
kubectl logs my-pod -c my-container
```

---

### 8. Climb inside a pod (`exec`)
**What it does:** Runs a command *inside* the running lunch box.

```bash
kubectl exec -it my-pod -- bash
```

If bash is not there, try:

```bash
kubectl exec -it my-pod -- sh
```

Good for checking files or testing a connection.

---

### 9. Make more copies (`scale`)
**What it does:** Changes how many copies of an app are running.

```bash
kubectl scale deployment my-app --replicas=3
```

Now Kubernetes tries to keep 3 pods ready.

---

### 10. Watch an update (`rollout`)
**What it does:** Manages rolling updates (new version in, old version out).

```bash
kubectl rollout status deployment/my-app
kubectl rollout history deployment/my-app
kubectl rollout undo deployment/my-app
```

`undo` is the “oops, go back” button.

---

### 11. Make a secret tunnel (`port-forward`)
**What it does:** Lets your laptop talk to a pod or service as if it were local.

```bash
kubectl port-forward pod/my-pod 8080:80
```

Now open `http://localhost:8080` on your computer.

---

### 12. Switch kitchens / clusters
**What it does:** Changes which cluster or namespace you are talking to.

```bash
kubectl config get-contexts
kubectl config use-context my-cluster
kubectl config set-context --current --namespace=dev
```

---

## Part 2: Common Helm Commands

Helm talks in three words:

- **Chart** = the cookbook recipe
- **Release** = one cooked meal made from that recipe
- **Repo** = a library of cookbooks on the internet

### 1. Check Helm
```bash
helm version
```

---

### 2. Add a cookbook library (`repo`)
**What it does:** Tells Helm where to find charts.

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm repo list
helm search repo nginx
```

`update` refreshes the list of available recipes.

---

### 3. Install an app
**What it does:** Cooks the recipe and puts it in the cluster.

```bash
helm install my-web bitnami/nginx
```

Install in a specific kitchen, and create that kitchen if needed:

```bash
helm install my-web bitnami/nginx -n web --create-namespace
```

Use your own settings:

```bash
helm install my-web bitnami/nginx -f values.yaml
helm install my-web bitnami/nginx --set replicaCount=3
```

Practice first without changing the cluster:

```bash
helm install my-web bitnami/nginx --dry-run --debug
```

---

### 4. See what is installed
```bash
helm list
helm list -A
helm status my-web
```

---

### 5. Upgrade (new version or new settings)
```bash
helm upgrade my-web bitnami/nginx -f values.yaml
```

Install *or* upgrade in one command (very common):

```bash
helm upgrade --install my-web bitnami/nginx -f values.yaml
```

---

### 6. Undo a bad update (`rollback`)
```bash
helm history my-web
helm rollback my-web 1
```

`1` is the old revision number from history.

---

### 7. Remove the app
```bash
helm uninstall my-web
```

That removes the release Helm created.

---

### 8. Make or check your own chart
```bash
helm create my-chart
helm lint my-chart
helm template my-web ./my-chart
```

- `create` builds a starter recipe folder
- `lint` checks for mistakes
- `template` shows the YAML Helm *would* send to Kubernetes, without installing it

---

### 9. Peek at settings
```bash
helm show values bitnami/nginx
helm get values my-web
```

`show values` = default recipe settings  
`get values` = the settings *your installed release* is using

---

## Easy Memory Trick

| You want to… | Use |
|---|---|
| Look at stuff | `kubectl get` / `helm list` |
| Learn why something is weird | `kubectl describe` / `helm status` |
| Put something in the cluster | `kubectl apply` / `helm install` |
| Change it | `kubectl apply` or `kubectl scale` / `helm upgrade` |
| Read app output | `kubectl logs` |
| Go inside a container | `kubectl exec` |
| Undo | `kubectl rollout undo` / `helm rollback` |
| Take it out | `kubectl delete` / `helm uninstall` |

Helm does **not** replace kubectl. Helm packages apps. kubectl still inspects pods, logs, and problems.

---

## Tutor Tips for Students

1. Always start with `kubectl get pods` or `kubectl get pods -A`.
2. If a pod is not `Running`, use `kubectl describe pod NAME` first, then `kubectl logs NAME`.
3. Practice in a practice cluster (minikube, kind, or a school lab). Do not delete things in a real shared cluster unless a teacher says so.
4. Namespaces matter. If you “can’t find” a pod, you may be in the wrong kitchen. Try `-A` or `-n`.
5. `apply` is safer for daily work than guessing `create` vs update.

---

# Quiz Time

Try these without looking first. Answers are below.

**1.** What command lists pods in every namespace?

**2.** A pod is stuck. Which command gives the most “why” details?

**3.** What is the difference between `kubectl create -f file.yaml` and `kubectl apply -f file.yaml`?

**4.** You want to watch logs live as they appear. Which flag do you add to `kubectl logs`?

**5.** Write a command that scales deployment `shop` to 4 copies.

**6.** In Helm, what is a **chart** vs a **release**?

**7.** Write a command that installs chart `bitnami/nginx` with release name `store`.

**8.** An upgrade went badly. Which Helm command goes back to an older revision?

**9.** Why would you run `helm template` before `helm install`?

**10.** True or false: After `helm install`, you never need kubectl again.

---

### Answer Key

1. `kubectl get pods -A` (or `--all-namespaces`)
2. `kubectl describe pod POD_NAME`
3. `create` usually fails if the thing already exists. `apply` creates it if missing and updates it if it already exists.
4. `-f` (follow)
5. `kubectl scale deployment shop --replicas=4`
6. A **chart** is the recipe. A **release** is one installed copy of that recipe in the cluster.
7. `helm install store bitnami/nginx`
8. `helm rollback store REVISION` (after checking `helm history store`)
9. It shows the YAML Helm would create, so you can catch mistakes without changing the cluster.
10. False. Helm installs the app. You still use kubectl to look at pods, logs, events, and bugs.

---
