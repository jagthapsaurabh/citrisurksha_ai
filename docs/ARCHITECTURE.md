# CitriSurksha Architecture

## Components

```text
Farmer Mobile App ── HTTPS ── NGINX / Cloud LB ── Backend API replicas ── Postgres
                                        │                 │
Admin Panel ───────── HTTPS ────────────┘                 ├── Redis cache
                                                          ├── S3/MinIO image storage
                                                          └── AI Inference service replicas
                                                                  │
                                                                  └── GPU training workers + model registry
```

## Runtime flow for pest detection

1. Mobile captures or uploads image.
2. API validates file type/size and stores original image.
3. API creates SHA-256 image key and checks Redis prediction cache.
4. On cache miss, API calls AI inference service.
5. AI returns `pest_id`, name, lifecycle stage, confidence and top-k results.
6. API enriches with pest details: symptoms, prevention, cure, organic and chemical control.
7. API stores detection history and returns farmer-friendly report.

## Scalability design

### Load balancing

- NGINX in this scaffold provides `least_conn` balancing to backend and AI service.
- Production should use AWS ALB/GCP Load Balancer/Nginx Ingress in Kubernetes.
- Run backend stateless replicas; JWT auth means no sticky sessions required.

### Caching

- Redis cache for pest catalogue, individual pest details, blog/calendar content and duplicate image predictions.
- NGINX can cache safe GET endpoints.
- CDN can cache public blog images and advisory content.

### Data storage

- Postgres stores users, pest catalogue, detections, labels, training metadata and jobs.
- S3/MinIO stores raw farmer images, curated training images and model artifacts.
- For 1M+ images, use partitioned metadata tables by dataset version/date.

### AI inference

- Run separate AI inference pods/services from API pods.
- Use GPU only if latency/throughput requires it; optimized CPU inference with ONNX/TensorRT/OpenVINO can be cheaper for moderate traffic.
- Use model versioning and canary deployment: 5% traffic to new model, compare confidence/expert review, then promote.

### AI training

- Training should run as asynchronous jobs on GPU workers, not inside request/response API path.
- Dataset manifest references image URIs and labels; workers stream from S3.
- Use active learning: prioritize low-confidence farmer detections and new pest lifecycle stages for admin/expert labelling.

## Security and safety

- Add HTTPS, rate limiting and WAF rules in production.
- Store passwords with bcrypt/argon2, rotate JWT secret, and use refresh tokens for mobile.
- Farmers should see chemical pesticide advice only with safety note, PPE, label compliance and local regulation filters.
- Admin actions require audit logs.

## Production deployment option

- Kubernetes namespaces: `frontend`, `api`, `ai`, `data`.
- HPA for backend based on CPU/RPS.
- HPA for AI inference based on GPU/CPU utilization and queue latency.
- Redis cluster or managed Redis.
- Managed Postgres with read replicas.
- Object storage with lifecycle rules.
- Observability: Prometheus/Grafana, Loki, OpenTelemetry tracing.
