from __future__ import annotations

from dataclasses import asdict
import logging
import os
import requests
import uuid
from typing import Callable, Optional

from fpdf import FPDF
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents import ChapterWriterAgent, InteractionManagerAgent, StoryPlannerAgent
from src.agents.langgraph_story_flow import StoryLangGraphOrchestrator
from src.core.guardrails import validate_user_choice_input, validate_user_story_input
from src.database.models import ChapterTable, StoryTable, WorldBibleTable
from src.schemas.story import (
    Chapter,
    Character,
    MangaPage,
    MangaPanel,
    MemoryEntry,
    NextOption,
    StoryBeat,
    StoryCanon,
    StoryOutline,
    StorySession,
    WorldBible,
)


def _world_bible_lore_payload(session: StorySession) -> dict:
    return {
        "tone": session.world_bible.tone,
        "setting": session.world_bible.setting,
        "lore": session.world_bible.lore,
        "opening_hook": session.world_bible.opening_hook,
        "protagonist_sd_anchor": session.world_bible.protagonist.sd_anchor,
        "side_characters": [asdict(item) for item in session.world_bible.side_characters],
        "outline": asdict(session.outline) if session.outline else None,
        "canon": asdict(session.canon),
        "memory": [asdict(item) for item in session.memory],
        "target_chapters": session.world_bible.target_chapters,
    }


