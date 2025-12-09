"""
Machine Translation API with:
- Priority queue (P0–P3, 0 = highest priority)
- Background worker
- Prometheus metrics

File: app/main.py
"""

import asyncio
import time
from typing import Optional

import torch
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from transformers import MarianMTModel, MarianTokenizer

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# -------------------------------------------------------------------
# FastAPI app
# -------------------------------------------------------------------

app = FastAPI(title="MT System with Priority Queue & Metrics")

# -------------------------------------------------------------------
# Model loading
# -------------------------------------------------------------------

MODEL_PATH = "./models/opus-mt-en-fr"



model: Optional[MarianMTModel] = None
tokenizer: Optional[MarianTokenizer] = None
device = "cpu"

# -------------------------------------------------------------------
# Priority queue & worker
# -------------------------------------------------------------------

# 0 = critical, 1 = high, 2 = normal, 3 = low
MIN_PRIORITY = 0
MAX_PRIORITY = 3

# Async priority queue: lower number -> higher priority
task_queue: "asyncio.PriorityQueue" = asyncio.PriorityQueue()
worker_task: Optional[asyncio.Task] = None


class TranslateRequest(BaseModel):
    text: str
    priority: int = 2  # default normal (P2)


class TranslateResponse(BaseModel):
    original_text: str
    translated_text: str
    priority: int
    processing_time: float
    queued_time: float
    model_loaded: bool


# Each queue item: (priority, created_time, text, future)
# created_time ensures FIFO within same priority level.


# -------------------------------------------------------------------
# Prometheus metrics
# -------------------------------------------------------------------

REQUEST_COUNTER = Counter(
    "mt_requests_total",
    "Total translation requests",
    ["priority"],
)

LATENCY_HISTOGRAM = Histogram(
    "mt_request_latency_seconds",
    "Total end-to-end request latency (enqueue + processing)",
    ["priority"],
)

QUEUE_TIME_HISTOGRAM = Histogram(
    "mt_queue_time_seconds",
    "Time spent waiting in the queue before processing",
    ["priority"],
)

IN_PROGRESS = Counter(
    "mt_requests_in_progress",
    "Requests currently being processed",
    ["priority"],
)


# -------------------------------------------------------------------
# Helper: translation function
# -------------------------------------------------------------------

def translate_text(text: str) -> str:
    if model is None or tokenizer is None:
        raise RuntimeError("Model not loaded")

    inputs = tokenizer([text], return_tensors="pt", padding=True, truncation=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        output_tokens = model.generate(**inputs, max_length=512)

    translated = tokenizer.batch_decode(output_tokens, skip_special_tokens=True)[0]
    return translated


# -------------------------------------------------------------------
# Background worker that consumes the priority queue
# -------------------------------------------------------------------

async def worker_loop():
    print("=" * 60)
    print("🧵 Starting background worker for translation queue")
    print("=" * 60)

    while True:
        try:
            # Wait for next job from queue
            priority, created_at, text, future = await task_queue.get()
            priority_label = str(priority)

            start_proc = time.time()
            queue_time = start_proc - created_at

            print(
                f"[WORKER] Dequeued job | priority={priority} | "
                f"queued_for={queue_time:.3f}s | text='{text[:40]}...'"
            )

            QUEUE_TIME_HISTOGRAM.labels(priority=priority_label).observe(queue_time)
            IN_PROGRESS.labels(priority=priority_label).inc()

            try:
                translated = translate_text(text)
                proc_time = time.time() - start_proc
                result = {
                    "original_text": text,
                    "translated_text": translated,
                    "priority": priority,
                    "processing_time": proc_time,
                    "queued_time": queue_time,
                    "model_loaded": True,
                }
                # Send result back to the waiting request handler
                if not future.cancelled():
                    future.set_result(result)
            except Exception as e:
                if not future.cancelled():
                    future.set_exception(e)
            finally:
                IN_PROGRESS.labels(priority=priority_label).dec()
                task_queue.task_done()

        except asyncio.CancelledError:
            print("[WORKER] Cancellation received, shutting down worker loop")
            break
        except Exception as e:
            print(f"[WORKER] Error in worker loop: {e}")


# -------------------------------------------------------------------
# Startup & shutdown events
# -------------------------------------------------------------------

@app.on_event("startup")
async def startup_event():
    global model, tokenizer, device, worker_task

    print("=" * 60)
    print("🚀 Starting Translation Service with Priority Queue")
    print("=" * 60)
    print(f"📂 Loading model from: {MODEL_PATH}")

    try:
        tokenizer = MarianTokenizer.from_pretrained(MODEL_PATH)
        print("   ✓ Tokenizer loaded")
        model = MarianMTModel.from_pretrained(MODEL_PATH)
        print("   ✓ Model loaded")

        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"   Moving model to: {device}")
        model.to(device)
        print("   ✓ Model ready")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        model = None
        tokenizer = None

    # Start background worker
    worker_task = asyncio.create_task(worker_loop())
    print("   ✓ Worker started")
    print("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    global worker_task
    print("🛑 Shutting down translation service")
    if worker_task:
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass
    print("✓ Shutdown complete")


# -------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "device": device,
        "queue_size": task_queue.qsize(),
    }


@app.post("/translate", response_model=TranslateResponse)
async def translate(req: TranslateRequest):
    if model is None or tokenizer is None:
        raise HTTPException(status_code=500, detail="Model not loaded")

    # Validate priority
    if req.priority < MIN_PRIORITY or req.priority > MAX_PRIORITY:
        raise HTTPException(
            status_code=400,
            detail=f"priority must be between {MIN_PRIORITY} and {MAX_PRIORITY}",
        )

    priority = req.priority
    priority_label = str(priority)

    start_total = time.time()
    created_at = start_total

    # Future to get result back from worker
    loop = asyncio.get_running_loop()
    future: asyncio.Future = loop.create_future()

    # Put job into queue (lower priority number = earlier)
    await task_queue.put((priority, created_at, req.text, future))
    print(
        f"[API] Enqueued job | priority={priority} | "
        f"text='{req.text[:40]}...' | queue_size={task_queue.qsize()}"
    )

    REQUEST_COUNTER.labels(priority=priority_label).inc()

    try:
        result = await future  # wait for worker to finish
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    total_latency = time.time() - start_total
    LATENCY_HISTOGRAM.labels(priority=priority_label).observe(total_latency)

    return TranslateResponse(**result)


@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint."""
    data = generate_latest()
    return PlainTextResponse(data.decode("utf-8"), media_type=CONTENT_TYPE_LATEST)
