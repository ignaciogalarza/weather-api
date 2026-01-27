# Deployment Guide

## Docker

### Build Image

```bash
docker build -t weather-api:latest .
```

### Run Container

```bash
docker run -p 8000:8000 weather-api:latest
```

### Test

```bash
curl http://localhost:8000/health
curl http://localhost:8000/forecast/Paris
```

## Kubernetes

### Prerequisites

- kubectl configured
- k3d cluster running (or any Kubernetes cluster)

### Deploy

1. **Import image to k3d** (if using k3d)
   ```bash
   k3d image import weather-api:latest -c weather-cluster
   ```

2. **Apply manifests**
   ```bash
   kubectl apply -f k8s/deployments/weather-api.yaml
   kubectl apply -f k8s/services/weather-api.yaml
   ```

3. **Verify deployment**
   ```bash
   kubectl get pods -l app=weather-api
   kubectl get svc weather-api
   ```

### Access the API

**Option 1: Port Forward**
```bash
kubectl port-forward svc/weather-api 8080:80
curl http://localhost:8080/forecast/Tokyo
```

**Option 2: NodePort** (if cluster supports it)
```bash
curl http://<node-ip>:30080/forecast/Tokyo
```

## Configuration

### Resource Limits

The deployment sets these resource limits:

| Resource | Request | Limit |
|----------|---------|-------|
| Memory | 128Mi | 256Mi |
| CPU | 100m | 500m |

### Health Probes

| Probe | Path | Initial Delay | Period |
|-------|------|---------------|--------|
| Liveness | /health | 10s | 10s |
| Readiness | /health | 5s | 5s |

### Scaling

```bash
# Scale to 3 replicas
kubectl scale deployment weather-api --replicas=3

# Check status
kubectl get pods -l app=weather-api
```

## Troubleshooting

### Check Logs
```bash
kubectl logs -l app=weather-api --tail=100
```

### Check Pod Status
```bash
kubectl describe pod -l app=weather-api
```

### Restart Deployment
```bash
kubectl rollout restart deployment/weather-api
```
