1. Overview

This project implements a production-style prototype of a scalable Machine Translation (MT) system with:

Priority-based request handling (P0–P3)

Background worker-based processing

Prometheus-compatible monitoring

Containerized deployment with Docker

The system is designed to meet the requirements of Use Case 1: Scalable Machine Translation System, while acknowledging the practical limitations of running large GPU workloads on a local development machine.

2. Mapping to Original Requirements
Requirement	Status
Priority handling (urgent requests)	✅ Fully Implemented
Asynchronous processing with workers	✅ Implemented
Monitoring & metrics	✅ Implemented
Containerization	✅ Implemented
Model size 60–100GB	⚠️ Simulated with smaller model
Throughput: 1,000 words/min	⚠️ Analytical validation
Autoscaling (GPU + workers)	⚠️ Design-level
Cost & TFLOPS estimation	✅ Analytical
3. Why the System Is Not Fully Implemented at Production Scale
3.1 Large Model Size vs Local Hardware

The original requirement specifies a 60–100GB Machine Translation model, which typically requires:

High-end data-center GPUs (A100/H100 class)

Large GPU VRAM (40–80GB+)

High system RAM and storage throughput

On a typical developer machine:

GPU VRAM is insufficient

System memory and disk I/O are limited

Loading such a model is not feasible

✅ What we did instead:

Used a lightweight Marian MT model (~300MB) for local development.

Kept the architecture model-agnostic, so a 60–100GB model can be plugged in directly on production GPU nodes.

✅ Architecture is production-ready
❌ Full-scale model is not loaded due to hardware constraints

3.2 No Real GPU Cluster or Node Autoscaling Locally

The use case assumes:

Multiple GPU nodes

Automatic GPU scale-up and scale-down

Cloud-based infrastructure (EKS/GKE/AKS)

Locally:

Docker runs on a single node

No real Kubernetes cluster

No GPU node autoscaler

✅ What we implemented:

Priority-based request queue

Background worker execution

Prometheus metrics for:

Request volume

Latency

Queue time

Containerized service ready for orchestration

⚠️ Autoscaling is designed but not executed on real GPU infrastructure.

3.3 Performance & Throughput Validation

Requirements include:

1,000 words/min/server (90 TFLOPS)

10,000 words translated within 12 minutes

Up to 1M words/day

On local systems:

CPU-based inference is slow

Large-scale stress testing is impractical

Network, disk, and memory are limited

✅ What is available:

Asynchronous pipeline

Non-blocking API

Queue-based backpressure control

Analytical throughput validation

⚠️ Real production benchmarks are not measured locally.

3.4 Cloud Cost & TFLOPS Estimation

Live cloud billing requires:

Real GPU instances

Cloud provider pricing

Long-running production workloads

✅ Instead, we use analytical assumptions:

1 server = 90 TFLOPS (FP32)

Effective utilization ≈ 50%

1,000 words/min ≈ 60,000 words/hour

Example GPU cost ≈ $2/hour

From this, daily costs are extrapolated for:

10k words/day

100k words/day

1M words/day

⚠️ These are theoretical estimates, not live cloud bills.

4. How Priority Requests Are Handled

Each request includes a priority value:

P0 = Critical

P1 = High

P2 = Normal

P3 = Low

Requests are placed into an asyncio.PriorityQueue

Background workers always dequeue the lowest priority number first

Result:

P0 requests always preempt P2/P3

Urgent translations are handled immediately even under load

This directly satisfies:

“If there is a priority request which needs to be resolved immediately, how will your system handle it?”

5. Production Deployment on Big Machines (Future State)

If deployed on real cloud infrastructure, the system would evolve as follows:

5.1 Large GPU Model Deployment

Replace lightweight model with 60–100GB MT model

Load on GPU (device = cuda)

Enable:

Mixed precision (FP16/BF16)

Optimized inference engines (TensorRT, vLLM, DeepSpeed)

5.2 Kubernetes-Based Autoscaling

Deploy as Kubernetes Deployment

Add HorizontalPodAutoscaler (HPA):

Scale based on CPU and/or queue depth

Enable GPU node autoscaling via:

Cluster Autoscaler / Karpenter

GPU nodes scale down to zero during idle periods

✅ This satisfies both:

Automatic scaling by load

Cost optimization during idle time

5.3 Priority Handling at Scale

Separate worker groups:

High-priority workers (P0/P1)

Normal workers (P2/P3)

Assign higher pod priority and minimum replicas for P0 workers

Guarantees SLA for urgent translations

5.4 Monitoring & Alerting

Using Prometheus + Grafana:

Monitor:

Queue depth

Latency by priority

Worker utilization

