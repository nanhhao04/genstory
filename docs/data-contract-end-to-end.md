# GenStory Data Contract And End-to-End Flow

## Scope

This document describes the current runtime contract of the GenStory story pipeline:

- API request and response shapes
- internal shared state passed through LangGraph
- agent input and output contracts
- guardrail checkpoints
- memory and persistence flow

The document reflects the current implementation in:

- `src/api/endpoints.py`
- `src/services/story_engine.py`
- `src/agents/langgraph_story_flow.py`
- `src/agents/*.py`
- `src/core/guardrails.py`
- `src/services/memory_service.py`
- `src/schemas/story.py`

## Architecture Summary

The current story generation stack is:

`HTTP API -> StoryEngine -> LangGraph -> Story Planner Agent / Chapter Writer Agent / Interaction Manager Agent -> Image Service -> DB`

The orchestration model is:

- `StoryEngine` is the application service entrypoint
- `LangGraph` coordinates agent execution
- agents exchange data through a shared `StoryGraphState`
- durable story state is represented by `StorySession`
- input and output guardrails run before and after agent execution

## Core Domain Contracts

### `StorySession`

`StorySession` is the canonical runtime object for an in-progress story.

```python
StorySession(
    world_bible: WorldBible,
    outline: Optional[StoryOutline],
    canon: StoryCanon,
    memory: list[MemoryEntry],
    chapters: list[Chapter],
)
```

Responsibilities:

- `world_bible`: stable story identity and world setup
- `outline`: planner-defined spine across target chapters
- `canon`: current truth of the story world
- `memory`: compact episodic memory of previous chapters
- `chapters`: rendered user-facing chapter history

### `WorldBible`

`WorldBible` holds the stable planning context shared across all chapters.

Key fields:

- `story_id`
- `title`
- `genre`
- `art_style`
- `tone`
- `setting`
- `protagonist`
- `side_characters`
- `lore`
- `target_chapters`
- `opening_hook`

### `StoryOutline`

`StoryOutline` is the planner-level contract for the full story arc.

Key fields:

- `premise`
- `opening_hook`
- `ending_vision`
- `progression_notes`
- `beats`

Each `StoryBeat` defines one chapter target:

- `chapter_number`
- `title`
- `objective`
- `conflict`
- `reveal`
- `planned_choice_theme`
- `must_include`

### `StoryCanon`

`StoryCanon` is the structured continuity state.

Key fields:

- `current_location`
- `active_companions`
- `inventory`
- `revealed_information`
- `unresolved_threads`
- `relationship_states`
- `latest_status`

### `MemoryEntry`

`MemoryEntry` is episodic memory for past chapters.

Key fields:

- `chapter_number`
- `summary`
- `key_events`
- `chosen_option`
- `canon_snapshot`

### `Chapter`

`Chapter` is the main output returned to the UI and persisted to the database.

Key fields:

- `chapter_number`
- `title`
- `choice_that_led_here`
- `narrative_text`
- `manga_page`
- `chapter_ending`
- `key_events`
- `state_changes`
- `next_options`
- `image_path`
- `summary`

## API Contracts

### `POST /api/stories/start`

Request body:

```json
{
  "description": "string, 20..2500 chars",
  "genre": "dark_fantasy|sci_fi|thriller|romance|adventure",
  "art_style": "anime|cyberpunk|dark_art|realistic_anime|ghibli_style|manga_bw|webtoon",
  "protagonist_name": "string, 2..60 chars",
  "protagonist_description": "string, <= 400 chars",
  "target_chapters": "integer, 4..20"
}
```

Response body:

```json
{
  "story_id": "string",
  "chapter": {
    "...": "Chapter payload"
  }
}
```

### `POST /api/stories/next`

Request body:

```json
{
  "story_id": "string",
  "chosen_option_text": "string, 2..120 chars"
}
```

Response body:

```json
{
  "chapter": {
    "...": "Chapter payload"
  }
}
```

