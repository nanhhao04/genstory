"""Story domain schemas for the interactive visual novel."""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Character:
    name: str
    role: str
    appearance: str
    sd_anchor: str


@dataclass
class StoryBeat:
    chapter_number: int
    title: str
    objective: str
    conflict: str
    reveal: str
    planned_choice_theme: str
    must_include: list[str] = field(default_factory=list)


@dataclass
class StoryOutline:
    premise: str
    opening_hook: str
    ending_vision: str
    progression_notes: list[str] = field(default_factory=list)
    beats: list[StoryBeat] = field(default_factory=list)


@dataclass
class StoryCanon:
    current_location: str = ""
    active_companions: list[str] = field(default_factory=list)
    inventory: list[str] = field(default_factory=list)
    revealed_information: list[str] = field(default_factory=list)
    unresolved_threads: list[str] = field(default_factory=list)
    relationship_states: dict[str, str] = field(default_factory=dict)
    latest_status: str = ""


@dataclass
class MemoryEntry:
    chapter_number: int
    summary: str
    key_events: list[str] = field(default_factory=list)
    chosen_option: str = ""
    canon_snapshot: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorldBible:
    story_id: str
    title: str
    genre: str
    art_style: str
    tone: str
    setting: str
    protagonist: Character
    side_characters: list[Character]
    lore: str
    target_chapters: int
    opening_hook: str = ""


@dataclass
class MangaPanel:
    position: str
    scene: str
    focus: str
    mood: str


@dataclass
class MangaPage:
    layout: str
    panels: list[MangaPanel]
    dominant_mood: str


@dataclass
class NextOption:
    id: str
    text: str
    hint: str
    consequence_type: str


@dataclass
class Chapter:
    chapter_number: int
    title: str
    choice_that_led_here: str
    narrative_text: str
    manga_page: MangaPage
    chapter_ending: str
    key_events: list[str]
    state_changes: dict
    next_options: list[NextOption]
    image_path: Optional[str] = None
    summary: Optional[str] = None


@dataclass
class StorySession:
    """Complete state for an in-progress story."""

    world_bible: WorldBible
    outline: Optional[StoryOutline] = None
    canon: StoryCanon = field(default_factory=StoryCanon)
    memory: list[MemoryEntry] = field(default_factory=list)
    chapters: list[Chapter] = field(default_factory=list)

    @property
    def current_chapter_number(self) -> int:
        return len(self.chapters)

    @property
    def latest_chapter(self) -> Optional[Chapter]:
        return self.chapters[-1] if self.chapters else None

    @property
    def is_finished(self) -> bool:
        return self.current_chapter_number >= self.world_bible.target_chapters
