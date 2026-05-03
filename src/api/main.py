from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import os

from src.database.session import engine, Base
from src.api.endpoints import router as api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: setup database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="GenStory AI API", lifespan=lifespan)

# Setup templates and static files
templates = Jinja2Templates(directory="src/ui/templates")

# Ensure directories exist
os.makedirs("src/outputs", exist_ok=True)
os.makedirs("src/ui/static", exist_ok=True)

app.mount("/static", StaticFiles(directory="src/ui/static"), name="static")
app.mount("/outputs", StaticFiles(directory="src/outputs"), name="outputs")

# Mount API Endpoints
app.include_router(api_router)

# --- Page Routes ---

@app.get("/auth", response_class=HTMLResponse)
async def auth_page(request: Request):
    return templates.TemplateResponse(request=request, name="auth.html", context={})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html", context={})

@app.get("/story/new", response_class=HTMLResponse)
async def story_setup_page(request: Request):
    return templates.TemplateResponse(request=request, name="setup.html", context={})

@app.get("/story/{story_id}", response_class=HTMLResponse)
async def story_reader_page(request: Request, story_id: str):
    return templates.TemplateResponse(request=request, name="reader.html", context={"story_id": story_id})

@app.get("/")
async def root():
    return RedirectResponse(url="/auth")
