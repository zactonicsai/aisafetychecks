# Kubernetes for Middle School Students

## A Hands-On Tutorial Using a School and Grocery Store

This tutorial uses the `docker-kubernetes-python-demo` project to explain Docker, Kubernetes, `kubectl`, Helm, networking, secrets, scaling, health checks, and troubleshooting.

The goal is not to memorize every command. The goal is to understand **what problem each tool solves** and then connect that idea to commands you can actually run.

---

# 1. The Big Idea

Imagine that you run a grocery store.

You have two jobs:

1. A **web page** that tells customers, “Hello from Kubernetes!”
2. An **API** that can answer requests such as “Hello, Zach!”

Now imagine the grocery store gets busy. One copy of the API may not be enough. You might want three copies. If one crashes, you want another one started automatically. If you update the software, you want the update performed safely.

That is the kind of problem Kubernetes helps solve.

A school gives us another useful example. A principal does not personally teach every class. Instead, the principal keeps track of classrooms, teachers, schedules, rules, and resources. Kubernetes works in a similar way: it coordinates many smaller pieces so applications stay in the state you asked for.

## The most important Kubernetes idea: desired state

You usually do not tell Kubernetes:

> Start this exact program once and then forget about it.

Instead, you tell Kubernetes:

> I want one copy of my web app and one copy of my API running all the time.

Kubernetes keeps checking.

If one Pod disappears, Kubernetes can create another one.

If you change the desired number from 1 to 3, Kubernetes creates more Pods.

If you change an image version, Kubernetes can replace old Pods with new Pods.

Think of it like a school principal checking a schedule:

> “Room 101 should have one math teacher. If the teacher is absent, I need a substitute.”

---

# 2. Kubernetes Vocabulary With School and Grocery Store Examples

| Kubernetes word | School example | Grocery store example | What it really means |
|---|---|---|---|
| Cluster | School district | Grocery company | The whole Kubernetes environment |
| Control plane | District office / principal | Store management office | Makes decisions and keeps track of the desired state |
| Node | School building | Store building | A machine that can run workloads |
| Pod | Classroom | Checkout station | The smallest normal unit Kubernetes schedules |
| Container | Teacher working in a classroom | Cashier working at a register | A running application created from an image |
| Image | Teacher lesson package | Boxed meal kit / recipe package | The packaged software used to create a container |
| Deployment | Staffing plan | Checkout staffing plan | Says how many Pods should run and how updates happen |
| Replica | Another copy of a class | Another open checkout lane | One copy of the workload |
| Service | School front desk number | Customer service desk | A stable network name/address that finds changing Pods |
| Namespace | Grade-level wing | Store department | A logical area used to organize resources |
| Label | Class/team sticker | Shelf/category label | A key/value tag used to identify resources |
| Selector | “Find all 7th-grade science rooms” | “Find all frozen-food shelves” | A rule that finds resources by labels |
| Secret | Locked staff password cabinet | Store safe | Stores sensitive configuration such as passwords or tokens |
| NetworkPolicy | Hallway access rules | Employees-only door rules | Controls which network traffic is allowed |
| ConfigMap | School handbook | Store procedure sheet | Non-secret configuration |
| Helm Chart | Binder of school setup forms | Store opening kit | A reusable package of Kubernetes YAML templates |
| Helm Release | One installed copy of the binder | One store opened from the kit | A particular installed Helm application |
| Probe | Teacher attendance/health check | “Is checkout register working?” check | Tells Kubernetes whether an app is alive or ready |
| Resource request | Reserved desks for a class | Reserved counter space | Minimum CPU/memory Kubernetes plans for |
| Resource limit | Maximum room capacity | Maximum shelf space | Maximum CPU/memory the container is allowed to use |

---

# 3. The Project We Are Using

The project has two Python Flask applications:

```text
apps/
├── web/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
└── api/
    ├── app.py
    ├── requirements.txt
    └── Dockerfile
```

The web application listens on port `8080` inside its container.

The API also listens on port `8080` inside its container.

Docker builds these two images:

```text
python-demo-web:1.0.0
python-demo-api:1.0.0
```

The project then creates a local Kubernetes cluster using **kind**.

`kind` means **Kubernetes IN Docker**. It runs Kubernetes nodes as Docker containers on your computer.

The project has this kind configuration:

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
  - role: worker
```

That gives us:

```text
Your Computer
    |
    +-- Docker
          |
          +-- kind control-plane node
          |
          +-- kind worker node
```

The control-plane node is like the school principal's office.

The worker node is like a classroom building where application workloads can run.

---

# 4. What Docker Does Before Kubernetes Starts

Kubernetes does not normally build your Python source code into an application package. Docker does that job in this project.

Look at the web Dockerfile:

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
USER 65532:65532
EXPOSE 8080
CMD ["python", "app.py"]
```

Think of a Dockerfile as a **recipe card**.

The recipe says:

1. Start with a small Python environment.
2. Make `/app` our work area.
3. Copy the package list.
4. Install Python packages.
5. Copy the Python program.
6. Run as a non-root user.
7. Document that the app uses port 8080.
8. Start `python app.py` when the container begins.

## Image versus container

This distinction is very important.

An **image** is the packaged recipe/product.

A **container** is a running copy made from that image.

Grocery-store example:

```text
Frozen pizza box = image
Cooked pizza     = container
```

School example:

```text
Lesson-plan package = image
Actual class session = container
```

You can create many containers from the same image, just as many classrooms can use the same lesson plan.

---

# 5. Why Image Names and Versions Matter

Our images are named:

```text
python-demo-web:1.0.0
python-demo-api:1.0.0
```

The part after the colon is the **tag**.

```text
python-demo-web : 1.0.0
      name          tag
```

A tag helps tell Kubernetes which version to run.

A grocery store would not order a box marked only:

> cereal

if there are many recipes and versions. A product number makes it clearer exactly which product is expected.

For learning, `1.0.0` is easy to understand. In real projects, use unique version tags such as:

```text
python-demo-api:1.0.1
python-demo-api:1.0.2
python-demo-api:2026-09-16-001
```

Production systems often use immutable image digests for even stronger version control.

## `imagePullPolicy: IfNotPresent`

Our Kubernetes files contain:

```yaml
imagePullPolicy: IfNotPresent
```

That means:

> If this image is already available on the node, use it. Do not download another copy unnecessarily.

