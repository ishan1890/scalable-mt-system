✅ Scalable Machine Translation System (Use Case 1)
📌 Project Overview

This project implements a scalable, priority-aware Machine Translation (MT) system designed to:

Handle urgent translation requests immediately

Scale automatically with traffic

Minimize GPU cost during idle periods

Provide monitoring, observability, and cost estimation

Be cloud-ready and production-deployable

This is a production-style prototype implemented on a local machine with a lightweight model, while keeping the full architecture ready for large GPU-based deployment.

✅ What We Implemented (Fully Completed)
✅ 1. Priority-Based Request Handling (P0–P3)

Every request contains a priority:

P0 → Critical (highest priority)

P1 → High

P2 → Normal

P3 → Low

Requests are placed into:

asyncio.PriorityQueue()


The worker always processes:

P0 → P1 → P2 → P3


✅ This guarantees urgent requests are processed immediately, even under heavy load.

✅ 2. Asynchronous Background Worker

The system follows:

Client → FastAPI → Priority Queue → Background Worker → Model → Response


API is non-blocking

Worker:

Pulls jobs from the queue

Runs translation

Sends results back via asyncio.Future

This ensures:

High concurrency

No API blocking

Easy horizontal scaling later

✅ 3. Machine Translation Pipeline

Frameworks used:

FastAPI

Transformers

Torch

Model:

MarianMT (~300MB) for development

Translation happens inside:

translate_text()


✅ Model can be swapped with a 60–100GB GPU model without changing architecture.

✅ 4. Dockerized Deployment

The entire system runs in:

Docker container

Enables:

Cloud portability

Kubernetes deployment

Easy CI/CD integration

✅ 5. Monitoring & Observability (Prometheus Ready)

Exposed metrics:

Total requests by priority

Queue waiting time

Processing latency

Active worker count

Accessed via:

GET /metrics


✅ These metrics are directly usable for autoscaling and alerting.

✅ 6. TFLOPS & Cost Estimation (Analytical)

Using these assumptions:

Parameter	Value
Server Compute	90 TFLOPS
Throughput	1000 words/min
GPU Cost	$2/hour

Daily estimates:

Load	Compute Cost	Always-On Cost
10k words/day	~$0.33	$48
100k words/day	~$3.33	$48
1M words/day	~$33.33	$48

✅ This proves why autoscaling is critical for cost savings.

❌ What We Did NOT Implement Fully (And WHY)
❌ 1. 60–100GB Model Deployment
Why NOT implemented locally?

A 60–100GB MT model requires:

Data-center GPUs (A100 / H100)

40–80GB GPU VRAM

High RAM and disk bandwidth

Local machine limitations:
Limitation	Reality
GPU VRAM	Too small
System RAM	Insufficient
Disk IO	Too slow
Power & Cooling	Not suitable

✅ We used a small 300MB model for development
✅ Architecture remains identical for big models
❌ Large model cannot physically run on this system

❌ 2. Real GPU Autoscaling (Cloud Level)

True GPU autoscaling requires:

Kubernetes cluster

GPU node groups

Cluster Autoscaler / Karpenter

Local environment only provides:

One machine

One Docker host

No dynamic GPU creation/removal

✅ We implemented:

Queue

Load metrics

Worker model
❌ We did NOT deploy actual cloud autoscaling because real GPU clusters are required

❌ 3. Real Cloud Billing Integration

True cost tracking requires:

AWS / GCP / Azure billing APIs

Production traffic

Real GPU usage data

✅ We provided accurate analytical estimates
❌ We did NOT connect real billing because this is not a cloud deployment

✅ What We Would Do on a Big GPU Machine / Cloud

If this system is deployed on real infrastructure:

🚀 1. Swap Model with 60–100GB GPU Model

Load model on:

device = "cuda"


Use:

FP16 / BF16

TensorRT / DeepSpeed / vLLM

No architectural change required.

🚀 2. Deploy on Kubernetes with HPA

Deployment + Service

Horizontal Pod Autoscaler:

minReplicas: 1
maxReplicas: 20
scale on CPU + queue depth


GPU nodes auto-created by:

Cluster Autoscaler / Karpenter

✅ This enables:

Zero GPU cost during idle

Instant scaling on traffic spikes

🚀 3. Priority Workers at Scale

Separate worker groups:

mt-worker-critical (P0)

mt-worker-normal (P2/P3)

P0 workers:

Higher pod priority

Higher minimum replicas

✅ Guarantees SLA for urgent jobs

🚀 4. Real Cost & TFLOPS Tracking

Real GPU prices from cloud provider

Cost dashboards per:

100k words

1M words

Dynamic optimization of GPU spend

✅ Code-Level Summary
Component	Purpose
FastAPI	API handling
PriorityQueue	Urgent job ordering
worker_loop()	Background execution
translate_text()	Model inference
Prometheus metrics	Monitoring
Docker	Packaging
Kubernetes (planned)	Autoscaling
✅ Final Conclusion (Submission-Ready)

✅ This project fully demonstrates:

Priority-based request handling

Scalable worker architecture

Containerized ML inference

Monitoring & performance visibility

Cost-aware system design

❌ Full-scale 60–100GB GPU execution and autoscaling are not implemented locally due to hardware and environment limitations, not due to architectural constraints.

✅ The system is cloud-ready and production-deployable without redesign.
