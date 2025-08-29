# Kubernetes Manifests (Kustomize)

This directory contains a Kustomize base and overlays for deploying the mcp-outline service to Kubernetes.

## Structure

- base/: Common resources shared by all environments
  - deployment.yaml: App Deployment (container listens on 3001)
  - service.yaml: ClusterIP Service on port 80 -> 3001
  - ingress.yaml: Ingress with path "/" and default host "mcp-outline.localtest.me"
  - kustomization.yaml: Assembles the above
- overlay/dev/: Example development overlay
  - kustomization.yaml: Sets namespace, image tag override, and ingress host/class

## Prerequisites

- Kubernetes cluster with an Ingress controller (e.g., NGINX Ingress)
- kubectl v1.14+ (with built-in Kustomize)
- The container image mcp-outline:latest available in your cluster nodes or in a registry your cluster can pull from

## Quick start

Apply the dev overlay:

```bash
kubectl apply -k manifests/overlay/dev
```

Get resources:

```bash
kubectl -n mcp-outline-dev get all,ingress
```

Port-forward (if you don't have an Ingress):

```bash
kubectl -n mcp-outline-dev port-forward svc/mcp-outline 8080:80
# Then access http://localhost:8080/
```

If using an Ingress controller and *.localtest.me (which resolves to 127.0.0.1), you can reach:

- http://mcp-outline.localtest.me/

## Notes

- The server can operate with SSE transport (default in manifests). Adjust MCP_TRANSPORT env if you prefer stdio.
- Resource requests/limits are conservative; tune for your workload.
- The container runs as a non-root user (UID/GID 1000), aligned with the Dockerfile.