class StoryEngine:
    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        self.session: Optional[StorySession] = None
        self.story_planner = StoryPlannerAgent()
        self.chapter_writer = ChapterWriterAgent()
        self.interaction_manager = InteractionManagerAgent()
        self.orchestrator = StoryLangGraphOrchestrator(
            story_planner=self.story_planner,
            chapter_writer=self.chapter_writer,
            interaction_manager=self.interaction_manager,
        )

    async def load_story(self, story_id: str) -> bool:
        if not self.db:
            return False

        result = await self.db.execute(select(WorldBibleTable).where(WorldBibleTable.id == story_id))
        db_bible = result.scalars().first()
        if not db_bible:
            return False

        lore = db_bible.lore or {}
        world_bible = WorldBible(
            story_id=db_bible.id,
            title=db_bible.title,
            genre=db_bible.genre,
            art_style=db_bible.art_style,
            tone=lore.get("tone", "dramatic"),
            setting=lore.get("setting", ""),
            protagonist=Character(
                name=db_bible.protagonist_name,
                role="protagonist",
                appearance=db_bible.protagonist_description,
                sd_anchor=lore.get("protagonist_sd_anchor", ""),
            ),
            side_characters=[
                Character(**item) for item in lore.get("side_characters", []) or []
            ],
            lore=lore.get("lore", ""),
            target_chapters=lore.get("target_chapters", 8),
            opening_hook=lore.get("opening_hook", ""),
        )

        outline = None
        outline_data = lore.get("outline")
        if outline_data:
            outline = StoryOutline(
                premise=outline_data.get("premise", ""),
                opening_hook=outline_data.get("opening_hook", ""),
                ending_vision=outline_data.get("ending_vision", ""),
                progression_notes=outline_data.get("progression_notes", []) or [],
                beats=[
                    StoryBeat(
                        chapter_number=beat.get("chapter_number", idx + 1),
                        title=beat.get("title", f"Chapter {idx + 1}"),
                        objective=beat.get("objective", ""),
                        conflict=beat.get("conflict", ""),
                        reveal=beat.get("reveal", ""),
                        planned_choice_theme=beat.get("planned_choice_theme", ""),
                        must_include=beat.get("must_include", []) or [],
                    )
                    for idx, beat in enumerate(outline_data.get("beats", []) or [])
                ],
            )

        canon_data = lore.get("canon", {}) or {}
        canon = StoryCanon(
            current_location=canon_data.get("current_location", ""),
            active_companions=canon_data.get("active_companions", []) or [],
            inventory=canon_data.get("inventory", []) or [],
            revealed_information=canon_data.get("revealed_information", []) or [],
            unresolved_threads=canon_data.get("unresolved_threads", []) or [],
            relationship_states=canon_data.get("relationship_states", {}) or {},
            latest_status=canon_data.get("latest_status", ""),
        )

        memory = [
            MemoryEntry(
                chapter_number=item.get("chapter_number", idx + 1),
                summary=item.get("summary", ""),
                key_events=item.get("key_events", []) or [],
                chosen_option=item.get("chosen_option", ""),
                canon_snapshot=item.get("canon_snapshot", {}) or {},
            )
            for idx, item in enumerate(lore.get("memory", []) or [])
        ]

        chapter_result = await self.db.execute(
            select(ChapterTable).where(ChapterTable.story_id == story_id).order_by(ChapterTable.chapter_number)
        )
        db_chapters = chapter_result.scalars().all()
        chapters = []
        for item in db_chapters:
            manga_page_data = item.manga_page_data or {}
            chapters.append(
                Chapter(
                    chapter_number=item.chapter_number,
                    title=item.title,
                    choice_that_led_here=item.choice_that_led_here or "",
                    narrative_text=item.narrative_text,
                    manga_page=MangaPage(
                        layout=manga_page_data.get("layout", "2x2"),
                        panels=[
                            MangaPanel(**panel) for panel in manga_page_data.get("panels", []) or []
                        ],
                        dominant_mood=manga_page_data.get("dominant_mood", "dramatic"),
                    ),
                    chapter_ending=item.chapter_ending or "",
                    key_events=item.key_events or [],
                    state_changes=item.state_changes or {},
                    next_options=[NextOption(**opt) for opt in (item.options or [])],
                    image_path=item.image_path,
                    summary=item.summary,
                )
            )

        self.session = StorySession(
            world_bible=world_bible,
            outline=outline,
            canon=canon,
            memory=memory,
            chapters=chapters,
        )
        return True

    async def start_story(
        self,
        description: str,
        genre: str = "dark_fantasy",
        art_style: str = "anime",
        protagonist_name: str = "Kael",
        protagonist_description: str = "",
        target_chapters: int = 8,
        user_id: Optional[str] = None,
        progress_callback: Optional[Callable] = None,
    ) -> Chapter:
        safe_input = validate_user_story_input(
            description=description,
            genre=genre,
            art_style=art_style,
            protagonist_name=protagonist_name,
            protagonist_description=protagonist_description,
            target_chapters=target_chapters,
        )
        graph_state = await self.orchestrator.run_start_story(
            description=safe_input["description"],
            genre=safe_input["genre"],
            art_style=safe_input["art_style"],
            protagonist_name=safe_input["protagonist_name"],
            protagonist_description=safe_input["protagonist_description"],
            target_chapters=safe_input["target_chapters"],
            progress_callback=progress_callback,
        )
        self.session = graph_state["session"]
        chapter = graph_state["chapter"]
        self.session.chapters.append(chapter)

        if self.db:
            await self._save_new_story(user_id=user_id)

        return chapter

    async def next_chapter(self, chosen_option_text: str, progress_callback: Optional[Callable] = None) -> Chapter:
        if not self.session:
            raise RuntimeError("Chua co story session.")

        safe_choice = validate_user_choice_input(chosen_option_text)
        graph_state = await self.orchestrator.run_next_chapter(
            session=self.session,
            chosen_option_text=safe_choice,
            progress_callback=progress_callback,
        )
        self.session = graph_state["session"]
        chapter = graph_state["chapter"]
        self.session.chapters.append(chapter)

        if self.db:
            await self._save_next_chapter(chapter)

        return chapter

    async def _save_new_story(self, user_id: Optional[str] = None) -> None:
        if not self.db or not self.session:
            return

        db_bible = WorldBibleTable(
            id=self.session.world_bible.story_id,
            user_id=user_id,
            title=self.session.world_bible.title,
            genre=self.session.world_bible.genre,
            art_style=self.session.world_bible.art_style,
            protagonist_name=self.session.world_bible.protagonist.name,
            protagonist_description=self.session.world_bible.protagonist.appearance,
            lore=_world_bible_lore_payload(self.session),
        )
        self.db.add(db_bible)

        db_story = StoryTable(
            id=self.session.world_bible.story_id,
            world_bible_id=self.session.world_bible.story_id,
            current_chapter_index=self.session.current_chapter_number,
            target_chapters=self.session.world_bible.target_chapters,
            is_finished=1 if self.session.is_finished else 0,
        )
        self.db.add(db_story)
        await self._save_chapter_to_db(self.session.world_bible.story_id, self.session.latest_chapter)
        await self.db.commit()

    async def _save_next_chapter(self, chapter: Chapter) -> None:
        if not self.db or not self.session:
            return

        await self._save_chapter_to_db(self.session.world_bible.story_id, chapter)
        bible_result = await self.db.execute(
            select(WorldBibleTable).where(WorldBibleTable.id == self.session.world_bible.story_id)
        )
        db_bible = bible_result.scalars().first()
        if db_bible:
            db_bible.lore = _world_bible_lore_payload(self.session)

        story_result = await self.db.execute(
            select(StoryTable).where(StoryTable.id == self.session.world_bible.story_id)
        )
        db_story = story_result.scalars().first()
        if db_story:
            db_story.current_chapter_index = self.session.current_chapter_number
            db_story.target_chapters = self.session.world_bible.target_chapters
            db_story.is_finished = 1 if self.session.is_finished else 0

        await self.db.commit()

    async def _save_chapter_to_db(self, story_id: str, chapter: Optional[Chapter]) -> None:
        if not self.db or not chapter:
            return

        db_chapter = ChapterTable(
            id=str(uuid.uuid4())[:8],
            story_id=story_id,
            chapter_number=chapter.chapter_number,
            title=chapter.title,
            narrative_text=chapter.narrative_text,
            image_path=chapter.image_path,
            summary=chapter.summary,
            choice_that_led_here=chapter.choice_that_led_here,
            chapter_ending=chapter.chapter_ending,
            key_events=chapter.key_events,
            state_changes=chapter.state_changes,
            manga_page_data=asdict(chapter.manga_page) if chapter.manga_page else None,
            options=[asdict(opt) for opt in chapter.next_options],
        )
        self.db.add(db_chapter)
        await self.db.flush()

    @property
    def story_title(self) -> str:
        return self.session.world_bible.title if self.session and self.session.world_bible else ""

    @property
    def is_finished(self) -> bool:
        if not self.session:
            return False
        return self.session.is_finished

    def get_chapter_history(self) -> list[dict]:
        if not self.session or not self.session.chapters:
            return []
        return [
            {"number": chapter.chapter_number, "title": chapter.title, "summary": chapter.summary or ""}
            for chapter in self.session.chapters
        ]

    async def export_to_pdf(self) -> str:
        if not self.session or not self.session.world_bible:
            raise RuntimeError("Khong co du lieu de xuat PDF.")

        bible = self.session.world_bible
        chapters = self.session.chapters or []

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_margins(left=15, top=15, right=15)
        effective_w = 210 - 30

        font_dir = os.path.join(os.path.dirname(__file__), "..", "ui", "static", "fonts")
        os.makedirs(font_dir, exist_ok=True)
        font_path = os.path.join(font_dir, "NotoSans-Regular.ttf")

        is_font_valid = os.path.exists(font_path) and os.path.getsize(font_path) > 100000
        if not is_font_valid:
            urls = [
                "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSans/NotoSans-Regular.ttf",
                "https://github.com/google/fonts/raw/main/ofl/notosans/NotoSans-Regular.ttf",
                "https://raw.githubusercontent.com/openmaptiles/fonts/master/fonts/noto-sans/NotoSans-Regular.ttf",
            ]
            for url in urls:
                try:
                    response = requests.get(url, timeout=20)
                    if response.status_code == 200 and len(response.content) > 100000:
                        with open(font_path, "wb") as handle:
                            handle.write(response.content)
                        is_font_valid = True
                        break
                except Exception as exc:
                    logging.error("Failed to download font from %s: %s", url, exc)

        if is_font_valid:
            pdf.add_font("NotoSans", "", font_path)
            pdf.set_font("NotoSans", size=12)
            font_family = "NotoSans"
        else:
            pdf.set_font("Arial", size=12)
            font_family = "Arial"

        pdf.add_page()
        pdf.set_font(font_family, size=22)
        pdf.multi_cell(effective_w, 12, f"TRUYEN: {self.story_title.upper()}", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font(font_family, size=13)
        pdf.multi_cell(
            effective_w,
            8,
            f"The loai: {bible.genre} | Phong cach: {bible.art_style}",
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.ln(10)
        pdf.set_font(font_family, size=12)
        pdf.multi_cell(effective_w, 8, f"Nhan vat chinh: {bible.protagonist.name}", new_x="LMARGIN", new_y="NEXT")
        pdf.multi_cell(effective_w, 8, f"Mo ta: {bible.protagonist.appearance[:200]}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(10)

        for chapter in chapters:
            pdf.add_page()
            pdf.set_font(font_family, size=16)
            pdf.multi_cell(
                effective_w,
                10,
                f"Chuong {chapter.chapter_number}: {chapter.title}",
                new_x="LMARGIN",
                new_y="NEXT",
            )
            pdf.ln(4)

            if chapter.image_path:
                image_full_path = os.path.join(os.path.dirname(__file__), "..", chapter.image_path)
                if os.path.exists(image_full_path):
                    try:
                        pdf.image(image_full_path, x=15, w=effective_w)
                        pdf.ln(5)
                    except Exception as exc:
                        logging.warning("Failed to add image to PDF: %s", exc)

            pdf.set_font(font_family, size=11)
            pdf.multi_cell(effective_w, 7, chapter.narrative_text, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(8)

            if chapter.chapter_ending:
                pdf.set_font(font_family, size=10)
                pdf.multi_cell(
                    effective_w,
                    6,
                    f"Ket chuong: {chapter.chapter_ending}",
                    new_x="LMARGIN",
                    new_y="NEXT",
                )

        export_dir = os.path.join(os.path.dirname(__file__), "..", "ui", "static", "exports")
        os.makedirs(export_dir, exist_ok=True)
        file_path = os.path.join(export_dir, f"story_{self.session.world_bible.story_id}.pdf")
        pdf.output(file_path)
        return file_path