This is especially useful for our local kind project because we manually load the images into the cluster.

If you rebuild `python-demo-api:1.0.0` but keep the same tag, Kubernetes may still have an older local copy unless you reload it and recreate/restart the Pods. That is why unique tags are a better habit for bigger projects.

---

# 6. Phase 0 — Check the Tools

Run:

```bash
./scripts/00-check-prereqs.sh
```

The script checks for:

```text
docker
kind
kubectl
helm
curl
```

It also checks whether Docker is actually running.

## What each tool does

### Docker

Builds images and runs containers.

Think of Docker as the school kitchen that packages meals into identical lunch boxes.

### kind

Builds a small Kubernetes cluster inside Docker.

Think of kind as building a tiny practice school district on your laptop.

### kubectl

`kubectl` is the main command-line remote control for Kubernetes.

You pronounce it in several common ways, including “cube control.”

Think of `kubectl` as a walkie-talkie connected to the principal's office.

You can ask:

```bash
kubectl get pods
```

which means approximately:

> Kubernetes, show me the Pods you know about.

You can tell it:

```bash
kubectl scale deployment python-api --replicas=3
```

which means:

> Kubernetes, I now want three copies of this API Deployment.

### Helm

Helm packages many Kubernetes YAML files into one reusable application package called a **Chart**.

Think of raw Kubernetes YAML files as individual school forms:

```text
teacher form
classroom form
schedule form
safety form
```

Helm is the binder that organizes the forms and lets you fill in common values once.

### curl

`curl` sends network requests.

We use it like a pretend customer visiting the web/API service.

---

# 7. Phase 1 — Create the Kubernetes Cluster

Run:

```bash
./scripts/01-create-cluster.sh
```

The important command inside the script is:

```bash
kind create cluster \
  --name python-demo \
  --config kind-config.yaml
```

This tells kind:

> Create a Kubernetes cluster named `python-demo` using the instructions in `kind-config.yaml`.

## What is a cluster?

A cluster is the whole Kubernetes system you are managing.

School analogy:

```text
School district
├── administration
├── school building A
└── school building B
```

Kubernetes analogy:

```text
Cluster
├── control plane
├── worker node A
└── worker node B
```

Our practice cluster is smaller:

```text
python-demo cluster
├── 1 control-plane node
└── 1 worker node
```

## Switch kubectl to the correct cluster

The script runs:

```bash
kubectl config use-context kind-python-demo
```

A **context** tells `kubectl` which cluster and credentials to use.

Imagine a school administrator manages three schools. Before using the intercom, they must make sure they selected the correct school.

Check it with:

```bash
kubectl config current-context
```

Expected:

```text
kind-python-demo
```

## Inspect the cluster

Run:

```bash
kubectl cluster-info
```

Then:

```bash
kubectl get nodes
```

For more information:

```bash
kubectl get nodes -o wide
```

`-o wide` means “show extra columns.”

## Understanding the node roles

The **control plane** decides what should happen.

It keeps track of Kubernetes objects and schedules work.

A **worker node** provides compute resources for workloads.

A simplified picture is:

```text
You
 |
 | kubectl command
 v
Kubernetes API / Control Plane
 |
 | scheduling decision
 v
Worker Node
 |
 v
Pod
 |
 v
Container
```

---

# 8. Phase 2 — Build the Docker Images

Run:

```bash
./scripts/02-build-images.sh
```

The script runs commands like:

```bash
docker build -t python-demo-web:1.0.0 apps/web
```

and:

```bash
docker build -t python-demo-api:1.0.0 apps/api
```

Break the first command apart:

```text
docker build
```

means:

> Build an image from a Dockerfile.

```text
-t python-demo-web:1.0.0
```

means:

> Give the image this name and tag.

```text
apps/web
```

means:

> Use this directory as the build context.

## See the images

Run:

```bash
docker images
```

Or filter them:

```bash
docker images | grep python-demo
```

You should see the two project images.

---

# 9. Phase 3 — Load the Images Into kind

Run:

```bash
./scripts/03-load-images.sh
```

The script runs:

```bash
kind load docker-image python-demo-web:1.0.0 --name python-demo
```

and:

```bash
kind load docker-image python-demo-api:1.0.0 --name python-demo
```

## Why is this necessary?

This confuses many beginners.

Your laptop's Docker image list and the container runtime inside kind's Kubernetes nodes are related, but they are not the same shelf.

Grocery analogy:

Imagine the warehouse has a box of cereal.

That does not automatically mean the school cafeteria pantry has the box.

`kind load docker-image` moves the image into the place where the kind cluster can use it.

The flow is:

```text
Python code
   |
   v
Docker build
   |
   v
Image on your computer
   |
   | kind load docker-image
   v
Image available to kind node
   |
   v
Kubernetes can start a Pod using it
```

---

# 10. Before Deployment: Understand YAML Manifests

Kubernetes configuration is often written in YAML.

Here is a shortened Deployment example:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: python-api
spec:
  replicas: 1
```

Think of this as an order form.

```text
kind: Deployment
```

means:

> The object I am asking for is a Deployment.

```text
name: python-api
```

means:

> Call it `python-api`.

```text
replicas: 1
```

means:

> I want one running copy.

Kubernetes reads the document and tries to make reality match it.

---

# 11. What Is a Pod?

A Pod is the smallest normal thing Kubernetes schedules.

A Pod usually contains one main application container, although it can contain multiple cooperating containers.

For our project:

```text
python-web Pod
└── web container

python-api Pod
└── api container
```

Think of a Pod as a classroom and a container as the teacher working inside it.

Why not manage containers directly?

Because Kubernetes needs a unit around the container where it can attach networking, storage, health status, labels, and scheduling information.

## Pods are replaceable

A Pod should usually be treated as replaceable.

If this Pod dies:

```text
python-api-abc123
```

Kubernetes may create:

```text
python-api-xyz789
```

That is why you normally should not depend on one Pod's name or IP address.

A **Service** gives you a more stable way to reach the application.

---

# 12. What Is a Deployment?

A Deployment says how a group of Pods should run.

Our API Deployment contains:

```yaml
spec:
  replicas: 1
