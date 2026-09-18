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
# Lesson 2: Troubleshooting Broken Pods

Welcome back. Lesson 1 was “how to talk to the kitchen.”  
This lesson is “what to do when lunch boxes will not start.”

Three statuses scare people the most:

- **Pending** — the lunch box never even sat down at a table
- **ImagePullBackOff** — Kubernetes cannot download the food package
- **CrashLoopBackOff** — the lunch box starts, dies, starts, dies, over and over

Rule #1: **the status is a clue, not the answer.**  
Your job is to find the *reason under* the status.

---

## The Detective Kit (use this every time)

Do these in order. Do not skip.

```bash
kubectl get pods -A
kubectl describe pod POD_NAME -n NAMESPACE
kubectl logs POD_NAME -n NAMESPACE
kubectl logs POD_NAME -n NAMESPACE --previous
kubectl get events -n NAMESPACE --sort-by=.lastTimestamp
```

What each one is good for:

| Command | What it tells you |
|---|---|
| `get pods` | Which status? How many restarts? |
| `describe pod` | Events + last exit reason. Best first deep look. |
| `logs` | What the app printed *this* run |
| `logs --previous` | What the app printed *the run that crashed* |
| `get events` | Cluster timeline around the failure |

**Tutor tip:** For Pending and ImagePullBackOff, `describe` Events usually wins.  
For CrashLoopBackOff, `logs --previous` usually wins.

---

## Case 1: Pending

### Plain-English meaning
The pod is waiting in line. Kubernetes has **not** picked a computer (node) for it yet.  
The app has not started. Logs will often be empty. That is normal.

### First look
```bash
kubectl get pod shop-abc123 -n web
kubectl describe pod shop-abc123 -n web
```

Scroll to **Events**. Look for `FailedScheduling`.

### Common Event messages and what they mean

**1. Not enough CPU or memory**
```
0/3 nodes are available: 3 Insufficient cpu
0/3 nodes are available: 3 Insufficient memory
```

The pod *asked* for more CPU/RAM than any node has free.

Check nodes:
```bash
kubectl get nodes
kubectl describe node NODE_NAME
kubectl top nodes
```

In `describe node`, look at **Allocated resources**.

Fixes students can choose from:
- Lower the pod’s `resources.requests` if they are too greedy
- Free space by deleting unused pods
- Add more nodes (teacher / cloud team)

**Important:** Kubernetes schedules using **requests**, not “how much the app might use later.”

**2. Taints (the “keep out” sign)**
```
0/3 nodes are available: 3 node(s) had untolerated taint
```

A node can say “only special pods sit here.” If your pod has no matching **toleration**, it stays Pending.

Check taints:
```bash
kubectl describe nodes | grep Taints
```

Fixes:
- Add a toleration to the pod, **or**
- Use a different node, **or**
- A teacher removes the taint (do not do this on a shared cluster without permission)

**3. Wrong node label / nodeSelector**
```
0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector
```

The recipe said “only sit at tables labeled `disk=ssd`,” but no table has that label.

```bash
kubectl get nodes --show-labels
```

**4. Storage is not ready (PVC)**
```
pod has unbound immediate PersistentVolumeClaims
```

The pod wants a saved backpack (volume), but that backpack does not exist yet.

```bash
kubectl get pvc -n web
kubectl describe pvc CLAIM_NAME -n web
```

If the PVC is also `Pending`, fix storage first. The pod will wait forever otherwise.

**5. Namespace quota is full**
```
exceeded quota
```

The kitchen has a class limit: “this namespace may only use 2 CPU.” Your pod would break the rule.

```bash
kubectl describe resourcequota -n web
```

### Pending cheat card
Pending = scheduler problem.  
Do **not** start with logs. Start with `describe` Events.

---

## Case 2: ImagePullBackOff (and ErrImagePull)

### Plain-English meaning
Kubernetes found a node, then tried to download the container image, and failed.  
It waits longer each time (**BackOff** = “I’ll try again later, slower”).

`ErrImagePull` is the failed pull.  
`ImagePullBackOff` is Kubernetes pausing before the next try.

### First look
```bash
kubectl describe pod shop-abc123 -n web
```

Events often say:
- `Failed to pull image`
- `manifest unknown`
- `unauthorized` / `authentication required`
- `not found`

### Common causes

**1. Typo in the image name or tag**
People write:
- `ngnix` instead of `nginx`
- `myapp:v2` when only `myapp:v1` exists
- `latest` when that tag was never pushed

