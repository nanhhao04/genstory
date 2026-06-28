from prometheus_client import Histogram

# Custom metrics for tracing backend performance

LLM_GENERATION_DURATION = Histogram(
    "llm_generation_duration_seconds",
    "Time spent generating content with LLM",
    labelnames=["provider", "status", "agent_name", "task_name"],
    buckets=(0.1, 0.5, 1.0, 2.0, 3.0, 5.0, 7.5, 10.0, 15.0, 20.0, 30.0, float("inf")),
)

TTS_GENERATION_DURATION = Histogram(
    "tts_generation_duration_seconds",
    "Time spent generating TTS audio using FPT.AI",
    labelnames=["status"],
    buckets=(0.5, 1.0, 2.0, 4.0, 6.0, 8.0, 10.0, 15.0, 20.0, 30.0, 45.0, 60.0, float("inf")),
)

IMAGE_GENERATION_DURATION = Histogram(
    "image_generation_duration_seconds",
    "Time spent generating manga page images via HF",
    labelnames=["status"],
    buckets=(0.5, 1.0, 2.0, 4.0, 6.0, 8.0, 10.0, 15.0, 20.0, 30.0, float("inf")),
)