```

That means:

> Keep one API Pod running.

If the Pod disappears, the Deployment controller works through its ReplicaSet to restore the desired number.

School analogy:

The staffing plan says:

> We need three lunchroom monitors.

If one monitor goes home sick, the plan still says three are needed, so another person must be assigned.

A Deployment gives Kubernetes that kind of continuing instruction.

---

# 13. Labels and Selectors

Our Pods have labels like:

```yaml
labels:
  app: python-api
```

The Service has a selector:

```yaml
selector:
  app: python-api
```

That is how the Service knows which Pods belong to it.

School analogy:

Every student on the robotics team wears a sticker:

```text
team=robotics
```

A teacher can say:

> Find everyone with `team=robotics`.

That is a selector.

You can inspect labels with:

```bash
kubectl get pods -n python-demo --show-labels
```

You can select only API Pods with:

```bash
kubectl get pods -n python-demo -l app=python-api
```

The `-l` means label selector.

---

# 14. What Is a Namespace?

The project uses:

```text
python-demo
```

as its namespace.

Think of a namespace as a department or school wing.

A school may have:

```text
7th-grade wing
8th-grade wing
music department
sports department
```

A Kubernetes cluster may have:

```text
default
dev
test
prod
python-demo
```

Namespaces help organize names and policies.

List namespaces:

```bash
kubectl get namespaces
```

Short version:

```bash
kubectl get ns
```

Show Pods in our namespace:

```bash
kubectl get pods -n python-demo
```

Without `-n python-demo`, you may accidentally look in the wrong namespace and think your Pods disappeared.

---

# 15. What Is a Service?

Pods can be destroyed and recreated. Their individual addresses are not a good thing for clients to memorize.

A Kubernetes Service gives a stable way to find a changing group of Pods.

Our API Service is similar to:

```yaml
kind: Service
metadata:
  name: python-api
spec:
  selector:
    app: python-api
  ports:
    - port: 80
      targetPort: 8080
```

This means:

```text
Client talks to Service port 80
              |
              v
Service finds Pod labeled app=python-api
              |
              v
Pod receives traffic on port 8080
```

Grocery analogy:

Customers call one main store phone number. They do not memorize the personal phone number of whichever employee is currently working.

The Service is the stable front desk.

## Why port 80 and targetPort 8080?

The Service presents port `80`.

The application inside the Pod listens on `8080`.

So Kubernetes forwards:

```text
Service :80 ---> Pod :8080
```

---

# 16. Phase 4 — Deploy With Helm

Run:

```bash
./scripts/04-deploy-helm.sh
```

The most important command is:

```bash
helm upgrade --install python-demo ./helm/python-demo \
  --namespace python-demo \
  --create-namespace \
  --wait \
  --timeout 2m
```

## Helm Chart

The Chart lives here:

```text
helm/python-demo/
├── Chart.yaml
├── values.yaml
└── templates/
```

### `Chart.yaml`

Describes the package itself.

It is like the label on a school setup binder:

```text
Name: python-demo
Chart version: 0.1.0
App version: 1.0.0
```

### `values.yaml`

Contains settings you are likely to change.

Our file includes:

```yaml
web:
  image: python-demo-web:1.0.0
  replicas: 1
  port: 8080
  servicePort: 80

api:
  image: python-demo-api:1.0.0
  replicas: 1
  port: 8080
  servicePort: 80
```

Think of the templates as blank school forms and `values.yaml` as the answers used to fill them in.

### `templates/`

Contains the Kubernetes templates for:

```text
web Deployment
web Service
api Deployment
api Service
namespace
```

## Helm Release

When Helm installs a Chart, the installed instance is called a **release**.

Our release is named:

```text
python-demo
```

## Breaking down `helm upgrade --install`

```text
helm upgrade --install
```

means:

> If the release is missing, install it. If it already exists, update it.

This makes the command useful in scripts and CI/CD pipelines.

```text
python-demo
```

is the release name.

```text
./helm/python-demo
```

is the Chart location.

```text
--namespace python-demo
```

chooses the namespace.

```text
--create-namespace
```

creates it if necessary.

```text
--wait
```

asks Helm to wait for important resources to become ready before reporting success.

```text
--timeout 2m
```

limits how long it waits.

---

# 17. Useful Helm Commands

## Check Chart formatting and common problems

```bash
helm lint ./helm/python-demo
```

School analogy:

This is like checking your homework for obvious formatting mistakes before turning it in.

## See the YAML Helm would generate

```bash
helm template python-demo ./helm/python-demo
```

This is extremely useful for learning because it lets you see what the templates become.

## List installed releases

```bash
helm list -n python-demo
```

## Check one release

```bash
helm status python-demo -n python-demo
```

## Update a release

```bash
helm upgrade python-demo ./helm/python-demo -n python-demo --wait
```

## See previous revisions

```bash
helm history python-demo -n python-demo
```

## Roll back

```bash
helm rollback python-demo 1 -n python-demo
```

A rollback is like returning to yesterday's known-good school schedule after today's new schedule causes trouble.

## Remove the release

```bash
helm uninstall python-demo -n python-demo
```

---

# 18. Alternate Phase 4 — Deploy With Raw kubectl YAML

Instead of Helm, the project also contains:

```text
k8s/web.yaml
k8s/api.yaml
```

Run:

```bash
./scripts/04-deploy-kubectl.sh
```

Do not manage the same named resources with both raw YAML and the Helm release at the same time while learning. Choose one method for that exercise.

The script creates the namespace and applies the YAML files.

The key command is:

```bash
kubectl apply -f k8s/web.yaml
```

`apply` means approximately:

> Read this file and make the cluster match it.

If the object does not exist, Kubernetes creates it.

If the object already exists, Kubernetes updates it as needed.

## Why learn raw YAML if Helm exists?

Because Helm eventually creates Kubernetes YAML.

Learning raw Kubernetes first is like learning basic arithmetic before using a calculator.

Helm makes repeated deployments easier, but understanding Deployments and Services still matters.

---

# 19. Health Checks: Readiness and Liveness Probes

The Helm templates contain health checks.

Example:

```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 2
  periodSeconds: 5
```

and:

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10
```

## Readiness probe

Question:

> Are you ready to receive customer traffic?

Grocery analogy:

A checkout register might be powered on but still loading software. Customers should not be sent there yet.

If the readiness check fails, Kubernetes can stop routing Service traffic to that Pod until it is ready.

## Liveness probe

Question:

> Are you still alive and functioning?

Grocery analogy:

A register that is completely frozen may need to be restarted.

