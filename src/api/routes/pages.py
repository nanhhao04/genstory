import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["pages"])

# Absolute path resolution for Jinja2 templates in serverless environment
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATES_DIR = os.path.join(BASE_DIR, "ui", "templates")

templates = Jinja2Templates(directory=TEMPLATES_DIR)


@router.get("/auth", response_class=HTMLResponse)
async def auth_page(request: Request):
    return templates.TemplateResponse(request=request, name="auth.html", context={})


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html", context={})


@router.get("/story/new", response_class=HTMLResponse)
async def story_setup_page(request: Request):
    return templates.TemplateResponse(request=request, name="setup.html", context={})


@router.get("/story/{story_id}", response_class=HTMLResponse)
async def story_reader_page(request: Request, story_id: str):
    return templates.TemplateResponse(
        request=request, name="reader.html", context={"story_id": story_id}
    )


@router.get("/")
async def root():
    return RedirectResponse(url="/auth")