**2. Private registry, missing password**
Docker Hub private images, GitHub packages, AWS/GCP/Azure registries need a **pull secret**.

The pod must reference it:
```yaml
imagePullSecrets:
  - name: regcred
```

**3. The cluster cannot reach the registry**
School firewall, no internet on nodes, or wrong registry URL.

**4. Rate limits**
Public Docker Hub sometimes says “too many downloads.” That can look like a pull failure.

### Useful checks
```bash
kubectl get pod shop-abc123 -n web -o yaml | grep image:
kubectl get secrets -n web
```

If you can test from your laptop:
```bash
docker pull IMAGE_NAME:TAG
```

If your laptop also fails, the image name/tag is probably wrong.  
If your laptop works but the cluster fails, it is often **auth or network**.

### ImagePullBackOff cheat card
The container never started, so app logs are usually empty.  
Fix the image name, tag, or pull secret.

---

## Case 3: CrashLoopBackOff

### Plain-English meaning
The image **did** download. The container **did** start. Then the process inside **quit**.  
Kubernetes restarts it. It fails again. Kubernetes waits longer between tries.

This is an **app or config** problem more often than a cluster problem.

### First look
```bash
kubectl get pod shop-abc123 -n web
kubectl describe pod shop-abc123 -n web
kubectl logs shop-abc123 -n web --previous
```

Why `--previous`?  
The current container may have just restarted and printed nothing yet.  
The *last dead container* usually has the real error.

If the pod has more than one container:
```bash
kubectl logs shop-abc123 -n web -c CONTAINER_NAME --previous
```

### What to read in `describe`

Find **Last State**:

```
State:          Waiting
  Reason:       CrashLoopBackOff
Last State:     Terminated
  Reason:       Error
  Exit Code:    1
Restart Count:  8
```

### Exit codes students should know

| Exit code | Usual meaning | Where to look |
|---|---|---|
| 1 | App error (bad config, missing file, crash) | logs |
| 126 | Command cannot run (permissions) | command / image |
| 127 | Command not found | command spelling |
| 137 | OOMKilled (out of memory, SIGKILL) | memory limit |
| 139 | Segfault (app / library bug) | app or base image |
| 143 | SIGTERM (asked to stop) | often a shutdown, not always a bug |
| 0 | Process finished “successfully” and left | app exited; pods for servers should stay running |

### Common CrashLoop causes

**1. The app is broken or missing settings**
Bad database URL, missing env var, wrong password, file not found.

Logs might say:
- `Cannot connect to database`
- `KEY not set`
- `No such file or directory`

Check ConfigMaps and Secrets exist:
```bash
kubectl get configmap -n web
kubectl get secret -n web
```

**2. OOMKilled (memory limit too small)**
`Last State` reason: `OOMKilled`, exit code **137**.

The app used more RAM than `resources.limits.memory`.  
Fix the app’s leak **or** raise the memory limit (with a teacher’s okay).

**3. Liveness probe is too strict**
Kubernetes thinks the app is dead and kills it, even if the app is just slow to start.

In `describe` Events you may see:
- `Liveness probe failed`
- `Killing container`

Fixes:
- Give the app more `initialDelaySeconds`
- Fix the health URL
- Do not use a probe that fails during startup

**4. The container command finishes**
A server should keep running. If the command is `echo hello`, it prints and exits 0. Kubernetes restarts it. Loop.

**5. Init container failed**
Sometimes the *main* app never starts because a helper container failed first.

```bash
kubectl logs shop-abc123 -n web -c INIT_CONTAINER_NAME
```

### CrashLoop cheat card
Image pulled. Process dies.  
`describe` for exit code.  
`logs --previous` for the story.

---

## Do Not Mix These Up

| Status | Did a node get chosen? | Did the image download? | Did the app start? | Best first command after `get` |
|---|---|---|---|---|
| Pending | No | No | No | `describe` Events |
| ImagePullBackOff | Yes | No | No | `describe` Events |
| CrashLoopBackOff | Yes | Yes | Yes, then died | `describe` + `logs --previous` |

Also nearby, not the same:
- **CreateContainerConfigError** — missing Secret/ConfigMap key before start
- **OOMKilled** — often seen *inside* a CrashLoop
- **Evicted** — node ran out of disk/memory and kicked the pod off

---

## A 5-Minute Classroom Flow

1. `kubectl get pods -n web`  
   Read STATUS and RESTARTS.
