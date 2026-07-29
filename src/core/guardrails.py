"""Input and output guardrails for the story pipeline."""

from __future__ import annotations

import re

from src.schemas.story import (
    Chapter,
    MangaPage,
    MangaPanel,
    NextOption,
    StoryBeat,
    StoryCanon,
    StoryOutline,
    StorySession,
    WorldBible,
)

ALLOWED_GENRES = {"dark_fantasy", "sci_fi", "thriller", "romance", "adventure"}
ALLOWED_ART_STYLES = {
    "anime",
    "cyberpunk",
    "dark_art",
    "realistic_anime",
    "ghibli_style",
    "manga_bw",
    "webtoon",
}
ALLOWED_CONSEQUENCE_TYPES = {"combat", "dialogue", "exploration", "stealth", "magic"}
INPUT_INJECTION_PATTERNS = (
    r"ignore\s+previous\s+instructions",
    r"reveal\s+(the\s+)?system\s+prompt",
    r"developer\s+message",
    r"<script\b",
    r"```(?:system|assistant|developer)",
)


class GuardrailViolation(ValueError):
    """Raised when input or output violates policy or schema constraints."""


def sanitize_text(value: str, *, max_length: int, field_name: str) -> str:
    cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", " ", value or "")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        raise GuardrailViolation(f"{field_name} must not be empty.")
    if len(cleaned) > max_length:
        raise GuardrailViolation(f"{field_name} exceeds the maximum length of {max_length}.")
    return cleaned


def validate_user_story_input(
    *,
    description: str,
    genre: str,
    art_style: str,
    protagonist_name: str,
    protagonist_description: str,
    target_chapters: int,
) -> dict[str, str | int]:
    description = sanitize_text(description, max_length=2500, field_name="description")
    protagonist_name = sanitize_text(protagonist_name, max_length=60, field_name="protagonist_name")
    protagonist_description = sanitize_optional_text(
        protagonist_description,
        max_length=400,
        field_name="protagonist_description",
    )

    lower_description = description.lower()
    lower_protagonist = protagonist_description.lower()
    for pattern in INPUT_INJECTION_PATTERNS:
        if re.search(pattern, lower_description) or re.search(pattern, lower_protagonist):
            raise GuardrailViolation("Input appears to contain prompt injection or unsafe markup.")

    if genre not in ALLOWED_GENRES:
        raise GuardrailViolation(f"Unsupported genre: {genre}")
    if art_style not in ALLOWED_ART_STYLES:
        raise GuardrailViolation(f"Unsupported art style: {art_style}")
    if not 4 <= target_chapters <= 20:
        raise GuardrailViolation("target_chapters must be between 4 and 20.")

    return {
        "description": description,
        "genre": genre,
        "art_style": art_style,
        "protagonist_name": protagonist_name,
        "protagonist_description": protagonist_description,
        "target_chapters": target_chapters,
    }


def validate_user_choice_input(chosen_option_text: str) -> str:
    choice = sanitize_text(chosen_option_text, max_length=120, field_name="chosen_option_text")
    for pattern in INPUT_INJECTION_PATTERNS:
        if re.search(pattern, choice.lower()):
            raise GuardrailViolation(
                "Choice input appears to contain prompt injection or unsafe markup."
            )
    return choice


def sanitize_optional_text(value: str, *, max_length: int, field_name: str) -> str:
    if not value:
        return ""
    return sanitize_text(value, max_length=max_length, field_name=field_name)


def validate_story_session(session: StorySession) -> StorySession:
    if not session.outline:
        raise GuardrailViolation("Planner output is missing story outline.")
    if not session.outline.beats:
        raise GuardrailViolation("Planner output must include outline beats.")
    if len(session.outline.beats) != session.world_bible.target_chapters:
        raise GuardrailViolation("Planner output beat count does not match target chapters.")
    if not session.world_bible.title.strip():
        raise GuardrailViolation("Planner output is missing story title.")
    if not session.world_bible.protagonist.name.strip():
        raise GuardrailViolation("Planner output is missing protagonist name.")

    session.world_bible = _normalize_world_bible(session.world_bible)
    session.outline = _normalize_outline(session.outline, session.world_bible.target_chapters)
    session.canon = _normalize_canon(session.canon)
    return session