A failed liveness probe can cause Kubernetes to restart the container.

## Test the health endpoint yourself

After port-forwarding, run:

```bash
curl http://localhost:8080/health
```

Expected result is similar to:

```json
{"service":"web","status":"ok"}
```

---

# 20. CPU and Memory: Requests and Limits

The Helm Deployment contains:

```yaml
resources:
  requests:
    cpu: 25m
    memory: 32Mi
  limits:
    cpu: 250m
    memory: 128Mi
```

## Request

A request tells Kubernetes how much resource the Pod expects to need for scheduling.

School analogy:

> This class needs at least 25 desks.

Grocery analogy:

> This department needs at least one shelf section reserved.

## Limit

A limit puts an upper boundary on resource use.

School analogy:

> This room may not hold more than 30 students.

## What does `25m` CPU mean?

CPU can be expressed in **millicores**.

```text
1000m = 1 CPU core
500m  = half of a CPU core
250m  = one quarter
25m   = 2.5% of one CPU core
```

These demo values are intentionally small.

## What does `Mi` mean?

`32Mi` and `128Mi` are memory amounts measured in mebibytes.

---

# 21. Security Context: Do Not Run as Root

Our Helm Deployment uses:

```yaml
securityContext:
  allowPrivilegeEscalation: false
  runAsNonRoot: true
  capabilities:
    drop: ["ALL"]
```

The Dockerfile also uses:

```dockerfile
USER 65532:65532
```

The idea is simple:

> Give the application only the power it needs.

School analogy:

A student helping in the library does not need the master key to every room in the school.

Grocery analogy:

A cashier does not need access to the building's electrical control room.

Least privilege reduces the damage possible if an application is compromised.

---

# 22. Phase 5 — Test the Application

Run:

```bash
./scripts/05-test.sh
```

This script temporarily creates port forwards for both Services and uses `curl` to test them.

It checks:

```text
web /health
API GET /api/hello
API POST /api/hello
```

## GET request

Example:

```bash
curl 'http://127.0.0.1:18081/api/hello?name=Kubernetes'
```

This is like asking the store information desk a question.

Expected result:

```json
{
  "message": "Hello, Kubernetes!",
  "pod": "python-api-..."
}
```

## POST request

Example:

```bash
curl -X POST http://127.0.0.1:18081/api/hello \
  -H 'Content-Type: application/json' \
  -d '{"name":"Docker"}'
```

Here you send JSON data in the request body.

---

# 23. Phase 6 — Port Forwarding

Run:

```bash
./scripts/06-port-forward.sh
```

For the web service:

```bash
kubectl -n python-demo port-forward svc/python-web 8080:80
```

Then visit:

```text
http://localhost:8080
```

For the API:

```bash
kubectl -n python-demo port-forward svc/python-api 8081:80
```

Then:

```bash
curl 'http://localhost:8081/api/hello?name=Student'
```

## What does port-forward do?

It creates a temporary tunnel from your computer into Kubernetes.

```text
Your browser
localhost:8080
      |
      | kubectl port-forward
      v
python-web Service :80
      |
      v
web Pod :8080
```

School analogy:

It is like temporarily connecting a private phone extension directly to a classroom.

It is excellent for development and debugging.

It is not normally how a public production website is exposed to the Internet.

---

# 24. ClusterIP, NodePort, LoadBalancer, and Ingress

Our Services do not specify a `type`, so they use the normal default Service type: **ClusterIP**.

ClusterIP is mainly for communication inside the cluster.

Think of it as an internal school phone extension.

## NodePort

A NodePort opens a port on cluster nodes.

Analogy:

> Add an outside door with a numbered entrance.

It can be useful for labs, but it is not usually the preferred public production design by itself.

## LoadBalancer

On supported cloud environments, a `LoadBalancer` Service can request an external load balancer.

Analogy:

> A main entrance where a greeter sends customers to available checkout lanes.

## Ingress / Gateway

Ingress and the newer Gateway API patterns can provide HTTP routing to multiple Services.

Example idea:

```text
example.com/       -> web Service
example.com/api    -> API Service
```

Think of one school front desk directing visitors to different rooms based on why they came.

---

# 25. kubectl Command Toolbox

These commands are some of the most useful things to learn.

## `kubectl get`

Show resources.

```bash
kubectl get pods -n python-demo
kubectl get services -n python-demo
kubectl get deployments -n python-demo
kubectl get all -n python-demo
```

Short names also work for many resources:

```bash
kubectl get po -n python-demo
kubectl get svc -n python-demo
kubectl get deploy -n python-demo
```

Think:

> Show me the class list.

## `kubectl describe`

Show detailed information and events.

```bash
kubectl describe pod -n python-demo <pod-name>
```

Think:

> Show me the student's full report and recent notes.

This is especially useful when a Pod will not start.

## `kubectl logs`

Show application output.

```bash
kubectl logs -n python-demo deployment/python-api
```

Follow logs live:

```bash
kubectl logs -f -n python-demo deployment/python-api
```

Think:

> Show me the security camera/event notebook for this application.

## `kubectl exec`

Run a command inside a running container.

Example:

```bash
kubectl exec -it -n python-demo deployment/python-api -- /bin/sh
```

Think:

> Let me temporarily walk into the classroom and look around.

Use this carefully. Debugging inside a container can be useful, but the real fix should normally be made in the image/configuration, not manually changed inside one temporary Pod.

## `kubectl apply`

Create or update resources from YAML.

```bash
kubectl apply -f k8s/api.yaml
```

## `kubectl delete`

Delete a resource.

```bash
kubectl delete -f k8s/api.yaml
```

## `kubectl rollout status`

Watch an update until it finishes.

```bash
kubectl rollout status deployment/python-api -n python-demo
```

## `kubectl rollout restart`

Ask Kubernetes to restart the Pods in a Deployment.

```bash
kubectl rollout restart deployment/python-api -n python-demo
```

## `kubectl rollout history`

See Deployment rollout history.

```bash
kubectl rollout history deployment/python-api -n python-demo
```

## `kubectl scale`

Change the desired number of Pods.

```bash
kubectl scale deployment/python-api \
  --replicas=3 \
  -n python-demo
```

## `kubectl port-forward`

Create a local tunnel to a Kubernetes resource.

```bash
kubectl -n python-demo port-forward svc/python-api 8081:80
```

