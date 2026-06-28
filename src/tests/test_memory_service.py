from src.schemas.story import Chapter, MangaPage, MangaPanel, MemoryEntry, StoryBeat, StoryCanon, StoryOutline, StorySession, WorldBible, Character
from src.services.memory_service import build_writer_memory_payload, select_relevant_memories


def _build_session() -> StorySession:
    session = StorySession(
        world_bible=WorldBible(
            story_id="abc12345",
            title="Memory Test",
            genre="dark_fantasy",
            art_style="anime",
            tone="dramatic",
            setting="Ancient ruins",
            protagonist=Character(name="Kael", role="protagonist", appearance="Hero", sd_anchor="silver hair"),
            side_characters=[],
            lore="Old gods and broken seals.",
            target_chapters=4,
            opening_hook="A sealed gate trembles.",
        ),
        outline=StoryOutline(
            premise="A hero explores sealed ruins.",
            opening_hook="A sealed gate trembles.",
            ending_vision="Truth beneath the city.",
            beats=[
                StoryBeat(1, "Gate", "Enter the ruins", "Fear", "A seal", "exploration", ["Gate"]),
                StoryBeat(2, "Archive", "Find the archive", "A rival arrives", "The map is alive", "dialogue", ["Map", "Archive"]),
                StoryBeat(3, "Vault", "Reach the vault", "Trap", "Ancestor secret", "magic", ["Vault"]),
                StoryBeat(4, "Core", "Decide fate", "Collapse", "Final truth", "combat", ["Core"]),
            ],
        ),
        canon=StoryCanon(
            current_location="Archive entrance",
            active_companions=["Mira"],
            inventory=["living map"],
            revealed_information=["The archive responds to bloodlines"],
            unresolved_threads=["Who sent the rival?"],
            relationship_states={"Mira": "Cautiously loyal"},
            latest_status="The path inward is unstable.",
        ),
    )
    session.memory = [
        MemoryEntry(
            chapter_number=1,
            summary="Kael opened the ancient gate and met Mira.",
            key_events=["Opened the gate", "Met Mira"],
            chosen_option="Open the gate",
            canon_snapshot={"current_location": "Outer gate", "unresolved_threads": ["Who built the gate?"]},
        ),
        MemoryEntry(
            chapter_number=2,
            summary="Kael found the living map near the archive entrance.",
            key_events=["Found the living map", "Reached the archive entrance"],
            chosen_option="Trust the map",
            canon_snapshot={"current_location": "Archive entrance", "inventory": ["living map"]},
        ),
    ]
    session.chapters = [
        Chapter(
            chapter_number=1,
            title="Gate",
            choice_that_led_here="",
            narrative_text="Gate text",
            manga_page=MangaPage(layout="2x2", panels=[MangaPanel("top-left", "gate scene", "wide shot", "dramatic")], dominant_mood="dramatic"),
            chapter_ending="The gate opened.",
            key_events=["Opened the gate", "Met Mira"],
            state_changes={},
            next_options=[],
            summary="- Opened the gate",
        ),
        Chapter(
            chapter_number=2,
            title="Archive",
            choice_that_led_here="Trust the map",
            narrative_text="Archive text",
            manga_page=MangaPage(layout="2x2", panels=[MangaPanel("top-left", "archive scene", "wide shot", "mysterious")], dominant_mood="mysterious"),
            chapter_ending="The map pulsed with light.",
            key_events=["Found the living map", "Reached the archive entrance"],
            state_changes={},
            next_options=[],
            summary="- Found the living map",
        ),
    ]
    return session


def test_select_relevant_memories_prefers_recent_and_beat_related():
    session = _build_session()
    beat = session.outline.beats[2]
    memories = select_relevant_memories(session, beat)
    assert len(memories) >= 2
    assert memories[-1].chapter_number == 2


def test_build_writer_memory_payload_returns_compact_structured_entries():
    session = _build_session()
    memories = select_relevant_memories(session, session.outline.beats[2])
    payload = build_writer_memory_payload(session, memories)
    assert payload
    assert "summary" in payload[0]
    assert "unresolved_threads" in payload[0]
