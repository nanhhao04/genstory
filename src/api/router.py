from fastapi import APIRouter

from src.api.routes.auth import router as auth_router
from src.api.routes.pages import router as pages_router
from src.api.routes.stories import router as stories_router
from src.api.routes.tts import router as tts_router

api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(stories_router)
api_router.include_router(tts_router)

page_router = APIRouter()
page_router.include_router(pages_router)