## `kubectl get events`

Show important events.

```bash
kubectl get events -n python-demo \
  --sort-by=.metadata.creationTimestamp
```

Events are often the first clue when scheduling, image, or health problems occur.

---

# 26. Manual Scaling

Start by checking the current number of API Pods:

```bash
kubectl get pods -n python-demo -l app=python-api
```

Now scale to three:

```bash
kubectl scale deployment/python-api \
  --replicas=3 \
  -n python-demo
```

Watch Kubernetes create the extra Pods:

```bash
kubectl get pods -n python-demo \
  -l app=python-api \
  -w
```

`-w` means **watch**.

Press `Ctrl+C` when finished watching.

## Grocery analogy

One checkout lane is open:

```text
Lane 1
```

The store gets busy, so the manager opens more lanes:

```text
Lane 1
Lane 2
Lane 3
```

Each Pod is another copy that can handle work.

Scale back down:

```bash
kubectl scale deployment/python-api \
  --replicas=1 \
  -n python-demo
```

Kubernetes removes the extra copies until reality matches the desired count again.

---

# 27. Helm-Controlled Scaling

Because Helm manages this project, another way to control scale is through Helm values.

The file currently contains:

```yaml
api:
  replicas: 1
```

Change it to:

```yaml
api:
  replicas: 3
```

Then run:

```bash
helm upgrade python-demo ./helm/python-demo \
  -n python-demo \
  --wait
```

This is usually better than a one-time manual scale when Helm is your source of truth.

Why?

Suppose you manually run:

```bash
kubectl scale deployment/python-api --replicas=3 -n python-demo
```

but `values.yaml` still says:

```yaml
replicas: 1
```

The next Helm upgrade can return the Deployment to one replica because that is what the Helm configuration says.

School analogy:

Changing the classroom count on a sticky note is temporary if the official school schedule still says one classroom.

---

# 28. Automatic Scaling With HPA

HPA means **HorizontalPodAutoscaler**.

Horizontal scaling means adding or removing Pods.

```text
1 Pod -> 2 Pods -> 3 Pods
```

Vertical scaling means changing the CPU/memory size of a Pod.

```text
small Pod -> bigger Pod
```

## Grocery analogy

Horizontal scaling:

> Open more checkout lanes.

Vertical scaling:

> Give one cashier a faster, bigger checkout station.

## Simple HPA command

A common form is:

```bash
kubectl autoscale deployment python-api \
  -n python-demo \
  --cpu=60% \
  --min=1 \
  --max=5
```

This describes a rule like:

> Keep at least one API Pod, never create more than five, and use CPU demand to decide when more copies are needed.

Check it:

```bash
kubectl get hpa -n python-demo
```

More detail:

```bash
kubectl describe hpa python-api -n python-demo
```

Delete it:

```bash
kubectl delete hpa python-api -n python-demo
```

## Important: HPA needs metrics

CPU-based HPA needs a resource metrics API, commonly supplied by **Metrics Server**.

Check whether your cluster has metrics:

```bash
kubectl top pods -n python-demo
```

If you see an error saying the Metrics API is unavailable, CPU-based HPA does not yet have the measurement system it needs.

Think of it like this:

A school cannot decide whether to open another lunch line based on wait time unless somebody is actually measuring the wait time.

## Requests matter to CPU utilization

Our Helm chart already defines CPU requests:

```yaml
requests:
  cpu: 25m
```

That matters because a CPU utilization target such as `60%` is calculated relative to the configured CPU request.

---

# 29. Controlling How Fast Autoscaling Changes

In a larger system, you may not want Kubernetes to jump instantly from 1 Pod to 50 Pods and then back down.

An HPA using `autoscaling/v2` can have behavior rules.

Example idea:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: python-api
  namespace: python-demo
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: python-api
  minReplicas: 1
  maxReplicas: 5
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 60
```

The stabilization window is like a store manager saying:

> Do not close extra checkout lanes the instant the line gets shorter. Wait a little while to make sure the rush is really over.

---

# 30. Secrets: Protect Sensitive Configuration

Applications often need sensitive values:

```text
database passwords
API tokens
private keys
credentials
```

Do not put real passwords directly into your Docker image.

Do not commit real passwords into Git.

Kubernetes has an object called a **Secret** for sensitive configuration.

## Grocery analogy

Normal configuration is like a sign on the wall:

```text
Store opens at 8:00 AM
```

A password is different. It belongs in the manager's safe, not on the wall.

## Create a practice Secret

Use a fake classroom value:

```bash
kubectl create secret generic api-demo-secret \
  -n python-demo \
  --from-literal=API_USERNAME=student \
  --from-literal=API_PASSWORD=practice-only-password
```

List Secrets:

```bash
kubectl get secrets -n python-demo
```

Describe metadata without intentionally printing the secret value:

```bash
kubectl describe secret api-demo-secret -n python-demo
```

Delete the practice Secret:

```bash
kubectl delete secret api-demo-secret -n python-demo
```

## Use a Secret as environment variables

A Deployment can contain:

```yaml
envFrom:
  - secretRef:
      name: api-demo-secret
```

Or reference individual keys:

```yaml
env:
  - name: API_PASSWORD
    valueFrom:
      secretKeyRef:
        name: api-demo-secret
        key: API_PASSWORD
```

## Very important security fact

A Kubernetes Secret is not magic encryption just because the object is named `Secret`.

Secret values are commonly represented in base64 form in YAML/API data, and base64 is **encoding**, not encryption.

For real clusters, administrators should also protect Secrets with strong access control, encryption at rest, restricted RBAC permissions, and appropriate external secret-management systems when needed.

School analogy:

Putting a note in a box labeled “secret” is not enough. You still need to lock the cabinet and control who has the key.

---

# 31. Secret Safety Rules for Students

Use these habits from the beginning:

1. Use fake/demo passwords in tutorials.
2. Never commit real passwords or tokens to Git.
3. Do not bake secrets into Docker images.
4. Give users and ServiceAccounts only the access they need.
5. Avoid printing secrets in logs.
6. Rotate important credentials when necessary.
7. Protect production Secrets with proper encryption and access controls.

---

# 32. Network Access: Who Is Allowed to Talk to Whom?

Inside Kubernetes, applications often talk over the network.

Imagine a school:

```text
students
teachers
principal's office
cafeteria
server room
```

Not everyone should be allowed into every room.

A Kubernetes **NetworkPolicy** can define network access rules for selected Pods.

## Grocery analogy

Customers can enter the shopping floor.

Only employees can enter the stockroom.

Only certain staff can enter the cash office.

NetworkPolicy provides a similar idea for network traffic.

---

# 33. Default Network Behavior

In a namespace with no isolating NetworkPolicies, Pods are normally allowed to send and receive traffic according to the cluster network's normal behavior.

A common security pattern is:

1. Start with a deny policy.
2. Add specific allow policies for the traffic the application really needs.

For example:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: python-demo
spec:
  podSelector: {}
  policyTypes:
    - Ingress
```

