import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator

from src.api.router import api_router, page_router
from src.database.session import Base, engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}")
    yield


app = FastAPI(title="GenStory AI API", lifespan=lifespan)

# Instrument and expose Prometheus metrics
try:
    Instrumentator().instrument(app).expose(app)
except Exception as e:
    logger.warning(f"Prometheus instrumentation warning: {e}")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "ui", "static")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")

try:
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    os.makedirs(STATIC_DIR, exist_ok=True)
except Exception:
    pass

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if os.path.exists(OUTPUTS_DIR):
    app.mount("/outputs", StaticFiles(directory=OUTPUTS_DIR), name="outputs")

app.include_router(api_router)
app.include_router(page_router)
