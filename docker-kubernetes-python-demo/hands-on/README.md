# Hands-On Kubernetes and Helm Command Lab

This directory teaches what each command does. It complements the automated
scripts in `../scripts/`; it does not replace or remove them.

## Goal

You will learn how Docker, kind, `kubectl`, Kubernetes YAML, and Helm work
together on macOS. Each numbered script:

1. explains the command;
2. prints the exact command;
3. runs it;
4. tells you what to inspect next.

Run the lessons from this directory:

```bash
cd hands-on
chmod +x lessons/*.sh
./lessons/01-check-tools.sh
```

## Mental model

| Tool or file | Job |
| --- | --- |
| Docker Desktop | Runs containers on your Mac. |
| kind | Creates Kubernetes nodes as Docker containers. |
| `kubectl` | Sends requests to the Kubernetes API server. |
| kubeconfig | Stores cluster addresses, users, and the selected context. |
| Kubernetes YAML | Declares the state you want Kubernetes to maintain. |
| Helm | Renders and manages groups of Kubernetes YAML files called charts. |
| Helm values YAML | Supplies chart settings without editing chart templates. |

## Configuration files included

| File | Why it is needed |
| --- | --- |
| `config/kind-config.yaml` | Defines one control plane, two workers, and the Mac-to-NodePort mapping. |
| `config/namespace.yaml` | Creates the isolated `hands-on` namespace. |
| `config/deployment.yaml` | Defines two nginx Pods and their CPU/memory limits. |
| `config/service.yaml` | Gives the changing Pods one stable NodePort endpoint. |
| `config/configmap.yaml` | Stores safe, non-secret application settings. |
| `config/secret-example.yaml` | Documents Secret structure; it contains placeholders and is not applied. |
| `config/keycloak-values.yaml` | Overrides the Keycloak Helm chart for this local lab. |

## Lesson order

| Lesson | Main command | What you learn |
| --- | --- | --- |
| 01 | version checks | Which command-line tools are installed. |
| 02 | `docker info` | Whether the Docker engine is ready. |
| 03 | `kind create cluster` | How kind turns Docker containers into Kubernetes nodes. |
| 04 | `kubectl config` | How contexts choose a cluster and namespace. |
| 05 | `kubectl cluster-info` | How to verify the API server. |
| 06 | `kubectl get nodes` | How to inspect cluster machines. |
| 07 | `kubectl get pods -A` | How to inspect Kubernetes system components. |
| 08 | `kubectl apply` | How declarative YAML creates a namespace. |
| 09 | `kubectl explain` | How to look up fields without guessing YAML. |
| 10 | `kubectl apply` | How a Deployment creates and maintains Pods. |
| 11 | `kubectl rollout status` | How to wait for a Deployment safely. |
| 12 | `kubectl get/describe` | How to inspect Pods and events. |
| 13 | `kubectl apply` | How a Service selects Pods using labels. |
| 14 | `curl` | How traffic reaches nginx through NodePort. |
| 15 | `kubectl logs` | How to read container output. |
| 16 | `kubectl exec` | How to run a command inside a container. |
| 17 | `kubectl scale` | How to change the desired replica count. |
| 18 | `kubectl delete pod` | How Deployment self-healing works. |
| 19 | ConfigMap and Secret | How configuration differs from sensitive data. |
| 20 | `helm repo` | How Helm locates charts. |
| 21 | `helm search/show` | How to inspect chart versions and defaults. |
| 22 | `helm template` | How to preview generated Kubernetes YAML. |
| 23 | Secret creation | How Keycloak receives generated credentials. |
| 24 | `helm upgrade --install` | How to install or safely rerun a Helm release. |
| 25 | `helm list/status` | How to inspect Helm-managed resources. |
| 26 | `kubectl port-forward` | How to access Keycloak only from your Mac. |
| 27 | troubleshooting | A practical investigation sequence. |
| 90 | uninstall/delete | Removes lab applications but keeps the cluster. |
| 99 | `kind delete cluster` | Removes the entire local cluster. |

## Suggested learning workflow

Run one script, read its output, then inspect the referenced YAML. Do not rush
through the lessons with a loop: the useful part is comparing the command with
the cluster state before and after it runs.

Commands that keep running, such as port-forwarding, end with `Control+C`.
Cleanup is intentionally split into application cleanup and whole-cluster
cleanup so you can choose what to preserve.

## Important safety notes

- The Keycloak configuration uses development mode and an embedded H2 database.
  It is for this local Mac lab only.
- The Keycloak service is accessed with local port-forwarding. It is not
  intentionally exposed to other computers.
- Never store a real password in `secret-example.yaml` or commit one to Git.
- A Kubernetes Secret is base64-encoded, not encrypted by default.

See [`COMMANDS.md`](COMMANDS.md) for command anatomy and common flags.
