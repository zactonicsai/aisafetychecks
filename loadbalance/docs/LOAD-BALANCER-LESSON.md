# Kubernetes Load Balancer Lesson

## Goal

In this lesson, we add a **front door** to the Python web application.

The safest beginner architecture is:

```text
Internet / your laptop
        |
        v
+-----------------------+
| LoadBalancer Service  |   <- public front door
| python-web :80        |
+-----------+-----------+
            |
            v
     +-------------+
     | Web Pods    |
     | port 8080   |
     +-------------+
            |
            | internal cluster traffic
            v
+-----------------------+
| ClusterIP Service     |   <- employees-only hallway
| python-api :80        |
+-----------+-----------+
            |
            v
     +-------------+
     | API Pods    |
     | port 8080   |
     +-------------+
```

The web service is exposed. The API stays internal.

---

## 1. Grocery-store example

Imagine a grocery store has four checkout lanes.

Customers should not need to know which cashier is free. They enter through the
same front door, and the store directs them to an available checkout lane.

A Kubernetes LoadBalancer works in a similar way:

```text
Customer requests
     |
     v
Load balancer
 /    |    \
Pod A Pod B Pod C
```

If you scale the web Deployment from one Pod to three Pods, clients still use the
same Service address. Kubernetes and the load-balancer implementation direct
traffic toward the Pods selected by the Service.

### School example

Think about a school office phone number.

Parents call one public number. They do not need the private extension of every
teacher. The office acts as the public entry point and routes requests inside.

A Kubernetes LoadBalancer Service is like that public phone number.

---

## 2. Service types: three doors

### ClusterIP - inside-only door

```yaml
type: ClusterIP
```

This is the normal default. It is reachable from inside the Kubernetes cluster.

Use it for things like databases, APIs, Redis, and other services that should not
need a direct public entrance.

### NodePort - special door on every node

```yaml
type: NodePort
```

Kubernetes opens a port on each node. This is useful for labs and as a building
block, but it is usually not the friendly public address you want users to type.

### LoadBalancer - managed front door

```yaml
type: LoadBalancer
```

This asks a load-balancer provider for an external entry point.

On AWS, Azure, or Google Cloud, the cloud integration can create a cloud load
balancer. On a local kind cluster, there is no cloud provider, so we add
`cloud-provider-kind` for this lesson.

---

## 3. Why `type: LoadBalancer` alone is not enough in kind

Kubernetes understands the request:

> "I want this Service to have an external load balancer."

But Kubernetes itself does not magically create a physical or cloud load
balancer. Something outside the core Service object must do that job.

In a local kind cluster, `cloud-provider-kind` watches for Services of type
`LoadBalancer` and creates local load-balancer containers for them.

Without a provider, this command may show:

```text
NAME         TYPE           CLUSTER-IP      EXTERNAL-IP
python-web   LoadBalancer   10.96.100.20    <pending>
```

`<pending>` means:

> Kubernetes asked for a load balancer, but nobody has supplied one yet.

---

## 4. Install the local load-balancer helper

Run:

```bash
./scripts/07-install-loadbalancer-helper.sh
```

On macOS with Homebrew, the important command is:

```bash
brew install cloud-provider-kind
```

Another supported installation method is:

```bash
go install sigs.k8s.io/cloud-provider-kind@latest
```

Check it:

```bash
cloud-provider-kind --help
```

---

## 5. Start the load-balancer controller

Open a second terminal and keep this process running:

```bash
cloud-provider-kind --enable-lb-port-mapping
```

If your system requires extra privileges:

```bash
sudo cloud-provider-kind --enable-lb-port-mapping
```

### What is this process doing?

Think of it as a student standing at the school entrance watching the request
board.

When Kubernetes posts this request:

```text
Please create a LoadBalancer for python-web.
```

`cloud-provider-kind` sees it and creates the local networking pieces needed to
route traffic toward the Service.

---

## 6. Change the web Service to LoadBalancer

The Helm chart now has these values:

```yaml
web:
  serviceType: ClusterIP

api:
  serviceType: ClusterIP
```

The load-balancer script overrides only the web value:

```bash
helm upgrade --install python-demo ./helm/python-demo \
  --namespace python-demo \
  --create-namespace \
  --set web.serviceType=LoadBalancer \
  --set api.serviceType=ClusterIP \
  --wait
```

Run the project helper:

```bash
./scripts/08-enable-loadbalancer.sh
```

### Why keep the API ClusterIP?

Because not every application needs a door to the outside world.

Grocery-store version:

```text
Front entrance             Stockroom door
      |                           |
 customers allowed         employees only
      |                           |
LoadBalancer                ClusterIP
      |                           |
 Web Pods -----------------> API Pods
```

A smaller public attack surface is easier to protect.

---

## 7. Inspect the Service

Run:

```bash
kubectl get services -n python-demo
```

You should eventually see something like:

```text
NAME         TYPE           CLUSTER-IP      EXTERNAL-IP    PORT(S)
python-web   LoadBalancer   10.96.20.10     172.18.0.10   80:31234/TCP
python-api   ClusterIP      10.96.30.20     <none>         80/TCP
```

Watch until the address appears:

```bash
kubectl get svc python-web -n python-demo -w
```

Stop watching with:

```text
Control + C
```

---

## 8. Understand every column

### NAME

```text
python-web
```

The Service name.

### TYPE

```text
LoadBalancer
```

The kind of entrance Kubernetes is creating.

### CLUSTER-IP

```text
10.96.20.10
```

The private Service address used inside the cluster.

### EXTERNAL-IP

```text
172.18.0.10
```

The address supplied by the load-balancer implementation.

### PORT(S)

```text
80:31234/TCP
```

This says the Service accepts TCP traffic on port 80. Depending on the
implementation, Kubernetes may also allocate a NodePort such as `31234`.

---

## 9. Follow one request

A request may travel like this:

```text
curl / browser
      |
      v
LoadBalancer :80
      |
      v
python-web Service :80
      |
      v
one selected Web Pod :8080
```

The Service does **not** copy the request to every Pod. It provides one stable
front door for a changing set of backend Pods.

---

## 10. Test it

Run:

```bash
./scripts/09-test-loadbalancer.sh
```

You can also get the LoadBalancer IP yourself:

```bash
LB_IP=$(kubectl get svc python-web \
  -n python-demo \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

echo "$LB_IP"
```

Then try:

```bash
curl "http://${LB_IP}:80/"
```

### macOS / Docker Desktop note

The LoadBalancer IP may be an address inside Docker's private network. The
`--enable-lb-port-mapping` option can map the LoadBalancer to a random host port.

See the mapping:

```bash
docker ps --format 'table {{.Names}}\t{{.Ports}}' | grep kindccm
```

Example:

```text
kindccm-ABCDEF   0.0.0.0:42381->80/tcp
```

Then use:

```bash
curl http://localhost:42381/
```

Think of `42381` as the temporary outside door Docker gave the local lab.

---

## 11. Scale the application behind the load balancer

Start with one web Pod:

```bash
kubectl get pods -n python-demo -l app=python-web
```

Scale to three:

```bash
kubectl scale deployment/python-web \
  --replicas=3 \
  -n python-demo
```

Watch the new Pods:

```bash
kubectl get pods -n python-demo -l app=python-web -w
```

Now the picture is:

```text
             LoadBalancer
                  |
             python-web
              Service
          /       |       \
         v        v        v
      Web Pod  Web Pod  Web Pod
```

The outside address stays the same even though the number of Pods changed.

That is one of the big advantages of Services: clients do not have to track Pod
IPs, which can appear and disappear.

---

## 12. Does the LoadBalancer decide how many Pods exist?

No.

This is an important difference.

### Deployment

Controls how many Pods you want.

```text
Deployment -> number of workers
```

### HPA

Can change the number of Pods automatically based on metrics.

```text
HPA -> automatic staffing manager
```

### Service / LoadBalancer

Gives traffic a stable entrance and routes to healthy matching Pods.

```text
LoadBalancer -> front entrance / traffic director
```

So:

```text
HPA/Deployment controls HOW MANY workers exist.
LoadBalancer controls HOW traffic reaches the workers.
```

---

## 13. See the backend endpoints

Run:

```bash
kubectl get endpointslices \
  -n python-demo \
  -l kubernetes.io/service-name=python-web
```

This helps show which Pod addresses sit behind the Service.

Grocery-store analogy:

```text
Service name = checkout department
EndpointSlice = current list of open checkout lanes
```

When Pods appear or disappear, Kubernetes updates that list.

---

## 14. LoadBalancer and health checks

A load balancer should not keep sending customers to a broken checkout lane.

Kubernetes uses readiness information to decide whether a Pod should receive
Service traffic.

Your Deployment includes readiness/liveness concepts in the main tutorial.

Think of readiness as this question:

> "Is this cashier ready to take the next customer?"

If a Pod is not Ready, it should not be treated as a normal backend endpoint for
Service traffic.

---

## 15. LoadBalancer and NetworkPolicy are different

Students often mix these up.

### LoadBalancer

Answers:

> How does traffic enter?

### NetworkPolicy

Answers:

> Once traffic is in the cluster, which Pods are allowed to talk to which other
> Pods?

You may use both:

```text
Internet
   |
LoadBalancer
   |
Web Pods
   |
NetworkPolicy says web may talk to API
   |
API Pods
```

A LoadBalancer is not a replacement for firewall rules, TLS, authentication,
Secrets, or NetworkPolicies.

---

## 16. LoadBalancer and Secrets are different

A Secret might hold a password or token used by the application.

A LoadBalancer moves network traffic.

Do not put passwords into Service YAML such as:

```yaml
metadata:
  name: password123
```

Instead, application credentials belong in an appropriate secret-management
mechanism, and access should be limited to the workloads that need them.

---

## 17. Raw kubectl version

If you are learning without Helm, the project includes:

```text
k8s/web-loadbalancer-service.yaml
```

Apply it:

```bash
kubectl apply -f k8s/web-loadbalancer-service.yaml
```

Inspect it:

```bash
kubectl get svc python-web -n python-demo
```

See the full object:

```bash
kubectl get svc python-web -n python-demo -o yaml
```

Describe it in a human-friendly format:

```bash
kubectl describe svc python-web -n python-demo
```

---

## 18. Helm version

Helm lets us put the Service type into `values.yaml`:

```yaml
web:
  serviceType: LoadBalancer
```

and use it in the template:

```yaml
spec:
  type: {{ .Values.web.serviceType }}
```

The same chart can therefore work in different environments.

Local learning environment:

```yaml
web:
  serviceType: ClusterIP
```

Load-balancer lab:

```yaml
web:
  serviceType: LoadBalancer
```

This is one reason Helm is useful: values can change without copying the whole
Kubernetes manifest.

---

## 19. Troubleshooting

### EXTERNAL-IP stays `<pending>`

Check that cloud-provider-kind is running:

```bash
ps aux | grep cloud-provider-kind
```

Check the Service:

```bash
kubectl describe svc python-web -n python-demo
```

Check cluster events:

```bash
kubectl get events \
  -n python-demo \
  --sort-by=.metadata.creationTimestamp
```

### Service exists but page does not load

Check Pods:

```bash
kubectl get pods -n python-demo -o wide
```

Check Service selectors:

```bash
kubectl describe svc python-web -n python-demo
```

Check EndpointSlices:

```bash
kubectl get endpointslices -n python-demo
```

Check application logs:

```bash
kubectl logs -n python-demo deployment/python-web
```

Test from inside the cluster:

```bash
kubectl run curl-test \
  -n python-demo \
  --rm -it \
  --restart=Never \
  --image=curlimages/curl \
  -- curl http://python-web
```

If inside access works but outside access does not, focus on the LoadBalancer,
Docker networking, host-port mapping, or firewall rather than the Python app.

---

## 20. Going from kind to AWS/Azure/GCP

The idea stays almost the same:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: python-web
spec:
  type: LoadBalancer
```

The difference is **who fulfills the request**.

```text
kind       -> cloud-provider-kind
AWS        -> AWS/cloud load-balancer integration
Azure      -> Azure/cloud load-balancer integration
Google     -> Google/cloud load-balancer integration
```

Cloud platforms also have provider-specific choices and annotations, so always
check the provider documentation before exposing production traffic.

---

## 21. Student challenge

1. Start with one web Pod.
2. Enable the LoadBalancer.
3. Record the Service's external address.
4. Scale the web Deployment to three Pods.
5. Check the EndpointSlices.
6. Delete one web Pod.
7. Watch Kubernetes replace it.
8. Verify the LoadBalancer entry point did not need to change.
9. Change the web Service back to `ClusterIP`.
10. Explain why the API should usually remain private unless there is a real
    reason to expose it.

Commands:

```bash
kubectl get svc -n python-demo
kubectl get pods -n python-demo -o wide
kubectl scale deployment/python-web --replicas=3 -n python-demo
kubectl get endpointslices -n python-demo
kubectl delete pod -n python-demo <web-pod-name>
kubectl get pods -n python-demo -w
```

---

## 22. Big-picture memory trick

```text
IMAGE         = packaged application
POD           = one running worker
DEPLOYMENT    = staffing plan
SERVICE       = stable department phone number
LOADBALANCER  = public front door
NETWORKPOLICY = hallway/security rules
SECRET        = locked credential box
HPA           = automatic staffing manager
KUBECTL       = command radio to Kubernetes
HELM          = reusable setup binder
```

If you remember the grocery-store picture, the pieces become much easier to
connect.
