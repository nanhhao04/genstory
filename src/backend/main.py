from fastapi import FastAPI, HTTPException, Depends, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import os
import io
import requests as http_requests

from src.models.db import get_db, engine, Base
from src.models.genstory_engine import StoryEngine
from src.models.schemas import Chapter, WorldBible

app = FastAPI(title="GenStory AI API")

TTS_API_URL = "https://api.hypereal.cloud/api/v1/audio/generate"
TTS_KEY = os.getenv("TTS_KEY", "")

# Setup database tables on startup (simple version)
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

class StartStoryRequest(BaseModel):
    description: str
    genre: str = "dark_fantasy"
    art_style: str = "anime"
    protagonist_name: str = "Kael"
    protagonist_description: str = ""
    target_chapters: int = 8

class NextChapterRequest(BaseModel):
    story_id: str
    chosen_option_text: str

class TTSRequest(BaseModel):
    text: str

@app.post("/api/stories/start", response_model=dict)
async def start_story(req: StartStoryRequest, db: AsyncSession = Depends(get_db)):
    story_engine = StoryEngine(db=db)
    try:
        chapter = await story_engine.start_story(
            description=req.description,
            genre=req.genre,
            art_style=req.art_style,
            protagonist_name=req.protagonist_name,
            protagonist_description=req.protagonist_description,
            target_chapters=req.target_chapters
        )
        return {
            "story_id": story_engine.session.world_bible.story_id,
            "chapter": chapter.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stories/next", response_model=dict)
async def next_chapter(req: NextChapterRequest, db: AsyncSession = Depends(get_db)):
    story_engine = StoryEngine(db=db)
    raise HTTPException(status_code=501, detail="Load story and session management not yet fully implemented in API")

@app.post("/tts")
async def text_to_speech(req: TTSRequest):
    """Chuyển văn bản thành giọng đọc MP3 qua Hypereal TTS API."""
    if not TTS_KEY:
        raise HTTPException(status_code=500, detail="TTS_KEY chưa được cấu hình trong .env")

    payload = {
        "model": "audio-tts",
        "input": {
            "text": req.text,
            "format": "mp3"
        }
    }
    headers = {
        "Authorization": f"Bearer {TTS_KEY}",
        "Content-Type": "application/json"
    }

    try:
        resp = http_requests.post(TTS_API_URL, json=payload, headers=headers, timeout=30)
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=f"TTS API lỗi: {resp.text[:200]}")
        return StreamingResponse(
            io.BytesIO(resp.content),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=tts_output.mp3"}
        )
    except http_requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Không thể kết nối TTS API: {e}")

@app.get("/")
async def root():
    return {"message": "GenStory API is running"}