# Command Anatomy and Quick Reference

## kubectl

General shape:

```text
kubectl VERB RESOURCE NAME --namespace NAMESPACE [flags]
```

Examples:

| Command | Meaning |
| --- | --- |
| `kubectl get pods -n hands-on` | List Pods in the `hands-on` namespace. |
| `kubectl describe pod NAME -n hands-on` | Show configuration, state, and recent events. |
| `kubectl logs NAME -n hands-on` | Read the main container's standard output/error. |
| `kubectl apply -f FILE` | Make cluster state match a YAML file. |
| `kubectl delete -f FILE` | Remove the objects declared by a YAML file. |
| `kubectl explain deployment.spec` | Display built-in API field documentation. |

Useful flags:

| Flag | Meaning |
| --- | --- |
| `-n NAME` | Use one namespace. |
| `-A` | Use all namespaces. |
| `-o wide` | Include extra columns. |
| `-o yaml` | Return the complete object as YAML. |
| `-l key=value` | Select objects by label. |
| `-w` | Watch for changes until `Control+C`. |
| `--dry-run=client` | Build/validate locally without sending a create request. |

## Helm

General shape:

```text
helm ACTION RELEASE CHART --namespace NAMESPACE [flags]
```

- A **chart** is the installable package.
- A **release** is one installed copy of a chart.
- A **repository** is a chart catalog.
- A **values file** contains your overrides.

`helm upgrade --install keycloak codecentric/keycloakx` means: upgrade the
release named `keycloak` if it exists; otherwise install it from the
`codecentric/keycloakx` chart.

## Declarative versus imperative

`kubectl create namespace hands-on` is imperative: do this action now.
`kubectl apply -f namespace.yaml` is declarative: make the actual state match
this saved desired state. Saved YAML is easier to review, repeat, and version.

## What happens after kubectl apply

1. `kubectl` reads and validates YAML.
2. It uses the selected kubeconfig context to contact the API server.
3. The API server stores the desired object.
4. Controllers compare desired and actual state.
5. The scheduler assigns new Pods to nodes.
6. The node's kubelet starts the requested containers.
