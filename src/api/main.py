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

try:
    os.makedirs("src/outputs", exist_ok=True)
    os.makedirs("src/ui/static", exist_ok=True)
except Exception:
    pass

if os.path.exists("src/ui/static"):
    app.mount("/static", StaticFiles(directory="src/ui/static"), name="static")

if os.path.exists("src/outputs"):
    app.mount("/outputs", StaticFiles(directory="src/outputs"), name="outputs")

app.include_router(api_router)
app.include_router(page_router)