This selects all Pods in the namespace and provides no ingress allow rule.

Conceptually:

> No one gets through the classroom doors unless another rule allows them.

## Important NetworkPolicy requirement

NetworkPolicy rules are enforced by the cluster's networking implementation, often called the **CNI plugin**.

Creating a NetworkPolicy object does not by itself guarantee enforcement if the network plugin does not support NetworkPolicy.

For a learning environment, verify the networking plugin you are using supports the policies you want to test.

---

# 34. Allow Only Web Pods to Reach API Pods

Suppose we want this design:

```text
web Pods  --------allowed-------> API Pods :8080
other Pods -------blocked-------> API Pods :8080
```

An example NetworkPolicy is:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-web-to-api
  namespace: python-demo
spec:
  podSelector:
    matchLabels:
      app: python-api
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: python-web
      ports:
        - protocol: TCP
          port: 8080
```

Break it apart.

```yaml
podSelector:
  matchLabels:
    app: python-api
```

means:

> These rules protect Pods labeled `app=python-api`.

```yaml
from:
  - podSelector:
      matchLabels:
        app: python-web
```

means:

> Allow traffic from Pods labeled `app=python-web`.

```yaml
port: 8080
```

means:

> Allow that traffic to the application port.

Save it as a file and apply it with:

```bash
kubectl apply -f allow-web-to-api.yaml
```

Inspect policies:

```bash
kubectl get networkpolicy -n python-demo
```

Short form:

```bash
kubectl get netpol -n python-demo
```

Describe one:

```bash
kubectl describe networkpolicy allow-web-to-api -n python-demo
```

---

# 35. Be Careful With Egress Deny Rules

Egress means traffic leaving a Pod.

A rule that denies all egress can also block things you did not think about, including DNS lookups unless DNS is explicitly allowed.

School analogy:

If you lock every exit from a classroom, students cannot even walk to the library unless you create an allowed route.

Security rules should be tested carefully.

---

# 36. Service Networking Versus NetworkPolicy

These ideas solve different problems.

## Service

Answers:

> Where should traffic go?

Example:

```text
python-api Service -> API Pods
```

## NetworkPolicy

Answers:

> Who is allowed to send or receive traffic?

Example:

```text
web Pods -> API Pods = allowed
random Pod -> API Pods = denied
```

Grocery analogy:

A Service is the address of the stockroom.

A NetworkPolicy is the rule about who is allowed through the stockroom door.

---

# 37. Change the Python Code Safely

Suppose you edit:

```text
apps/api/app.py
```

Docker images do not automatically change just because the source file changed.

Remember:

```text
Source code != image
```

You must rebuild.

Run:

```bash
./scripts/02-build-images.sh
```

Then load the rebuilt image into kind:

```bash
./scripts/03-load-images.sh
```

Then restart the Deployment:

```bash
kubectl rollout restart deployment/python-api -n python-demo
```

Watch it:

```bash
kubectl rollout status deployment/python-api -n python-demo
```

Better long-term method:

1. Give the new build a new image tag.
2. Update the Kubernetes/Helm configuration to that new tag.
3. Perform a rollout.

Example:

```text
1.0.0 -> 1.0.1
```

That makes it much easier to know exactly which code is running.

---

# 38. Rolling Updates

Deployments can update Pods gradually rather than stopping everything at once.

Imagine three checkout lanes:

```text
old v1   old v1   old v1
```

During an update Kubernetes can move toward:

```text
new v2   old v1   old v1
```

then:

```text
new v2   new v2   old v1
```

then:

```text
new v2   new v2   new v2
```

This helps keep an application available during updates.

Watch a rollout:

```bash
kubectl rollout status deployment/python-api -n python-demo
```

Inspect rollout history:

```bash
kubectl rollout history deployment/python-api -n python-demo
```

---

# 39. Troubleshooting: A Simple Order to Follow

When something fails, do not randomly change many things at once.

Use a repeatable order.

## Step 1: Is the cluster alive?

```bash
kubectl get nodes
```

Nodes should normally show `Ready`.

## Step 2: Are the Pods running?

```bash
kubectl get pods -n python-demo
```

Look at:

```text
STATUS
READY
RESTARTS
```

## Step 3: Describe the failing Pod

```bash
kubectl describe pod -n python-demo <pod-name>
```

Read the Events section near the bottom.

## Step 4: Read application logs

```bash
kubectl logs -n python-demo deployment/python-api
```

## Step 5: Check Services

```bash
kubectl get svc -n python-demo
```

## Step 6: Check labels

```bash
kubectl get pods -n python-demo --show-labels
```

Make sure the Service selector matches the Pod labels.

## Step 7: Check endpoints

Depending on cluster version and resources, useful commands include:

```bash
kubectl get endpoints -n python-demo
kubectl get endpointslices -n python-demo
```

If a Service has no backing endpoints, it may not be finding any matching ready Pods.

## Step 8: Check events

```bash
kubectl get events -n python-demo \
  --sort-by=.metadata.creationTimestamp
```

---

# 40. Common Pod Problems

## `ImagePullBackOff`

Meaning:

> Kubernetes cannot get the container image it needs.

For this project, first try:

```bash
./scripts/03-load-images.sh
```

Then:

```bash
kubectl rollout restart deployment/python-web -n python-demo
kubectl rollout restart deployment/python-api -n python-demo
```

Possible causes include:

```text
wrong image name
wrong tag
image was not loaded into kind
private registry authentication problem
registry unavailable
```

## `CrashLoopBackOff`

Meaning:

> The container starts, crashes, Kubernetes retries, and the cycle continues.

Check:

```bash
kubectl logs -n python-demo <pod-name>
```

and:

```bash
kubectl describe pod -n python-demo <pod-name>
```

## `Pending`

Meaning:

> Kubernetes has not successfully scheduled or started the Pod yet.

Possible causes include insufficient CPU/memory, node issues, storage problems, or scheduling restrictions.

---

# 41. Understanding the Project's `run-all.sh`

The file runs the phases in this order:

```text
00-check-prereqs.sh
        |
        v
