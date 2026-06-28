import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.api.schemas.stories import StoryNextRequest, StoryStartRequest
from src.core.guardrails import GuardrailViolation
from src.database.models import UserTable, WorldBibleTable
from src.database.session import get_db
from src.services.story_engine import StoryEngine

router = APIRouter(prefix="/stories", tags=["stories"])


@router.post("/start")
async def start_story(
    req: StoryStartRequest,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    engine = StoryEngine(db=db)
    try:
        chapter = await engine.start_story(
            description=req.description,
            genre=req.genre,
            art_style=req.art_style,
            protagonist_name=req.protagonist_name,
            protagonist_description=req.protagonist_description,
            target_chapters=req.target_chapters,
            user_id=current_user.id,
        )
        return {"story_id": engine.session.world_bible.story_id, "chapter": chapter}
    except GuardrailViolation as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/next")
async def next_chapter(
    req: StoryNextRequest,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    engine = StoryEngine(db=db)
    if not await engine.load_story(req.story_id):
        raise HTTPException(status_code=404, detail="Story not found")

    try:
        chapter = await engine.next_chapter(req.chosen_option_text)
        return {"chapter": chapter}
    except GuardrailViolation as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{story_id}")
async def get_story(
    story_id: str,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    engine = StoryEngine(db=db)
    if not await engine.load_story(story_id):
        raise HTTPException(status_code=404, detail="Story not found")
    return {"bible": engine.session.world_bible, "chapters": engine.session.chapters}


@router.get("")
async def list_my_stories(
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(WorldBibleTable).where(WorldBibleTable.user_id == current_user.id))
    stories = result.scalars().all()
    return [{"id": story.id, "title": story.title, "genre": story.genre, "created_at": story.created_at} for story in stories]


@router.get("/{story_id}/pdf")
async def export_pdf(
    story_id: str,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    engine = StoryEngine(db=db)
    if not await engine.load_story(story_id):
        raise HTTPException(status_code=404, detail="Story not found")

    try:
        pdf_path = await engine.export_to_pdf()
        return FileResponse(path=pdf_path, filename=f"GenStory_{story_id}.pdf", media_type="application/pdf")
    except Exception as exc:
        logging.error("Error exporting PDF: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