### `GET /api/stories/{story_id}`

Response body:

```json
{
  "bible": {
    "...": "WorldBible payload"
  },
  "chapters": [
    {
      "...": "Chapter payload"
    }
  ]
}
```

## LangGraph State Contract

The shared graph state is `StoryGraphState`.

```python
class StoryGraphState(TypedDict, total=False):
    description: str
    genre: str
    art_style: str
    protagonist_name: str
    protagonist_description: str
    target_chapters: int
    chosen_option_text: str
    session: StorySession
    retrieved_memories: list[MemoryEntry]
    chapter: Chapter
    progress_callback: Optional[Callable[..., Any]]
```

Field ownership:

- API input populates request fields
- `plan_story` writes `session`
- `retrieve_memory` writes `retrieved_memories`
- `write_chapter` writes `chapter`
- `finalize_interaction` mutates `session` and `chapter`
- `generate_image` mutates `chapter.image_path`

## Agent Contracts

### Story Planner Agent

Implementation:

- `src/agents/story_planner_agent.py`

Input:

- `description`
- `genre`
- `art_style`
- `protagonist_name`
- `protagonist_description`
- `target_chapters`

Output:

- a validated `StorySession` with:
  - `world_bible`
  - `outline`
  - `canon`
  - empty `memory`
  - empty `chapters`

Planner JSON expectation:

- `world_bible`
- `outline`
- `initial_canon`

Guardrail:

- `validate_story_session(...)`

### Chapter Writer Agent

Implementation:

- `src/agents/chapter_writer_agent.py`

Input:

- `session`
- `chosen_option`
- `retrieved_memories`

Writer prompt depends on:

- `world_bible`
- `outline`
- current `StoryBeat`
- `canon`
- compact retrieved memory payload
- latest chapter text
- chosen option

Output:

- a validated `Chapter` without final choices yet

Writer JSON expectation:

- `chapter_title`
- `narrative_text`
- `manga_page`
- `chapter_ending`
- `key_events`
- `state_changes`

Guardrail:

- `validate_chapter_output(...)`

### Interaction Manager Agent

Implementation:

- `src/agents/interaction_manager_agent.py`

Input:

- `session`
- current `chapter`

Responsibilities:

- generate end-of-chapter choices
- update canon
- append episodic memory
- produce chapter summary

Output:

- a validated finalized `Chapter`
- updated `session.canon`
- appended `session.memory`

Interaction JSON expectation:

- `summary`
- `canon_update`
- `next_options`
- `consistency_report`

Guardrail:

- `validate_finalized_chapter(...)`

## Memory Contract

Implementation:

- `src/services/memory_service.py`

There are two active memory forms:

- `canonical memory`: `StoryCanon`
- `episodic memory`: `list[MemoryEntry]`

### Retrieval Policy

`select_relevant_memories(...)` returns a compact memory slice for the writer.

Selection signals:

- recent chapters
- overlap with current `StoryBeat`
- overlap with canon keywords
- chapter key event density

### Writer Memory Payload

`build_writer_memory_payload(...)` converts raw `MemoryEntry` objects into a compact prompt-ready structure.

Each item may contain:

- `chapter_number`
- `summary`
- `key_events`
- `chosen_option`
- `location`
- `active_companions`
- `inventory`
- `revealed_information`
- `unresolved_threads`
- `latest_status`

## Guardrail Contract

Implementation:

- `src/core/guardrails.py`

### Input Guardrails

Applied before graph execution:

- text sanitization
- empty-value rejection
- length limits
- supported `genre` validation
- supported `art_style` validation
- `target_chapters` range validation
- basic prompt injection pattern detection
- basic unsafe markup detection

Primary functions:

- `validate_user_story_input(...)`
- `validate_user_choice_input(...)`

### Output Guardrails

Applied after agent execution:

- title and narrative non-empty checks
- chapter event count checks
- manga page normalization
- state change shape normalization
- choice normalization and deduplication
- canon normalization
- outline beat count consistency

