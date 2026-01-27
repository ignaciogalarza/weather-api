# Skill: Deployment

## Purpose

Deploy the Weather API using Docker containers and Kubernetes orchestration following project standards.

## Triggers

- "Deploy the application"
- "Build Docker image"
- "Deploy to Kubernetes"
- "Update deployment"
- "Scale the service"

## Rules

### Docker Requirements

| Requirement | Standard |
|-------------|----------|
| Base Image | python:3.12-slim |
| Build | Multi-stage for minimal size |
| User | Non-root |
| Health Check | Configured |
| Labels | Version, maintainer |

### Kubernetes Requirements

| Component | Required |
|-----------|----------|
| Deployment | Yes - with replicas >= 2 |
| Service | Yes - NodePort or LoadBalancer |
| ConfigMap | For non-sensitive config |
| Secrets | For sensitive data |
| Resource Limits | CPU and memory defined |
| Probes | Liveness and readiness |

### Health Probes

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Resource Limits

```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "500m"
```

## Examples

### Full Deployment Flow

```bash
# 1. Build Docker image
docker build -t weather-api:v1.0.0 .

# 2. Tag for registry (if using)
docker tag weather-api:v1.0.0 registry.example.com/weather-api:v1.0.0

# 3. Push to registry (if using)
docker push registry.example.com/weather-api:v1.0.0

# 4. Import to k3d (local development)
k3d image import weather-api:v1.0.0 -c weather-cluster

# 5. Apply Kubernetes manifests
kubectl apply -f k8s/deployments/weather-api.yaml
kubectl apply -f k8s/services/weather-api.yaml

# 6. Verify deployment
kubectl rollout status deployment/weather-api

# 7. Check pods
kubectl get pods -l app=weather-api

# 8. Test endpoint
kubectl port-forward svc/weather-api 8080:80 &
curl http://localhost:8080/health
```

### Rolling Update

```bash
# Update image in deployment
kubectl set image deployment/weather-api \
  weather-api=weather-api:v1.1.0

# Watch rollout
kubectl rollout status deployment/weather-api

# Rollback if needed
kubectl rollout undo deployment/weather-api
```

### Scaling

```bash
# Manual scaling
kubectl scale deployment weather-api --replicas=5

# Autoscaling (HPA)
kubectl autoscale deployment weather-api \
  --min=2 --max=10 --cpu-percent=80
```

## Commands Reference

### Docker

```bash
# Build
docker build -t weather-api:latest .

# Run locally
docker run -p 8000:8000 weather-api:latest

# View logs
docker logs <container-id>

# Shell into container
docker exec -it <container-id> /bin/bash
```

### Kubernetes

```bash
# Apply manifests
kubectl apply -f k8s/

# Get resources
kubectl get deployments,pods,services

# Describe for debugging
kubectl describe pod <pod-name>

# View logs
kubectl logs -l app=weather-api --tail=100

# Port forward
kubectl port-forward svc/weather-api 8080:80
```

## Manifest Structure

```
k8s/
├── deployments/
│   └── weather-api.yaml      # Deployment spec
├── services/
│   └── weather-api.yaml      # Service spec
├── configmaps/
│   └── weather-api.yaml      # Configuration (future)
├── secrets/
│   └── weather-api.yaml      # Secrets (future)
└── ingress/
    └── weather-api.yaml      # Ingress rules (future)
```

## Extensions

### Adding Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: weather-api
spec:
  rules:
    - host: weather.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: weather-api
                port:
                  number: 80
```

### Adding HPA

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: weather-api
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: weather-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 80
```