2. If Pending or ImagePullBackOff → `describe`, read Events, stop guessing.
3. If CrashLoopBackOff → `describe` for Last State / exit code, then `logs --previous`.
4. Fix the **cause**, not the status.  
   Deleting the pod over and over does not fix a typo in the image name.
5. After a fix: `kubectl get pods -w` and watch it become `Running`.

---

# Harder Quiz (Lesson 2)

Try these before the answer key. Some have more than one good part.

**1.** A pod shows `Pending` and RESTARTS is 0. A student runs `kubectl logs`. Why is that usually a weak first move?

**2.** Events say:  
`0/4 nodes are available: 2 Insufficient memory, 2 node(s) had untolerated taint {dedicated=gpu:NoSchedule}.`  
Explain *both* numbers. Why is the pod still Pending?

**3.** Which resource number does the scheduler care about when it decides if a node has “enough”: `requests` or `limits`? Why does that matter?

**4.** Status is `ImagePullBackOff`. `kubectl logs` is empty. Is the app crashing? What should you read instead?

**5.** You can `docker pull myorg/shop:2.1` on your laptop, but the cluster pod stays ImagePullBackOff with `unauthorized`. What is the most likely missing piece?

**6.** A pod is CrashLoopBackOff. Current `kubectl logs` is empty, restart count is 12. Which flag should you add, and why?

**7.** `Last State` shows `Reason: OOMKilled` and `Exit Code: 137`.  
Is this an image-name problem, a scheduling problem, or a memory problem? What would you change?

**8.** Events show `Liveness probe failed` then `Killing`. The app log says it needs 40 seconds to start. What setting is probably too impatient?

**9.** PVC `data-pvc` is `Pending`. Pod `db-0` is also `Pending` with “unbound PersistentVolumeClaim.” Which do you fix first, and why?

**10.** Match the clue to the status:

- A) `manifest unknown`  
- B) `FailedScheduling` + `Insufficient cpu`  
- C) `Last State: Terminated` + `Exit Code: 1` + app stack trace  

**11.** A container command is `python migrate.py` (runs once and exits 0). The pod keeps restarting. Why can that become CrashLoopBackOff even though the script “worked”?

**12.** True or false: `helm uninstall` then `helm install` is the fastest correct fix for ImagePullBackOff caused by `ngnix:latest`. Explain.

---

### Answer Key

1. Pending means the pod was not scheduled (or not started) yet. There is usually no running container to log. `describe` Events is the right first deep look.

2. Out of 4 nodes, 2 fail because they do not have enough free memory for this pod’s *request*. The other 2 fail because they have a GPU taint and this pod has no matching toleration. Every node is blocked for one reason or the other, so the scheduler has nowhere to put the pod.

3. **Requests.** The scheduler reserves request amounts. A pod can stay Pending because requests are huge, even if the app would only use a little RAM at runtime. Limits matter later (for killing / throttling), not for “can this pod sit here?”

4. No, the app probably never started. Read `kubectl describe pod` Events for the pull error (bad name, missing tag, auth).

5. A registry **pull secret** (and `imagePullSecrets` on the pod/service account). Your laptop is already logged in; the cluster nodes are not.

6. `--previous`. You need logs from the container instance that already crashed. The new one may not have printed yet.

7. Memory problem (hit the container memory limit). Not image pull, not Pending/scheduling. Raise `resources.limits.memory` and/or fix a memory leak. Check that requests still fit on a node after you change values.

8. The **liveness probe** (often `initialDelaySeconds` is too small, or the probe path is wrong). Kubernetes is killing a slow starter.

9. Fix the **PVC / storage** first. The pod is only waiting on the volume. Restarting the pod will not bind a broken claim.

10. A = ImagePullBackOff (or ErrImagePull). B = Pending. C = CrashLoopBackOff.

11. A Deployment/Pod expects the main process to keep running. Exit code 0 still means “process gone.” Kubernetes starts it again. That loop is CrashLoopBackOff. One-shot work belongs in a Job, or the container needs a long-running server command.

12. False. Reinstalling the same typo just fails again. Fix the image name to `nginx:latest` (or the real tag) in the chart/values, then `helm upgrade` / `kubectl apply`. The status is a symptom; the typo is the bug.

---

**Score yourself**
- 10–12: you can tutor a classmate
- 7–9: solid; restudy Events vs logs
- 6 or below: redo the three cheat cards, then retry 2, 6, 10, and 12