GPU utilization

Alert on:

P0 latency breaches

Queue backlog growth

GPU under/over-utilization

5.5 Real Cloud Cost Tracking

Replace analytical TFLOPS math with:

Actual cloud billing data

Per-SKU GPU cost

Cost per 100k translated words

Visual dashboards for real-time cost optimization

6. Final Summary

This project delivers a fully functional, production-grade prototype for:

Priority-based Machine Translation

Background worker execution

Monitoring and observability

Containerized deployment

Due to local hardware and environment limits, the following are implemented at design level rather than full production scale:

60–100GB model deployment

Real GPU autoscaling

Live cloud billing-based cost tracking

However, the core architecture is production-ready and cloud-deployable without redesign.




1️⃣ TFLOPS & Cost Estimation Table
Assumptions (state these clearly in your DESIGN.md)

Throughput per server:

1,000 words/minute ⇒

1,000 × 60 = 60,000 words/hour

Server compute:

Peak: 90 TFLOPS (FP32)

Effective utilization: 50% under load ⇒ treat as 45 TFLOP-hours consumed per hour at full throughput.

Example GPU cost:

$2.00 per GPU-hour (just an assumption; replace with real cloud pricing later).

Scenarios:

10k words/day

100k words/day

1M words/day

“Compute-only cost” = GPU used exactly for the loaded hours

“Always-on cost” = one GPU running 24/7, regardless of load

Step-by-step formulas

For each scenario:

Required full-load hours/day

hours
=
words_per_day
60,000
hours=
60,000
words_per_day
	​


TFLOP-hours/day

TFLOP-hours
=
hours
×
45
TFLOP-hours=hours×45

Compute-only cost/day

compute_cost
=
hours
×
$
2
compute_cost=hours×$2

Always-on cost/day

always_on_cost
=
24
×
$
2
=
$
48
always_on_cost=24×$2=$48
Table
### TFLOPS & Cost Estimates (Per Day, Per 1× 90-TFLOPS Server)

| Scenario           | Words / Day | Full-Load Hours / Day | TFLOP-Hours / Day | Compute-Only Cost / Day* | Always-On Cost / Day** |
|--------------------|------------:|----------------------:|-------------------:|--------------------------:|------------------------:|
| Low load           |     10,000  |       0.17 h (~1/6)   |        7.5         |       ~$0.33              |        ~$48             |
| Medium load        |    100,000  |       1.67 h (10/6)   |       75           |       ~$3.33              |        ~$48             |
| High load          |  1,000,000  |      16.67 h (100/6)  |      750           |      ~$33.33              |        ~$48             |

\* Compute-only cost assumes GPU is powered only for the required full-load hours.  
\** Always-on cost assumes a single GPU node running 24 hours/day at $2.00/hr.

How to interpret (what you can say)

At low volumes (10k/day), GPU is massively underutilized if always on:

You pay $48/day, but only need 0.17 hours of compute (≈$0.33 of “real” work).

At medium load (100k/day), utilization is still low:

Need ~1.67 hours/day (≈$3.33), still far from $48 always-on.

At high load (1M/day):

Need ~16.67 hours/day (≈$33.33), which is much closer to full-time usage.

This supports the design decision:

Aggressive autoscaling (scale to zero) for low/medium loads.

Keep some baseline capacity only if high sustained traffic.

2️⃣ Kubernetes + HPA YAML Sample

Here’s a simple but realistic Kubernetes setup:

Deployment for the MT app

Service to expose it

HorizontalPodAutoscaler (CPU-based example)

Comment where you’d plug in queue-depth/custom metrics

You can put this in k8s/mt-system.yaml for example.

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mt-system
  labels:
    app: mt-system
spec:
  replicas: 1   # will be managed by HPA
  selector:
    matchLabels:
      app: mt-system
  template:
    metadata:
      labels:
        app: mt-system
    spec:
      containers:
        - name: mt-system
          image: your-registry/mt-system:latest
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8000
          env:
            - name: PYTHONUNBUFFERED
              value: "1"
            # Example: toggle GPU if available
            - name: TORCH_DEVICE
              value: "cuda"   # or "cpu" for non-GPU cluster
          resources:
            requests:
              cpu: "500m"
              memory: "1Gi"
            limits:
              cpu: "1"
              memory: "2Gi"
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 5
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: mt-system
  labels:
    app: mt-system
spec:
  type: ClusterIP
  selector:
    app: mt-system
  ports:
    - name: http
      port: 80
      targetPort: 8000
---
# Simple CPU-based HPA example
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mt-system-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mt-system
  minReplicas: 1          # keep at least one pod for P0 requests
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70   # target 70% CPU usage