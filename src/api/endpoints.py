from fastapi import APIRouter, HTTPException, Depends, Response, Request
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import os
import io
import uuid
import logging
import requests as http_requests
import httpx
import asyncio
from jose import jwt

from src.database.session import get_db
from src.services.story_engine import StoryEngine
from src.schemas.story import Chapter, WorldBible
from src.database.models import UserTable, WorldBibleTable, ChapterTable
from src.core.auth import get_password_hash, verify_password, create_access_token, ALGORITHM, SECRET_KEY
from fastapi.security import OAuth2PasswordBearer

router = APIRouter(prefix="/api")

# --- Security ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    
    result = await db.execute(select(UserTable).where(UserTable.username == username))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    return user

# --- Auth Schemas ---
from pydantic import BaseModel, Field, field_validator

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=6)
    email: str
    @field_validator("email")
    @classmethod
    def email_must_be_gmail(cls, v):
        if not v.endswith("@gmail.com"):
            raise ValueError("Email must be a @gmail.com address")
        return v

class StoryStartRequest(BaseModel):
    description: str
    genre: str = "dark_fantasy"
    art_style: str = "anime"
    protagonist_name: str = "Kael"
    protagonist_description: str = ""
    target_chapters: int = 8

class StoryNextRequest(BaseModel):
    story_id: str
    chosen_option_text: str

class TTSRequest(BaseModel):
    text: str

# --- Endpoints ---

@router.post("/auth/register")
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(UserTable).where(UserTable.username == user_data.username))
    if res.scalars().first():
        raise HTTPException(status_code=400, detail="Username already registered")
    
    new_user = UserTable(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password)
    )
    db.add(new_user)
    await db.commit()
    return {"message": "User created successfully"}

@router.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(UserTable).where(UserTable.username == form_data.username))
    user = res.scalars().first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me")
async def read_users_me(current_user: UserTable = Depends(get_current_user)):
    return {"username": current_user.username, "email": current_user.email}

@router.post("/stories/start")
async def start_story(req: StoryStartRequest, current_user: UserTable = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    engine = StoryEngine(db=db)
    chapter = await engine.start_story(
        description=req.description,
        genre=req.genre,
        art_style=req.art_style,
        protagonist_name=req.protagonist_name,
        protagonist_description=req.protagonist_description,
        target_chapters=req.target_chapters,
        user_id=current_user.id
    )
    return {"story_id": engine.session.world_bible.story_id, "chapter": chapter}

@router.post("/stories/next")
async def next_chapter(req: StoryNextRequest, current_user: UserTable = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    engine = StoryEngine(db=db)
    if not await engine.load_story(req.story_id):
        raise HTTPException(status_code=404, detail="Story not found")
    
    chapter = await engine.next_chapter(req.chosen_option_text)
    return {"chapter": chapter}

@router.get("/stories/{story_id}")
async def get_story(story_id: str, current_user: UserTable = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    engine = StoryEngine(db=db)
    if not await engine.load_story(story_id):
        raise HTTPException(status_code=404, detail="Story not found")
    return {"bible": engine.session.world_bible, "chapters": engine.session.chapters}

@router.get("/stories")
async def list_my_stories(current_user: UserTable = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(WorldBibleTable).where(WorldBibleTable.user_id == current_user.id))
    stories = res.scalars().all()
    return [{"id": s.id, "title": s.title, "genre": s.genre, "created_at": s.created_at} for s in stories]

@router.get("/stories/{story_id}/pdf")
async def export_pdf(story_id: str, current_user: UserTable = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from fastapi.responses import FileResponse
    engine = StoryEngine(db=db)
    if not await engine.load_story(story_id):
        raise HTTPException(status_code=404, detail="Story not found")
    try:
        pdf_path = await engine.export_to_pdf()
        return FileResponse(path=pdf_path, filename=f"GenStory_{story_id}.pdf", media_type="application/pdf")
    except Exception as e:
        logging.error(f"Error exporting PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tts")
async def text_to_speech(req: TTSRequest, current_user: UserTable = Depends(get_current_user)):
    TTS_API_URL = os.getenv("TTS_API_URL", "https://api.fpt.ai/hmi/tts/v5")
    TTS_KEY = os.getenv("FPT_API_KEY", "")
    if not TTS_KEY:
        raise HTTPException(status_code=500, detail="FPT_API_KEY chưa được cấu hình")

    headers = {"api-key": TTS_KEY, "speed": "", "voice": "banmai"}
    
    async with httpx.AsyncClient() as client:
        try:
            # Step 1: Request TTS generation
            resp = await client.post(TTS_API_URL, data=req.text.encode('utf-8'), headers=headers, timeout=30)
            if resp.status_code != 200:
                logging.error(f"FPT.AI POST Error: {resp.status_code} - {resp.text}")
                raise HTTPException(status_code=resp.status_code, detail="Lỗi gửi yêu cầu đến FPT.AI")
                
            data = resp.json()
            audio_url = data.get("async")
            if not audio_url:
                raise HTTPException(status_code=500, detail="Không tìm thấy URL âm thanh từ FPT.AI")

            # Step 2: Poll for the audio file (FPT.AI needs time to generate)
            max_retries = 30
            audio_content = None
            for i in range(max_retries):
                audio_resp = await client.get(audio_url, timeout=10)
                if audio_resp.status_code == 200:
                    audio_content = audio_resp.content
                    break
                elif audio_resp.status_code == 404:
                    await asyncio.sleep(1.5) # Wait a bit longer
                else:
                    logging.error(f"FPT.AI GET Error: {audio_resp.status_code}")
                    raise HTTPException(status_code=audio_resp.status_code, detail="Lỗi tải file âm thanh")
            
            if not audio_content:
                raise HTTPException(status_code=408, detail="FPT.AI xử lý quá lâu, vui lòng thử lại sau giây lát.")

            return StreamingResponse(io.BytesIO(audio_content), media_type="audio/mpeg")
            
        except httpx.TimeoutException:
            raise HTTPException(status_code=408, detail="Yêu cầu đến FPT.AI bị quá hạn")
        except Exception as e:
            logging.error(f"TTS Unhandled Error: {e}")
            raise HTTPException(status_code=500, detail=f"Lỗi hệ thống TTS: {str(e)}")