def validate_chapter_output(chapter: Chapter) -> Chapter:
    chapter.title = sanitize_text(chapter.title, max_length=120, field_name="chapter_title")
    chapter.narrative_text = sanitize_text(
        chapter.narrative_text, max_length=6000, field_name="narrative_text"
    )
    chapter.chapter_ending = sanitize_text(
        chapter.chapter_ending or chapter.title, max_length=300, field_name="chapter_ending"
    )
    chapter.key_events = _normalize_list(chapter.key_events, max_items=6, item_max_length=220)
    if len(chapter.key_events) < 2:
        raise GuardrailViolation("Chapter output must include at least two key events.")
    chapter.state_changes = _normalize_state_changes(chapter.state_changes)
    chapter.manga_page = _normalize_manga_page(chapter.manga_page)
    return chapter


def validate_finalized_chapter(chapter: Chapter) -> Chapter:
    chapter = validate_chapter_output(chapter)
    chapter.next_options = _normalize_options(chapter.next_options)
    if len(chapter.next_options) < 2:
        raise GuardrailViolation("Final chapter output must include at least two valid choices.")
    if chapter.summary:
        chapter.summary = sanitize_text(chapter.summary, max_length=1200, field_name="summary")
    return chapter


def _normalize_world_bible(world_bible: WorldBible) -> WorldBible:
    world_bible.title = sanitize_text(world_bible.title, max_length=120, field_name="title")
    world_bible.tone = sanitize_text(world_bible.tone, max_length=40, field_name="tone")
    world_bible.setting = sanitize_text(world_bible.setting, max_length=800, field_name="setting")
    world_bible.lore = sanitize_text(world_bible.lore, max_length=1200, field_name="lore")
    world_bible.opening_hook = sanitize_optional_text(
        world_bible.opening_hook, max_length=300, field_name="opening_hook"
    )
    world_bible.protagonist.name = sanitize_text(
        world_bible.protagonist.name, max_length=60, field_name="protagonist_name"
    )
    world_bible.protagonist.appearance = sanitize_text(
        world_bible.protagonist.appearance,
        max_length=500,
        field_name="protagonist_appearance",
    )
    world_bible.protagonist.sd_anchor = sanitize_optional_text(
        world_bible.protagonist.sd_anchor,
        max_length=200,
        field_name="protagonist_sd_anchor",
    )
    world_bible.side_characters = world_bible.side_characters[:10]
    for char in world_bible.side_characters:
        char.name = sanitize_text(char.name, max_length=60, field_name="side_character_name")
        char.role = sanitize_optional_text(
            char.role, max_length=80, field_name="side_character_role"
        )
        char.appearance = sanitize_optional_text(
            char.appearance, max_length=400, field_name="side_character_appearance"
        )
        char.sd_anchor = sanitize_optional_text(
            char.sd_anchor, max_length=200, field_name="side_character_sd_anchor"
        )
    return world_bible


def _normalize_outline(outline: StoryOutline, target_chapters: int) -> StoryOutline:
    outline.premise = sanitize_text(outline.premise, max_length=1000, field_name="premise")
    outline.opening_hook = sanitize_optional_text(
        outline.opening_hook, max_length=300, field_name="outline_opening_hook"
    )
    outline.ending_vision = sanitize_optional_text(
        outline.ending_vision, max_length=600, field_name="ending_vision"
    )
    outline.progression_notes = _normalize_list(
        outline.progression_notes, max_items=12, item_max_length=250
    )
    outline.beats = outline.beats[:target_chapters]
    normalized_beats: list[StoryBeat] = []
    for index, beat in enumerate(outline.beats, start=1):
        normalized_beats.append(
            StoryBeat(
                chapter_number=index,
                title=sanitize_text(
                    beat.title or f"Chapter {index}", max_length=120, field_name="beat_title"
                ),
                objective=sanitize_text(
                    beat.objective or "Advance the story.",
                    max_length=300,
                    field_name="beat_objective",
                ),
                conflict=sanitize_optional_text(
                    beat.conflict, max_length=300, field_name="beat_conflict"
                ),
                reveal=sanitize_optional_text(
                    beat.reveal, max_length=300, field_name="beat_reveal"
                ),
                planned_choice_theme=sanitize_optional_text(
                    beat.planned_choice_theme,
                    max_length=120,
                    field_name="beat_choice_theme",
                ),
                must_include=_normalize_list(beat.must_include, max_items=6, item_max_length=180),
            )
        )
    outline.beats = normalized_beats
    return outline


