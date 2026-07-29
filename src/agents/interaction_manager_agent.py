"""Interaction Manager Agent implementation."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from src.agents.base import BaseStoryAgent
from src.core.guardrails import validate_finalized_chapter
from src.prompts.story_prompts import INTERACTION_MANAGER_SYSTEM, INTERACTION_MANAGER_USER
from src.schemas.story import Chapter, MemoryEntry, NextOption, StoryCanon, StorySession, WorldBible


class InteractionManagerAgent(BaseStoryAgent):
    name = "interaction_manager"

    async def finalize_chapter(self, session: StorySession, chapter: Chapter) -> Chapter:
        beat = None
        if session.outline:
            for item in session.outline.beats:
                if item.chapter_number == chapter.chapter_number:
                    beat = item
                    break

        payload = await self.call_json(
            INTERACTION_MANAGER_SYSTEM,
            INTERACTION_MANAGER_USER.format(
                world_bible_json=self.dump_json(self._world_bible_to_prompt(session.world_bible)),
                outline_json=self.dump_json(asdict(session.outline) if session.outline else {}),
                beat_json=self.dump_json(asdict(beat) if beat else {}),
                canon_json=self.dump_json(asdict(session.canon)),
                memory_json=self.dump_json([asdict(entry) for entry in session.memory]),
                chapter_json=self.dump_json(
                    {
                        "chapter_number": chapter.chapter_number,
                        "title": chapter.title,
                        "choice_that_led_here": chapter.choice_that_led_here,
                        "narrative_text": chapter.narrative_text,
                        "chapter_ending": chapter.chapter_ending,
                        "key_events": chapter.key_events,
                        "state_changes": chapter.state_changes,
                    }
                ),
            ),
            log_name=f"interaction_manager_{chapter.chapter_number}",
            context=f"interaction_manager_{chapter.chapter_number}",
        )

        chapter.next_options = self._parse_options(payload.get("next_options", []) or [])
        chapter.summary = self._format_summary(payload.get("summary", []) or chapter.key_events)
        session.canon = self._merge_canon(
            session.canon, chapter.state_changes, payload.get("canon_update", {}) or {}
        )
        session.memory.append(
            MemoryEntry(
                chapter_number=chapter.chapter_number,
                summary=chapter.summary or "",
                key_events=chapter.key_events,
                chosen_option=chapter.choice_that_led_here,
                canon_snapshot=asdict(session.canon),
            )
        )
        return validate_finalized_chapter(chapter)

    def _parse_options(self, payload: list[dict[str, Any]]) -> list[NextOption]:
        options = []
        for idx, item in enumerate(payload[:4]):
            options.append(
                NextOption(
                    id=item.get("id", chr(65 + idx)),
                    text=item.get("text", f"Lua chon {idx + 1}"),
                    hint=item.get("hint", ""),
                    consequence_type=item.get("consequence_type", "exploration"),
                )
            )
        return options

    def _format_summary(self, lines: list[str]) -> str:
        return "\n".join(f"- {line}" for line in lines if line)

    def _merge_canon(
        self,
        canon: StoryCanon,
        state_changes: dict[str, Any],
        canon_update: dict[str, Any],
    ) -> StoryCanon:
        merged = asdict(canon)

        if state_changes.get("location"):
            merged["current_location"] = state_changes["location"]
        if state_changes.get("companions"):
            merged["active_companions"] = state_changes["companions"]
        if state_changes.get("inventory"):
            merged["inventory"] = state_changes["inventory"]
        if state_changes.get("new_info"):
            merged["revealed_information"] = state_changes["new_info"]
        if state_changes.get("unresolved_threads"):
            merged["unresolved_threads"] = state_changes["unresolved_threads"]
        if state_changes.get("relationship_states"):
            merged["relationship_states"] = state_changes["relationship_states"]
        if state_changes.get("status"):
            merged["latest_status"] = state_changes["status"]

        for key, value in canon_update.items():
            if value not in (None, ""):
                merged[key] = value

        return StoryCanon(
            current_location=merged.get("current_location", ""),
            active_companions=merged.get("active_companions", []) or [],
            inventory=merged.get("inventory", []) or [],
            revealed_information=merged.get("revealed_information", []) or [],
            unresolved_threads=merged.get("unresolved_threads", []) or [],
            relationship_states=merged.get("relationship_states", {}) or {},
            latest_status=merged.get("latest_status", ""),
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
