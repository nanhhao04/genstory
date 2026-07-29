from __future__ import annotations

import logging
import os
import time
import uuid
from typing import Optional

from src.core.llm import cfg, hf_client
from src.core.metrics import IMAGE_GENERATION_DURATION
from src.prompts.story_prompts import build_sd_prompt
from src.schemas.story import Chapter, WorldBible

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")


async def generate_manga_page(
    chapter: Chapter, bible: WorldBible, save_dir: str = OUTPUT_DIR
) -> Optional[str]:
    os.makedirs(save_dir, exist_ok=True)
    manga_page_dict = {
        "layout": chapter.manga_page.layout,
        "dominant_mood": chapter.manga_page.dominant_mood,
        "panels": [
            {
                "position": panel.position,
                "scene": panel.scene,
                "focus": panel.focus,
                "mood": panel.mood,
            }
            for panel in chapter.manga_page.panels
        ],
    }
    bible_dict = {
        "story_id": bible.story_id,
        "protagonist": {"sd_anchor": bible.protagonist.sd_anchor},
        "side_characters": [
            {"name": char.name, "sd_anchor": char.sd_anchor} for char in bible.side_characters
        ],
    }
    sd_params = build_sd_prompt(manga_page_dict, bible_dict, bible.art_style)
    filename = f"chapter_{chapter.chapter_number:02d}_{uuid.uuid4().hex[:6]}.png"
    path = os.path.join(save_dir, filename)

    start_time = time.time()
    status = "success"
    try:
        image = await hf_client.text_to_image(
            sd_params["prompt"],
            model=cfg.get("HF_IMAGE_MODEL"),
            negative_prompt=sd_params["negative_prompt"],
            width=sd_params["width"],
            height=sd_params["height"],
        )
        image.save(path)
        return f"outputs/{filename}"
    except Exception as exc:
        status = "failed"
        logging.error("Image generation failed: %s", exc)
        return None
    finally:
        duration = time.time() - start_time
        IMAGE_GENERATION_DURATION.labels(status=status).observe(duration)
