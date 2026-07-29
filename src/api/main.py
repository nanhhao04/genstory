import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator

from src.api.router import api_router, page_router
from src.database.session import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="GenStory AI API", lifespan=lifespan)

# Instrument and expose Prometheus metrics
Instrumentator().instrument(app).expose(app)

os.makedirs("src/outputs", exist_ok=True)
os.makedirs("src/ui/static", exist_ok=True)

app.mount("/static", StaticFiles(directory="src/ui/static"), name="static")
app.mount("/outputs", StaticFiles(directory="src/outputs"), name="outputs")

app.include_router(api_router)
app.include_router(page_router)
