# Kubernetes ImagePullBackOff demo

This lab uses raw Kubernetes manifests and `kubectl` commands to reproduce seven common paths to `ImagePullBackOff`. Run it only in the disposable Minikube profile created below.

## What the lab covers

| Manifest | Failure signal |
| --- | --- |
| `01-missing-tag.yaml` | `manifest unknown` or `not found` |
| `02-registry-authentication.yaml` | `401 Unauthorized` or `pull access denied` |
| `03-registry-rate-limit.yaml` | `429 Too Many Requests` |
| `04-registry-dns.yaml` | `no such host` |
| `05-tls-certificate.yaml` | `x509` certificate error |
| `06-platform-mismatch.yaml` | `no matching manifest` |
| `07-runtime-unpack-failure.yaml` | failed image download or digest verification |

Exact wording can vary with the Kubernetes version and container runtime. The lab was verified with Minikube 1.37.0, Kubernetes 1.34.0, and Docker Engine 28.4.0 on arm64.

## Prerequisites

- Docker
- Minikube
- `kubectl`
- Docker Compose

The registry credentials in this repository are fixed demo credentials. Do not reuse them outside this disposable lab.

## Start the registry fixtures

The authenticated registry provides a real private image for the authentication case. The mock registry returns deterministic 429, platform, and corrupted-image responses.

```bash
docker compose up -d --build
```

Seed the authenticated registry with the valid NGINX image used for recovery:

```bash
docker login localhost:5050 \
  --username demo \
  --password imagepullbackoff

docker pull nginx:1.27-alpine
docker tag nginx:1.27-alpine localhost:5050/private/nginx:1.27-alpine
docker push localhost:5050/private/nginx:1.27-alpine
```

## Start the disposable cluster

The two HTTP registries are deliberately marked insecure for this local profile. The TLS failure uses a separate HTTPS endpoint and is not covered by these flags.

```bash
minikube start -p imagepullbackoff-demo \
  --driver=docker \
  --insecure-registry=host.minikube.internal:5050 \
  --insecure-registry=host.minikube.internal:5001

kubectl config use-context imagepullbackoff-demo
kubectl apply -f manifests/namespace.yaml
```

## Run a case

Apply one failure manifest at a time:

```bash
kubectl apply -f manifests/failures/01-missing-tag.yaml
kubectl get pod missing-tag -n imagepullbackoff-lab
kubectl describe pod missing-tag -n imagepullbackoff-lab
kubectl get events -n imagepullbackoff-lab \
  --field-selector involvedObject.kind=Pod,involvedObject.name=missing-tag \
  --sort-by='.metadata.creationTimestamp'
```

Each article example links to its manifest and identifies the line to change. Reapply the same manifest after making that correction, then use `kubectl get pod` to verify that the Pod reaches `1/1 Running`.

## Authentication-case credentials

After observing the unauthenticated failure, create the pull Secret:

```bash
kubectl create secret docker-registry registry-credentials \
  --docker-server=host.minikube.internal:5050 \
  --docker-username=demo \
  --docker-password=imagepullbackoff \
  -n imagepullbackoff-lab
```

Reapply `02-registry-authentication.yaml` after creating the Secret.

## Clean up

```bash
kubectl delete namespace imagepullbackoff-lab --ignore-not-found
minikube delete -p imagepullbackoff-demo
docker compose down
```