01-create-cluster.sh
        |
        v
02-build-images.sh
        |
        v
03-load-images.sh
        |
        v
04-deploy-helm.sh
        |
        v
05-test.sh
```

That order matters.

You cannot load an image that has not been built.

You cannot deploy to a cluster that does not exist.

You cannot test an application that has not been deployed.

School analogy:

You cannot:

```text
teach class
```

before you:

```text
open school -> prepare room -> assign teacher -> admit students
```

Run the complete sequence with:

```bash
./scripts/run-all.sh
```

---

# 42. Full Hands-On Lab

## Step 1 — Make scripts executable

```bash
chmod +x scripts/*.sh
```

## Step 2 — Check tools

```bash
./scripts/00-check-prereqs.sh
```

## Step 3 — Create the cluster

```bash
./scripts/01-create-cluster.sh
```

Verify:

```bash
kubectl config current-context
kubectl get nodes -o wide
```

## Step 4 — Build images

```bash
./scripts/02-build-images.sh
```

Verify:

```bash
docker images | grep python-demo
```

## Step 5 — Load images

```bash
./scripts/03-load-images.sh
```

## Step 6 — Deploy with Helm

```bash
./scripts/04-deploy-helm.sh
```

Verify:

```bash
helm list -n python-demo
kubectl get all -n python-demo
```

## Step 7 — Test

```bash
./scripts/05-test.sh
```

## Step 8 — Open the web application

Terminal 1:

```bash
kubectl -n python-demo port-forward svc/python-web 8080:80
```

Browser:

```text
http://localhost:8080
```

## Step 9 — Open the API

Terminal 2:

```bash
kubectl -n python-demo port-forward svc/python-api 8081:80
```

Terminal 3:

```bash
curl 'http://localhost:8081/api/hello?name=Student'
```

## Step 10 — Scale the API

```bash
kubectl scale deployment/python-api \
  --replicas=3 \
  -n python-demo
```

Check:

```bash
kubectl get pods -n python-demo -l app=python-api
```

## Step 11 — Watch self-healing

Get the Pods:

```bash
kubectl get pods -n python-demo -l app=python-api
```

Delete one API Pod:

```bash
kubectl delete pod -n python-demo <one-api-pod-name>
```

Immediately check again:

```bash
kubectl get pods -n python-demo -l app=python-api -w
```

You should see Kubernetes work toward the desired three replicas again.

This is one of the best demonstrations of desired state.

## Step 12 — Return to one replica

If Helm is managing your app, edit `helm/python-demo/values.yaml` and set:

```yaml
api:
  replicas: 1
```

Then:

```bash
helm upgrade python-demo ./helm/python-demo \
  -n python-demo \
  --wait
```

---

# 43. Optional Secret Lab

Create a fake Secret:

```bash
kubectl create secret generic school-demo-secret \
  -n python-demo \
  --from-literal=USERNAME=student \
  --from-literal=PASSWORD=not-a-real-password
```

List it:

```bash
kubectl get secret -n python-demo
```

Describe it:

```bash
kubectl describe secret school-demo-secret -n python-demo
```

Notice that `describe` can show metadata and key names without being used as a normal way to print the actual sensitive values.

Delete it when finished:

```bash
kubectl delete secret school-demo-secret -n python-demo
```

Lesson:

> Secrets are configuration objects that require careful permission and storage protection. Do not treat base64 text as encryption.

---

# 44. Optional NetworkPolicy Lab Design

Before testing NetworkPolicy enforcement, verify that your cluster networking solution supports NetworkPolicy.

Create this file as `allow-web-to-api.yaml`:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-web-to-api
  namespace: python-demo
spec:
  podSelector:
    matchLabels:
      app: python-api
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: python-web
      ports:
        - protocol: TCP
          port: 8080
```

Apply it:

```bash
kubectl apply -f allow-web-to-api.yaml
```

Inspect it:

```bash
kubectl get netpol -n python-demo
kubectl describe netpol allow-web-to-api -n python-demo
```

Remove it:

```bash
kubectl delete -f allow-web-to-api.yaml
```

Lesson:

> Services route traffic. NetworkPolicies control which traffic is allowed.

---

# 45. Optional Autoscaling Lab Design

First check metrics:

```bash
kubectl top pods -n python-demo
```

If the metrics API is available, create an HPA:

```bash
kubectl autoscale deployment python-api \
  -n python-demo \
  --cpu=60% \
  --min=1 \
  --max=5
```

Watch it:

```bash
kubectl get hpa -n python-demo -w
```

Check details:

```bash
kubectl describe hpa python-api -n python-demo
```

Remove it:

```bash
kubectl delete hpa python-api -n python-demo
```

Lesson:

> HPA is the automatic checkout-lane manager, but it needs measurements before it can make good decisions.

---

# 46. Why the Helm Version Is Safer Than the Raw YAML in This Project

The raw `k8s/web.yaml` and `k8s/api.yaml` files are intentionally simple for learning.

The Helm templates add important production-style ideas:

```text
readiness probes
liveness probes
CPU requests
memory requests
CPU limits
memory limits
runAsNonRoot
no privilege escalation
dropped Linux capabilities
```

That makes the Helm path a better example of how a real application starts adding reliability and security controls.

The raw YAML is useful because it is easier to read when first learning Deployment and Service basics.

---

# 47. Kubernetes Does Not Automatically Solve Everything

Kubernetes is powerful, but it is not magic.

It does not automatically:

```text
write secure application code
choose correct CPU limits
protect badly stored passwords
back up your database
fix every network design
make a broken image work
know how your business should scale
```

It gives you tools for managing distributed applications. You still need good application design, security, testing, observability, backups, and operational practices.

---

# 48. A Complete Mental Model

Think about the project like a grocery store opening for the day.

```text
Dockerfile
  = recipe for building a product

Docker image
  = packaged product ready to use

kind cluster
  = practice grocery store organization

Node
  = store building

Control plane
  = management office

Pod
  = checkout station

Container
  = cashier running the checkout software

Deployment
  = staffing plan saying how many checkout stations must run

Service
  = front desk that knows which checkout stations are available

Label
  = department/name sticker

Selector
  = rule for finding matching stations

Readiness probe
  = is this register ready for customers?

Liveness probe
  = is this register still functioning?

Resource request
  = amount of space/resources reserved

Resource limit
  = maximum resources allowed

Secret
  = protected safe for sensitive values

NetworkPolicy
  = employees-only door/access rules

HPA
  = manager opening or closing lanes based on demand

kubectl
  = management walkie-talkie / command console

Helm
  = reusable store-opening kit containing many forms
```

---

# 49. Command Cheat Sheet

## Cluster

```bash
kubectl cluster-info
kubectl config current-context
kubectl get nodes -o wide
```

## Namespace

```bash
kubectl get ns
kubectl get all -n python-demo
```

## Pods

```bash
kubectl get pods -n python-demo
kubectl get pods -n python-demo -o wide
kubectl get pods -n python-demo --show-labels
kubectl describe pod -n python-demo <pod-name>
kubectl logs -n python-demo <pod-name>
```

## Deployment

```bash
kubectl get deployment -n python-demo
kubectl describe deployment python-api -n python-demo
kubectl rollout status deployment/python-api -n python-demo
kubectl rollout restart deployment/python-api -n python-demo
kubectl scale deployment/python-api --replicas=3 -n python-demo
```

## Services

```bash
kubectl get svc -n python-demo
kubectl describe svc python-api -n python-demo
kubectl -n python-demo port-forward svc/python-api 8081:80
```

## Labels

```bash
kubectl get pods -n python-demo -l app=python-api
```

## Network policies

```bash
kubectl get netpol -n python-demo
kubectl describe netpol <policy-name> -n python-demo
```

## Secrets

```bash
kubectl get secrets -n python-demo
kubectl describe secret <secret-name> -n python-demo
```

## HPA

```bash
kubectl get hpa -n python-demo
kubectl describe hpa python-api -n python-demo
```

## Events

```bash
kubectl get events -n python-demo \
  --sort-by=.metadata.creationTimestamp
```

## Helm

```bash
helm lint ./helm/python-demo
helm template python-demo ./helm/python-demo
helm list -n python-demo
helm status python-demo -n python-demo
helm upgrade python-demo ./helm/python-demo -n python-demo --wait
helm history python-demo -n python-demo
helm rollback python-demo 1 -n python-demo
helm uninstall python-demo -n python-demo
```

---

# 50. Student Challenges

Try these after the basic project works.

## Challenge 1 — Change the greeting

Edit the Python API so it returns a different message.

Then rebuild, reload, restart, and test it.

Question:

> Why did editing the Python file alone not change the running Pod?

Answer:

Because the Pod runs the code packaged inside the Docker image.

## Challenge 2 — Scale to four APIs

Run:

```bash
kubectl scale deployment/python-api --replicas=4 -n python-demo
```

Then:

```bash
kubectl get pods -n python-demo -l app=python-api
```

Question:

> What Kubernetes object remembers that four copies are desired?

Answer:

The Deployment's desired replica count.

## Challenge 3 — Delete one Pod

Delete one API Pod and watch Kubernetes replace it.

Question:

> Why did the application come back?

Answer:

Because the Deployment still says the desired number of replicas should exist.

## Challenge 4 — Break an image name

In a learning environment only, change an image name to something that does not exist and observe the error.

Use:

```bash
kubectl get pods -n python-demo
kubectl describe pod -n python-demo <pod-name>
```

Then fix the image.

This teaches you how `ImagePullBackOff` problems look.

## Challenge 5 — Change Helm replicas

Change:

```yaml
api:
  replicas: 1
```

to:

```yaml
api:
  replicas: 2
```

Run a Helm upgrade and watch Kubernetes create the additional Pod.

---

# 51. Cleanup

When you are completely finished with the local cluster, run:

```bash
./scripts/99-destroy.sh
```

The key command is:

```bash
kind delete cluster --name python-demo
```

This deletes the practice Kubernetes cluster.

The Docker images built on your computer may still exist.

See them with:

```bash
docker images | grep python-demo
```

If you intentionally want to remove those local images too:

```bash
docker image rm python-demo-web:1.0.0

docker image rm python-demo-api:1.0.0
```

---

# 52. Final Review

If you remember only ten ideas, remember these:

1. **Docker images package the application.**
2. **Containers are running copies of images.**
3. **A Kubernetes cluster contains nodes that run workloads.**
4. **Pods are the normal scheduling unit for containers.**
5. **Deployments keep the requested number of Pods running and manage updates.**
6. **Services give changing Pods a stable network destination.**
7. **`kubectl` is your main command-line tool for talking to Kubernetes.**
8. **Helm packages reusable Kubernetes templates and settings.**
9. **Secrets and NetworkPolicies are security tools, but they must be configured and protected correctly.**
10. **Scaling changes how many copies run; HPA can automate that when metrics are available.**

The big idea underneath all ten is still the same:

> You describe the state you want, and Kubernetes continuously works to make the real cluster match that desired state.

---

# 53. Official References

Use official documentation when you want to go deeper:

- Kubernetes documentation: https://kubernetes.io/docs/
- kubectl reference: https://kubernetes.io/docs/reference/kubectl/
- Kubernetes Deployments: https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
- Kubernetes Services: https://kubernetes.io/docs/concepts/services-networking/service/
- Kubernetes NetworkPolicy: https://kubernetes.io/docs/concepts/services-networking/network-policies/
- Kubernetes Secrets: https://kubernetes.io/docs/concepts/configuration/secret/
- Kubernetes Horizontal Pod Autoscaling: https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/
- Kubernetes container images: https://kubernetes.io/docs/concepts/containers/images/
- Helm documentation: https://helm.sh/docs/
- kind documentation: https://kind.sigs.k8s.io/docs/user/quick-start/

---

# Extra Chapter: Load Balancers

The project now includes a dedicated hands-on load-balancer lesson:

```text
docs/LOAD-BALANCER-LESSON.md
```

It explains `ClusterIP`, `NodePort`, and `LoadBalancer` using school and grocery
store examples; shows how to use `cloud-provider-kind` locally; keeps the API
private; and includes scaling, testing, troubleshooting, and Helm examples.
