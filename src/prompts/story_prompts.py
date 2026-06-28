"""Prompt definitions for the multi-agent story pipeline."""

STORY_PLANNER_SYSTEM = """
You are the Story Planner Agent for an interactive visual novel.
Design a coherent world, character cast, canon rules, and a high-level story outline.
Return strict JSON only. No markdown. No explanation.
""".strip()

STORY_PLANNER_USER = """
Create the master story plan from this request.

Story description: {description}
Genre: {genre}
Art style: {art_style}
Protagonist name: {protagonist_name}
Protagonist description: {protagonist_description}
Target chapters: {target_chapters}

Return JSON with this schema:
{{
  "world_bible": {{
    "title": "Compelling title",
    "tone": "dramatic|lighthearted|mysterious|action",
    "setting": "World and era description",
    "protagonist": {{
      "name": "{protagonist_name}",
      "appearance": "Detailed Vietnamese appearance description",
      "sd_anchor": "Short English visual anchor",
      "background": "Origin and motivation"
    }},
    "side_characters": [
      {{
        "name": "Character name",
        "role": "Narrative role",
        "appearance": "Appearance description",
        "sd_anchor": "Short English visual anchor"
      }}
    ],
    "lore": "World rules, power system, factions",
    "opening_hook": "A strong opening hook for chapter 1"
  }},
  "outline": {{
    "premise": "One paragraph premise",
    "opening_hook": "Hook for chapter 1",
    "ending_vision": "The intended emotional ending direction",
    "progression_notes": ["note 1", "note 2"],
    "beats": [
      {{
        "chapter_number": 1,
        "title": "Beat title",
        "objective": "Main purpose of the chapter",
        "conflict": "Primary conflict",
        "reveal": "What new truth is revealed",
        "planned_choice_theme": "What type of decision closes the chapter",
        "must_include": ["required scene", "required reveal"]
      }}
    ]
  }},
  "initial_canon": {{
    "current_location": "Starting location",
    "active_companions": [],
    "inventory": [],
    "revealed_information": [],
    "unresolved_threads": ["thread 1"],
    "relationship_states": {{
      "{protagonist_name}": "Self-driven but incomplete"
    }},
    "latest_status": "Current emotional and plot status"
  }}
}}

Rules:
- Create exactly {target_chapters} beats.
- Keep the tone aligned with the selected genre.
- Side characters should be useful for future conflicts.
- Make the outline suitable for branching choices but preserve a strong canon spine.
""".strip()

CHAPTER_WRITER_SYSTEM = """
You are the Chapter Writer Agent.
Write only the current chapter while respecting the planner's outline and the canon memory.
Return strict JSON only. No markdown. No explanation.
""".strip()

CHAPTER_WRITER_USER = """
Write chapter {next_num} for this interactive story.

=== WORLD BIBLE ===
{world_bible_json}

=== STORY OUTLINE ===
{outline_json}

=== TARGET BEAT FOR THIS CHAPTER ===
{beat_json}

=== CURRENT CANON ===
{canon_json}

=== MEMORY OF PRIOR CHAPTERS ===
{memory_json}

=== LATEST CHAPTER ===
{last_chapter_text}

=== USER CHOICE THAT LED HERE ===
"{chosen_option}"

Requirements:
- Write 300-450 words.
- Use second person perspective in Vietnamese and address the protagonist as "ban".
- Start from the consequence of the chosen option when chapter > 1.
- Follow the beat objective and must_include constraints.
- End with a sharp cliffhanger.

Return JSON:
{{
  "chapter_title": "Title",
  "narrative_text": "Full chapter text",
  "manga_page": {{
    "layout": "2x2|1top-2bottom|2top-1bottom|3x1|full",
    "panels": [
      {{
        "position": "top-left|top-right|bottom-left|bottom-right|wide-top|wide-bottom|full",
        "scene": "Detailed English scene description for image generation",
        "focus": "wide shot|medium shot|close-up|extreme close-up",
        "mood": "tense|action|calm|emotional|mysterious|dramatic"
      }}
    ],
    "dominant_mood": "dark|action|emotional|mysterious|dramatic|hopeful"
  }},
  "chapter_ending": "Exact last-line cliffhanger",
  "key_events": ["event 1", "event 2", "event 3"],
  "state_changes": {{
    "location": "current location after the chapter",
    "companions": ["active companion"],
    "inventory": ["important item"],
    "new_info": ["newly revealed truth"],
    "unresolved_threads": ["remaining question"],
    "relationship_states": {{
      "character": "relationship update"
    }},
    "status": "short latest plot status"
  }}
}}
""".strip()

INTERACTION_MANAGER_SYSTEM = """
You are the Interaction Manager Agent.
Generate coherent end-of-chapter choices, validate logic against canon, and update memory.
Return strict JSON only. No markdown. No explanation.
""".strip()

