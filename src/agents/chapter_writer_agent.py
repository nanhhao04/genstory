"""Chapter Writer Agent implementation."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from src.agents.base import BaseStoryAgent
from src.core.guardrails import validate_chapter_output
from src.prompts.story_prompts import CHAPTER_WRITER_SYSTEM, CHAPTER_WRITER_USER
from src.schemas.story import (
    Chapter,
    MangaPage,
    MangaPanel,
    MemoryEntry,
    StoryBeat,
    StorySession,
    WorldBible,
)
from src.services.memory_service import build_writer_memory_payload, select_relevant_memories


class ChapterWriterAgent(BaseStoryAgent):
    name = "chapter_writer"

    async def write_chapter(
        self,
        session: StorySession,
        chosen_option: str = "",
        retrieved_memories: list[MemoryEntry] | None = None,
    ) -> Chapter:
        next_num = session.current_chapter_number + 1
        beat = self._get_current_beat(session, next_num)
        relevant_memories = (
            retrieved_memories
            if retrieved_memories is not None
            else select_relevant_memories(session, beat)
        )

        last_chapter_text = "(Chua co - day la chuong 1)"
        if session.latest_chapter:
            last = session.latest_chapter
            last_chapter_text = (
                f"Chuong {last.chapter_number} - {last.title}\n"
                f"{last.narrative_text}\n"
                f"Ket chuong: {last.chapter_ending}"
            )

        payload = await self.call_json(
            CHAPTER_WRITER_SYSTEM,
            CHAPTER_WRITER_USER.format(
                next_num=next_num,
                world_bible_json=self.dump_json(self._world_bible_to_prompt(session.world_bible)),
                outline_json=self.dump_json(asdict(session.outline) if session.outline else {}),
                beat_json=self.dump_json(asdict(beat) if beat else {}),
                canon_json=self.dump_json(asdict(session.canon)),
                memory_json=self.dump_json(build_writer_memory_payload(session, relevant_memories)),
                last_chapter_text=last_chapter_text,
                chosen_option=chosen_option
                or session.world_bible.opening_hook
                or "Bat dau cau chuyen",
            ),
            log_name=f"chapter_writer_{next_num}",
            context=f"chapter_writer_{next_num}",
        )

        return validate_chapter_output(
            Chapter(
                chapter_number=next_num,
                title=payload.get("chapter_title", f"Chuong {next_num}"),
                choice_that_led_here=chosen_option,
                narrative_text=payload.get("narrative_text", ""),
                manga_page=self._parse_manga_page(payload.get("manga_page", {})),
                chapter_ending=payload.get("chapter_ending", ""),
                key_events=payload.get("key_events", []) or [],
                state_changes=payload.get("state_changes", {}) or {},
                next_options=[],
            )
        )

    def _get_current_beat(self, session: StorySession, chapter_number: int) -> StoryBeat | None:
        if not session.outline:
            return None
        for beat in session.outline.beats:
            if beat.chapter_number == chapter_number:
                return beat
        return None

    def _parse_manga_page(self, payload: dict[str, Any]) -> MangaPage:
        return MangaPage(
            layout=payload.get("layout", "2x2"),
            panels=[
                MangaPanel(
                    position=item.get("position", ""),
                    scene=item.get("scene", ""),
                    focus=item.get("focus", ""),
                    mood=item.get("mood", ""),
                )
                for item in payload.get("panels", []) or []
            ],
            dominant_mood=payload.get("dominant_mood", "dramatic"),
        )

    def _world_bible_to_prompt(self, world_bible: WorldBible) -> dict[str, Any]:
        return {
            "story_id": world_bible.story_id,
            "title": world_bible.title,
            "genre": world_bible.genre,
            "art_style": world_bible.art_style,
            "tone": world_bible.tone,
            "setting": world_bible.setting,
            "lore": world_bible.lore,
            "opening_hook": world_bible.opening_hook,
            "protagonist": asdict(world_bible.protagonist),
            "side_characters": [asdict(item) for item in world_bible.side_characters],
        }
