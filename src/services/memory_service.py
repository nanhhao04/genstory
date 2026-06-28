from __future__ import annotations

import re

from src.schemas.story import MemoryEntry, StoryBeat, StoryCanon, StorySession


def select_relevant_memories(
    session: StorySession,
    beat: StoryBeat | None = None,
    *,
    recent_limit: int = 3,
    max_items: int = 8,
) -> list[MemoryEntry]:
    """Return a compact, relevant slice of story memory for the next chapter."""

    if not session.memory:
        return []

    recent = session.memory[-recent_limit:]
    keyword_set = _build_keyword_set(session.canon, beat)

    scored: list[tuple[int, MemoryEntry]] = []
    for entry in session.memory:
        score = 0
        haystack = " ".join(
            [
                entry.summary,
                entry.chosen_option,
                " ".join(entry.key_events),
                " ".join(str(v) for v in entry.canon_snapshot.values()),
            ]
        ).lower()

        if entry in recent:
            score += 100
        score += min(len(entry.key_events), 4) * 2
        score += sum(6 for keyword in keyword_set if keyword and keyword in haystack)
        if entry.chapter_number == session.current_chapter_number:
            score += 5
        scored.append((score, entry))

    scored.sort(key=lambda item: (item[0], item[1].chapter_number), reverse=True)

    selected: list[MemoryEntry] = []
    seen_chapters: set[int] = set()
    for _, entry in scored:
        if entry.chapter_number in seen_chapters:
            continue
        selected.append(entry)
        seen_chapters.add(entry.chapter_number)
        if len(selected) >= max_items:
            break

    selected.sort(key=lambda item: item.chapter_number)
    return selected


def build_writer_memory_payload(
    session: StorySession,
    memories: list[MemoryEntry],
) -> list[dict]:
    """Prepare a compact structured memory view for the writer agent prompt."""

    payload = []
    for entry in memories:
        snapshot = entry.canon_snapshot or {}
        payload.append(
            {
                "chapter_number": entry.chapter_number,
                "summary": entry.summary,
                "key_events": entry.key_events[:4],
                "chosen_option": entry.chosen_option,
                "location": snapshot.get("current_location", ""),
                "active_companions": snapshot.get("active_companions", [])[:5],
                "inventory": snapshot.get("inventory", [])[:5],
                "revealed_information": snapshot.get("revealed_information", [])[:4],
                "unresolved_threads": snapshot.get("unresolved_threads", [])[:4],
                "latest_status": snapshot.get("latest_status", ""),
            }
        )

    if not payload and session.latest_chapter:
        payload.append(
            {
                "chapter_number": session.latest_chapter.chapter_number,
                "summary": session.latest_chapter.summary or "",
                "key_events": session.latest_chapter.key_events[:4],
                "chosen_option": session.latest_chapter.choice_that_led_here,
                "location": session.canon.current_location,
                "active_companions": session.canon.active_companions[:5],
                "inventory": session.canon.inventory[:5],
                "revealed_information": session.canon.revealed_information[:4],
                "unresolved_threads": session.canon.unresolved_threads[:4],
                "latest_status": session.canon.latest_status,
            }
        )

    return payload


def _build_keyword_set(canon: StoryCanon, beat: StoryBeat | None) -> set[str]:
    candidates = set()
    if beat:
        candidates.update(_tokenize_text(beat.title))
        candidates.update(_tokenize_text(beat.objective))
        candidates.update(_tokenize_text(beat.conflict))
        candidates.update(_tokenize_text(beat.reveal))
        for item in beat.must_include:
            candidates.update(_tokenize_text(item))

    candidates.update(_tokenize_text(canon.current_location))
    candidates.update(_tokenize_text(canon.latest_status))
    for item in canon.active_companions + canon.inventory + canon.unresolved_threads:
        candidates.update(_tokenize_text(item))

    return {item for item in candidates if len(item) >= 4}


def _tokenize_text(text: str) -> set[str]:
    if not text:
        return set()
    return {token for token in re.findall(r"\w+", text.lower()) if token}
