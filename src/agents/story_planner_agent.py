"""Story Planner Agent implementation."""

from __future__ import annotations

import uuid

from src.agents.base import BaseStoryAgent
from src.core.guardrails import validate_story_session
from src.prompts.story_prompts import STORY_PLANNER_SYSTEM, STORY_PLANNER_USER
from src.schemas.story import (
    Character,
    StoryBeat,
    StoryCanon,
    StoryOutline,
    StorySession,
    WorldBible,
)


class StoryPlannerAgent(BaseStoryAgent):
    name = "story_planner"

    async def plan_story(
        self,
        *,
        description: str,
        genre: str,
        art_style: str,
        protagonist_name: str,
        protagonist_description: str,
        target_chapters: int,
    ) -> StorySession:
        payload = await self.call_json(
            STORY_PLANNER_SYSTEM,
            STORY_PLANNER_USER.format(
                description=description,
                genre=genre,
                art_style=art_style,
                protagonist_name=protagonist_name,
                protagonist_description=protagonist_description or "Tu do sang tao ngoai hinh",
                target_chapters=target_chapters,
            ),
            log_name="story_planner",
            context="story_planner",
        )

        world_data = payload.get("world_bible", {})
        outline_data = payload.get("outline", {})
        canon_data = payload.get("initial_canon", {})
        story_id = str(uuid.uuid4())[:8]

        world_bible = WorldBible(
            story_id=story_id,
            title=world_data.get("title", "Khong ten"),
            genre=genre,
            art_style=art_style,
            tone=world_data.get("tone", "dramatic"),
            setting=world_data.get("setting", ""),
            protagonist=Character(
                name=world_data.get("protagonist", {}).get("name", protagonist_name),
                role="protagonist",
                appearance=world_data.get("protagonist", {}).get(
                    "appearance", protagonist_description or ""
                ),
                sd_anchor=world_data.get("protagonist", {}).get("sd_anchor", ""),
            ),
            side_characters=[
                Character(
                    name=item.get("name", ""),
                    role=item.get("role", ""),
                    appearance=item.get("appearance", ""),
                    sd_anchor=item.get("sd_anchor", ""),
                )
                for item in world_data.get("side_characters", [])
            ],
            lore=world_data.get("lore", ""),
            target_chapters=target_chapters,
            opening_hook=world_data.get("opening_hook", ""),
        )

        outline = StoryOutline(
            premise=outline_data.get("premise", description),
            opening_hook=outline_data.get("opening_hook", world_bible.opening_hook),
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
                for idx, beat in enumerate(outline_data.get("beats", []))
            ],
        )

        canon = StoryCanon(
            current_location=canon_data.get("current_location", ""),
            active_companions=canon_data.get("active_companions", []) or [],
            inventory=canon_data.get("inventory", []) or [],
            revealed_information=canon_data.get("revealed_information", []) or [],
            unresolved_threads=canon_data.get("unresolved_threads", []) or [],
            relationship_states=canon_data.get("relationship_states", {}) or {},
            latest_status=canon_data.get("latest_status", ""),
        )

        return validate_story_session(
            StorySession(world_bible=world_bible, outline=outline, canon=canon, memory=[])
        )