INTERACTION_MANAGER_USER = """
Review this completed chapter and act as canon + choice manager.

=== WORLD BIBLE ===
{world_bible_json}

=== STORY OUTLINE ===
{outline_json}

=== TARGET BEAT FOR THIS CHAPTER ===
{beat_json}

=== CURRENT CANON BEFORE UPDATE ===
{canon_json}

=== MEMORY OF PRIOR CHAPTERS ===
{memory_json}

=== CHAPTER DRAFT ===
{chapter_json}

Return JSON:
{{
  "summary": ["bullet 1", "bullet 2", "bullet 3", "bullet 4"],
  "canon_update": {{
    "current_location": "updated location",
    "active_companions": ["companion"],
    "inventory": ["important item"],
    "revealed_information": ["known truth"],
    "unresolved_threads": ["open thread"],
    "relationship_states": {{
      "character": "state"
    }},
    "latest_status": "current story status"
  }},
  "next_options": [
    {{
      "id": "A",
      "text": "Choice text under 12 words",
      "hint": "What it may risk or gain",
      "consequence_type": "combat|dialogue|exploration|stealth|magic"
    }},
    {{
      "id": "B",
      "text": "Another distinct choice",
      "hint": "Different tradeoff",
      "consequence_type": "combat|dialogue|exploration|stealth|magic"
    }},
    {{
      "id": "C",
      "text": "Third distinct choice",
      "hint": "Different tradeoff",
      "consequence_type": "combat|dialogue|exploration|stealth|magic"
    }},
    {{
      "id": "D",
      "text": "Fourth distinct choice",
      "hint": "Different tradeoff",
      "consequence_type": "combat|dialogue|exploration|stealth|magic"
    }}
  ],
  "consistency_report": {{
    "is_consistent": true,
    "issues": [],
    "reasoning": "Short explanation"
  }}
}}

Rules:
- Choices must follow directly from the chapter ending.
- Choices must be meaningfully different from each other.
- Preserve canon continuity.
- If you find a contradiction, resolve it conservatively in canon_update and report it.
""".strip()

LAYOUT_KEYWORDS = {
    "2x2": "4-panel manga page, 2x2 grid layout, equal panels",
    "1top-2bottom": "3-panel manga page, one large panel on top, two smaller panels on bottom",
    "2top-1bottom": "3-panel manga page, two smaller panels on top, one large panel on bottom",
    "3x1": "3-panel manga page, three horizontal panels stacked vertically",
    "full": "single full-page manga panel",
}

MOOD_KEYWORDS = {
    "dark": "dark atmosphere, heavy shadows, dramatic chiaroscuro lighting",
    "action": "dynamic poses, speed lines, motion blur, kinetic energy",
    "emotional": "soft lighting, detailed facial expressions, intimate framing",
    "mysterious": "foggy atmosphere, moonlight, long shadows, silhouettes",
    "dramatic": "low angle shot, strong contrast, intense expressions",
    "hopeful": "warm lighting, open space, uplifting composition",
}

ART_STYLE_KEYWORDS = {
    "anime": "anime style, vibrant colors, clean linework, detailed shading",
    "manga_bw": "black and white manga, clean ink linework, screentone shading, no color",
    "dark_art": "dark fantasy illustration, muted colors, painterly style, atmospheric",
    "webtoon": "webtoon style, flat clean colors, simple linework, bright palette",
}

SD_NEGATIVE = (
    "deformed, ugly, bad anatomy, extra limbs, missing limbs, "
    "blurry, low quality, watermark, text, logo, "
    "inconsistent character, wrong eye color, wrong hair color, "
    "merged panels without borders, nsfw"
)


def build_sd_prompt(manga_page: dict, world_bible: dict, art_style: str) -> dict:
    """Build an image prompt from the manga page and story world."""

    layout = manga_page.get("layout", "2x2")
    dom_mood = manga_page.get("dominant_mood", "dramatic")
    panels = manga_page.get("panels", [])
    protagonist = world_bible.get("protagonist", {})
    anchor = protagonist.get("sd_anchor", "")

    side_anchors = []
    for char in world_bible.get("side_characters", []):
        char_name = char.get("name", "").lower()
        for panel in panels:
            if char_name in panel.get("scene", "").lower():
                side_anchors.append(char.get("sd_anchor", ""))
                break

    panel_descs = []
    for idx, panel in enumerate(panels, 1):
        focus = panel.get("focus", "medium shot")
        scene = panel.get("scene", "")
        panel_descs.append(f"panel {idx} [{focus}]: {scene}")

    all_anchors = ", ".join(filter(None, [anchor] + side_anchors))
    panels_text = " | ".join(panel_descs)

    prompt = (
        f"{LAYOUT_KEYWORDS.get(layout, LAYOUT_KEYWORDS['2x2'])}, "
        f"{ART_STYLE_KEYWORDS.get(art_style, ART_STYLE_KEYWORDS['anime'])}, "
        f"panel borders, gutters between panels, "
        f"{MOOD_KEYWORDS.get(dom_mood, '')}, "
        f"characters: {all_anchors}, "
        f"{panels_text}, "
        f"high quality, detailed, professional manga art"
    )

    story_id = world_bible.get("story_id", "default")
    stable_seed = abs(hash(story_id)) % (2 ** 31)

    return {
        "prompt": prompt,
        "negative_prompt": SD_NEGATIVE,
        "width": 768,
        "height": 1024,
        "num_inference_steps": 28,
        "guidance_scale": 7.5,
        "seed": stable_seed,
    }