Primary functions:

- `validate_story_session(...)`
- `validate_chapter_output(...)`
- `validate_finalized_chapter(...)`

### Failure Mode

Guardrail failures raise:

```python
GuardrailViolation
```

At the API layer, this becomes:

- HTTP `400 Bad Request`

## Persistence Contract

### Database Tables

Main tables:

- `users`
- `world_bibles`
- `stories`
- `chapters`

### What Gets Stored

`world_bibles.lore` stores the structured story runtime metadata:

- `tone`
- `setting`
- `lore`
- `opening_hook`
- `protagonist_sd_anchor`
- `side_characters`
- `outline`
- `canon`
- `memory`
- `target_chapters`

`chapters` stores per-chapter user-facing output:

- title
- narrative text
- image path
- summary
- choice that led here
- chapter ending
- key events
- state changes
- manga page data
- options

## End-to-End Flow

### Flow A: Start Story

1. Client sends `POST /api/stories/start`.
2. Pydantic validates request body.
3. `StoryEngine.start_story(...)` runs input guardrails.
4. `StoryLangGraphOrchestrator.run_start_story(...)` starts LangGraph.
5. `plan_story` node creates a new `StorySession`.
6. `retrieve_memory` node returns an empty or minimal memory slice.
7. `write_chapter` node generates chapter 1 from planner output.
8. Writer output guardrail validates the draft chapter.
9. `finalize_interaction` node generates choices and updates canon/memory.
10. Finalized chapter guardrail validates the chapter.
11. `generate_image` node creates the manga page image and writes `image_path`.
12. Graph returns `session + chapter`.
13. `StoryEngine` appends the chapter into `session.chapters`.
14. `StoryEngine` persists:
    - `world_bibles`
    - `stories`
    - first `chapters` row
15. API returns `story_id + chapter`.

### Flow B: Next Chapter

1. Client sends `POST /api/stories/next`.
2. `StoryEngine.load_story(...)` hydrates `StorySession` from DB.
3. `StoryEngine.next_chapter(...)` runs choice input guardrail.
4. `StoryLangGraphOrchestrator.run_next_chapter(...)` starts LangGraph.
5. `retrieve_memory` selects relevant episodic memory.
6. `write_chapter` generates the next chapter from:
   - current canon
   - retrieved memory
   - current beat
   - chosen option
7. Writer output guardrail validates the draft chapter.
8. `finalize_interaction` updates canon, summary, memory and options.
9. Finalized chapter guardrail validates the output.
10. `generate_image` generates and attaches chapter image.
11. Graph returns updated `session + chapter`.
12. `StoryEngine` appends the chapter to session history.
13. `StoryEngine` persists:
    - new chapter row
    - refreshed `world_bibles.lore`
    - updated `stories.current_chapter_index`
14. API returns the new `chapter`.

## Sequence Overview

```text
Client
  -> FastAPI endpoint
  -> StoryEngine
  -> Input Guardrail
  -> LangGraph
      -> Story Planner Agent or hydrated Session
      -> Memory Retrieval
      -> Chapter Writer Agent
      -> Output Guardrail
      -> Interaction Manager Agent
      -> Output Guardrail
      -> Image Service
  -> StoryEngine persistence
  -> API response
```

## Current Invariants

The current pipeline assumes:

- one `StorySession` maps to one `story_id`
- one `StoryBeat` maps to one target chapter number
- finalized chapters must have at least two valid choices
- canonical continuity is updated after every chapter
- memory is append-only within the current story session
- image generation is best effort and may return `None`

## Known Extension Points

Recommended future extension points:

- add a `consistency repair` branch in LangGraph when `consistency_report` fails
- move `memory` into its own persistence table if story length grows
- add richer `MemoryEntry` metadata such as `importance`, `tags`, `entities`
- add stronger content policy guardrails for sensitive story categories
- add per-agent traces for audit and debugging