def _normalize_canon(canon: StoryCanon) -> StoryCanon:
    return StoryCanon(
        current_location=sanitize_optional_text(
            canon.current_location, max_length=120, field_name="current_location"
        ),
        active_companions=_normalize_list(canon.active_companions, max_items=8, item_max_length=60),
        inventory=_normalize_list(canon.inventory, max_items=12, item_max_length=80),
        revealed_information=_normalize_list(
            canon.revealed_information, max_items=20, item_max_length=200
        ),
        unresolved_threads=_normalize_list(
            canon.unresolved_threads, max_items=12, item_max_length=200
        ),
        relationship_states={
            sanitize_text(
                name, max_length=60, field_name="relationship_name"
            ): sanitize_optional_text(
                state,
                max_length=160,
                field_name="relationship_state",
            )
            for name, state in canon.relationship_states.items()
        },
        latest_status=sanitize_optional_text(
            canon.latest_status, max_length=240, field_name="latest_status"
        ),
    )


def _normalize_manga_page(manga_page: MangaPage) -> MangaPage:
    allowed_layouts = {"2x2", "1top-2bottom", "2top-1bottom", "3x1", "full"}
    layout = manga_page.layout if manga_page.layout in allowed_layouts else "2x2"
    panels = []
    for panel in manga_page.panels[:4]:
        panels.append(
            MangaPanel(
                position=sanitize_optional_text(
                    panel.position, max_length=40, field_name="panel_position"
                ),
                scene=sanitize_text(panel.scene, max_length=500, field_name="panel_scene"),
                focus=sanitize_optional_text(panel.focus, max_length=40, field_name="panel_focus")
                or "medium shot",
                mood=sanitize_optional_text(panel.mood, max_length=40, field_name="panel_mood")
                or "dramatic",
            )
        )
    if not panels:
        raise GuardrailViolation("Chapter output must include at least one manga panel.")
    return MangaPage(
        layout=layout,
        panels=panels,
        dominant_mood=sanitize_optional_text(
            manga_page.dominant_mood, max_length=40, field_name="dominant_mood"
        )
        or "dramatic",
    )


def _normalize_state_changes(state_changes: dict) -> dict:
    if not isinstance(state_changes, dict):
        raise GuardrailViolation("state_changes must be a dictionary.")
    relationship_states = state_changes.get("relationship_states", {}) or {}
    return {
        "location": sanitize_optional_text(
            state_changes.get("location", ""), max_length=120, field_name="state_location"
        ),
        "companions": _normalize_list(
            state_changes.get("companions", []) or [], max_items=8, item_max_length=60
        ),
        "inventory": _normalize_list(
            state_changes.get("inventory", []) or [], max_items=12, item_max_length=80
        ),
        "new_info": _normalize_list(
            state_changes.get("new_info", []) or [], max_items=10, item_max_length=200
        ),
        "unresolved_threads": _normalize_list(
            state_changes.get("unresolved_threads", []) or [],
            max_items=10,
            item_max_length=200,
        ),
        "relationship_states": {
            sanitize_text(
                name, max_length=60, field_name="state_relationship_name"
            ): sanitize_optional_text(
                state,
                max_length=160,
                field_name="state_relationship_value",
            )
            for name, state in relationship_states.items()
        },
        "status": sanitize_optional_text(
            state_changes.get("status", ""), max_length=240, field_name="state_status"
        ),
    }


def _normalize_options(options: list[NextOption]) -> list[NextOption]:
    normalized: list[NextOption] = []
    seen_texts: set[str] = set()
    for index, option in enumerate(options[:4], start=1):
        text = sanitize_text(option.text, max_length=80, field_name="option_text")
        text_key = text.lower()
        if text_key in seen_texts:
            continue
        seen_texts.add(text_key)
        consequence_type = (
            option.consequence_type
            if option.consequence_type in ALLOWED_CONSEQUENCE_TYPES
            else "exploration"
        )
        normalized.append(
            NextOption(
                id=(option.id or chr(64 + index))[:1].upper(),
                text=text,
                hint=sanitize_optional_text(option.hint, max_length=160, field_name="option_hint"),
                consequence_type=consequence_type,
            )
        )
    return normalized


def _normalize_list(values: list[str], *, max_items: int, item_max_length: int) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in values[:max_items]:
        cleaned = sanitize_optional_text(
            str(raw), max_length=item_max_length, field_name="list_item"
        )
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(cleaned)
    return normalized
