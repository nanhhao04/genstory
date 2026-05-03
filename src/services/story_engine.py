from dataclasses import asdict
import json
import os
import re
import asyncio
import uuid
import traceback
import logging
import datetime
import requests
from typing import Optional, Callable, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fpdf import FPDF

from src.core.llm import llm, hf_client, cfg
from src.prompts.story_prompts import (
    WORLD_BIBLE_SYSTEM, WORLD_BIBLE_USER,
    CHAPTER_SYSTEM, CHAPTER_USER,
    SUMMARIZE_SYSTEM, SUMMARIZE_USER,
    build_sd_prompt,
)
from src.schemas.story import (
    WorldBible, Character, Chapter, MangaPage, MangaPanel,
    NextOption, StorySession,
)
from src.database.models import WorldBibleTable, StoryTable, ChapterTable

HF_MODEL = cfg.get("HF_IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")
LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "logs"))

def _log_to_file(filename: str, prompt: str, response: str):
    """Lưu log dưới dạng JSON array đẹp (pretty-print) để dễ đọc."""
    os.makedirs(LOG_DIR, exist_ok=True)
    log_path = os.path.join(LOG_DIR, f"{filename}.json")
    
    new_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "prompt": prompt,
        "response": response
    }
    
    # Đọc dữ liệu cũ nếu có
    data = []
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, list): data = [data]
        except Exception:
            data = []
            
    data.append(new_entry)
    
    # Ghi lại toàn bộ array (pretty-print)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def _call_gemini(system: str, user: str, log_name: str = "general") -> str:
    """Gọi Gemini với system + user prompt, trả raw text."""
    full_prompt = f"{system}\n\n{user}"
    print(f"  [Gemini] Đang gọi API (model: {llm.model_name})...")
    try:
        response = await llm.generate_content_async(full_prompt)
        text = response.text
        _log_to_file(log_name, full_prompt, text)
        print(f"  [Gemini] Phản hồi thành công. ({len(text)} chars)")
        return text
    except Exception as e:
        print(f"  [Gemini] LỖI API: {e}")
        raise

async def _call_gemini_json(system: str, user: str, log_name: str, context: str) -> dict:
    """Gọi Gemini và bóc tách JSON"""
    raw = await _call_gemini(system, user, log_name=log_name)
    try:
        return _parse_json_safe(raw, context=context)
    except ValueError as e:
        print(f"  [Gemini] JSON lỗi, đang yêu cầu sửa lại...")
        repair_system = "Bạn là chuyên gia về JSON. Hãy sửa lại đoạn văn bản sau để nó là một JSON hợp lệ và đúng schema đã yêu cầu. CHỈ TRẢ VỀ JSON, KHÔNG GIẢI THÍCH."
        repair_user = f"Context: {context}\nLỗi: {e}\n\nVăn bản cần sửa:\n{raw}"
        raw_repaired = await _call_gemini(repair_system, repair_user, log_name=f"{log_name}_repair")
        return _parse_json_safe(raw_repaired, context=f"{context}_repaired")

def _parse_json_safe(raw: str, context: str = "") -> dict:
    # Loại bỏ code block markdown
    clean = re.sub(r"```(?:json)?\s*", "", str(raw)).strip().rstrip("`").strip()
    # Tìm cặp { } lớn nhất nếu vẫn lỗi
    if not (clean.startswith("{") and clean.endswith("}")):
        match = re.search(r"(\{.*\})", clean, re.DOTALL)
        if match:
            clean = match.group(1)
            
    print(f"  [Parser] Đang parse JSON ({len(clean)} chars)...")
    try:
        data = json.loads(clean)
        print(f"  [Parser] Parse thành công.")
        return data
    except json.JSONDecodeError as e:
        print(f"  [Parser] Parse THẤT BẠI: {e}")
        raise ValueError(f"JSON parse failed [{context}]: {e}")

async def init_world_bible(
        description: str,
        genre: str,
        art_style: str,
        protagonist_name: str,
        protagonist_description: str = "",
        target_chapters: int = 8,
) -> WorldBible:
    print("Đang khởi tạo thế giới truyện...")
    user_prompt = WORLD_BIBLE_USER.format(
        description=description,
        genre=genre,
        art_style=art_style,
        protagonist_name=protagonist_name,
        protagonist_description=protagonist_description or "Ngoại hình tùy ý sáng tạo",
        target_chapters=target_chapters,
    )

    data = await _call_gemini_json(WORLD_BIBLE_SYSTEM, user_prompt, log_name="world_bible", context="world_bible")

    story_id = str(uuid.uuid4())[:8]
    bible = WorldBible(
        story_id=story_id,
        title=data.get("title", "Không tên"),
        genre=genre,
        art_style=art_style,
        tone=data.get("tone", "dramatic"),
        setting=data.get("setting", ""),
        protagonist=Character(
            name=data.get("protagonist", {}).get("name", protagonist_name),
            role="protagonist",
            appearance=data.get("protagonist", {}).get("appearance", ""),
            sd_anchor=data.get("protagonist", {}).get("sd_anchor", ""),
        ),
        side_characters=[
            Character(name=c.get("name", ""), role=c.get("role", ""), appearance=c.get("appearance", ""), sd_anchor=c.get("sd_anchor", ""))
            for c in data.get("side_characters", [])
        ],
        lore=data.get("lore", ""),
        target_chapters=target_chapters,
    )
    return bible

# ---------------------------------------------------------------------------
# CHAPTER GENERATION
# ---------------------------------------------------------------------------

async def generate_chapter(
        session: StorySession,
        chosen_option: str = "",
) -> Chapter:
    bible = session.world_bible
    prev_chaps = session.chapters or []
    next_num = len(prev_chaps) + 1

    bible_json = {
        "title": bible.title,
        "genre": bible.genre,
        "tone": bible.tone,
        "setting": bible.setting,
        "story_id": bible.story_id,
        "protagonist": {
            "name": bible.protagonist.name,
            "appearance": bible.protagonist.appearance,
            "sd_anchor": bible.protagonist.sd_anchor,
        },
        "side_characters": [
            {"name": c.name, "role": c.role, "sd_anchor": c.sd_anchor}
            for c in bible.side_characters
        ],
        "lore": bible.lore,
    }

    last_chapter_text = ""
    if prev_chaps:
        last = prev_chaps[-1]
        last_chapter_text = f"Chương {last.chapter_number} — {last.title}\n{last.narrative_text}\nKết chương: {last.chapter_ending}"

    summaries = []
    for c in prev_chaps[:-1]:
        s = c.summary or (", ".join(c.key_events) if c.key_events else "")
        summaries.append(f"Chương {c.chapter_number}: {s}")

    print(f"\nĐang sinh chương {next_num} (All-in-One)...")
    try:
        user_prompt = CHAPTER_USER.format(
            world_bible_json=json.dumps(bible_json, ensure_ascii=False, indent=2),
            chapter_summaries="\n\n".join(summaries),
            last_chapter_text=last_chapter_text or "(Chưa có — đây là chương 1)",
            chosen_option=chosen_option or "Bắt đầu câu chuyện",
            next_num=next_num,
        )

        data = await _call_gemini_json(CHAPTER_SYSTEM, user_prompt, log_name=f"chapter_{next_num}_all", context=f"chapter_{next_num}")
        print(f"  [Chapter] AI sinh xong và parse JSON thành công.")

        narrative_text = data.get("narrative_text", "")
        mp_data = data.get("manga_page", {})
        manga_page = MangaPage(
            layout=mp_data.get("layout", "2x2"),
            panels=[
                MangaPanel(
                    position=p.get("position", ""),
                    scene=p.get("scene", ""),
                    focus=p.get("focus", ""),
                    mood=p.get("mood", "")
                )
                for p in mp_data.get("panels", [])
            ] if mp_data.get("panels") else [],
            dominant_mood=mp_data.get("dominant_mood", "dramatic"),
        )

        chapter = Chapter(
            chapter_number=next_num,
            title=data.get("chapter_title", f"Chương {next_num}"),
            choice_that_led_here=chosen_option,
            narrative_text=narrative_text,
            manga_page=manga_page,
            chapter_ending=data.get("chapter_ending", ""),
            key_events=data.get("key_events") or [],
            state_changes=data.get("state_changes") or {},
            next_options=[
                NextOption(
                    id=opt.get("id", ""),
                    text=opt.get("text", ""),
                    hint=opt.get("hint", ""),
                    consequence_type=opt.get("consequence_type", "")
                )
                for opt in data.get("next_options", [])
            ] if data.get("next_options") else [],
        )
        return chapter
    except Exception as e:
        print(f"!!! LỖI TẠI generate_chapter: {e}")
        traceback.print_exc()
        raise

async def generate_manga_page(chapter: Chapter, bible: WorldBible, save_dir: str = OUTPUT_DIR) -> Optional[str]:
    os.makedirs(save_dir, exist_ok=True)
    manga_page_dict = {
        "layout": chapter.manga_page.layout,
        "dominant_mood": chapter.manga_page.dominant_mood,
        "panels": [
            {"position": p.position, "scene": p.scene, "focus": p.focus, "mood": p.mood}
            for p in chapter.manga_page.panels
        ],
    }
    bible_dict = {
        "story_id": bible.story_id,
        "protagonist": {"sd_anchor": bible.protagonist.sd_anchor},
        "side_characters": [{"name": c.name, "sd_anchor": c.sd_anchor} for c in bible.side_characters],
    }
    sd_params = build_sd_prompt(manga_page_dict, bible_dict, bible.art_style)
    filename = f"chapter_{chapter.chapter_number:02d}_{uuid.uuid4().hex[:6]}.png"
    path = os.path.join(save_dir, filename)

    print(f"  [Manga] Đang gọi HuggingFace API (Model: {cfg.get('HF_IMAGE_MODEL')})...")
    try:
        prompt = sd_params["prompt"]
        print(f"  [Manga] Prompt: {prompt[:100]}...")
        image = await hf_client.text_to_image(
            prompt,
            model=cfg.get("HF_IMAGE_MODEL"),
            negative_prompt=sd_params["negative_prompt"],
            width=sd_params["width"],
            height=sd_params["height"],
        )
        print(f"  [Manga] Sinh ảnh thành công, đang lưu vào {path}...")
        image.save(path)
        # Return relative path for UI
        return f"outputs/{filename}"
    except Exception as e:
        print(f"Lỗi sinh ảnh: {e}")
        return None

async def summarize_chapter(chapter: Chapter) -> str:
    user_prompt = SUMMARIZE_USER.format(
        chapter_text=f"Chương {chapter.chapter_number} — {chapter.title}\n{chapter.narrative_text}\nKết thúc: {chapter.chapter_ending}"
    )
    try:
        data = await _call_gemini_json(SUMMARIZE_SYSTEM, user_prompt, log_name="summarize", context="summarize")
        lines = data.get("summary") or chapter.key_events or []
        return "\n".join(f"- {line}" for line in lines)
    except Exception:
        fallback = chapter.key_events or []
        return "\n".join(f"- {e}" for e in fallback)

# ---------------------------------------------------------------------------
# ASYNC STORY ENGINE
# ---------------------------------------------------------------------------

class StoryEngine:
    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        self.session: Optional[StorySession] = None

    async def load_story(self, story_id: str) -> bool:
        if not self.db: return False
        
        # Load World Bible
        from src.schemas.story import Character, WorldBible, Chapter, MangaPage, MangaPanel, NextOption, StorySession
        
        res = await self.db.execute(select(WorldBibleTable).where(WorldBibleTable.id == story_id))
        db_bible = res.scalars().first()
        if not db_bible: return False
        
        lore = db_bible.lore or {}
        side_chars = [
            Character(**c) for c in lore.get("side_characters", [])
        ]
        
        bible = WorldBible(
            story_id=db_bible.id,
            title=db_bible.title,
            genre=db_bible.genre,
            art_style=db_bible.art_style,
            tone=lore.get("tone", "dramatic"),
            setting=lore.get("setting", ""),
            protagonist=Character(
                name=db_bible.protagonist_name,
                role="protagonist",
                appearance=db_bible.protagonist_description,
                sd_anchor=lore.get("protagonist_sd_anchor", "")
            ),
            side_characters=side_chars,
            lore=lore.get("lore", ""),
            target_chapters=8 # Default if not found
        )
        
        # Load Chapters
        from src.database.models import ChapterTable
        res_chap = await self.db.execute(
            select(ChapterTable).where(ChapterTable.story_id == story_id).order_by(ChapterTable.chapter_number)
        )
        db_chaps = res_chap.scalars().all()
        
        chapters = []
        for c in db_chaps:
            opts = [NextOption(**opt) for opt in (c.options or [])]
            
            # Reconstruct MangaPage
            mp_data = getattr(c, "manga_page_data", None) or {}
            if mp_data:
                mp = MangaPage(
                    layout=mp_data.get("layout", "1x1"),
                    panels=[MangaPanel(**p) for p in mp_data.get("panels", [])],
                    dominant_mood=mp_data.get("dominant_mood", "dramatic")
                )
            else:
                mp = MangaPage(layout="1x1", panels=[], dominant_mood="dramatic")
            
            chapters.append(Chapter(
                chapter_number=c.chapter_number,
                title=c.title,
                choice_that_led_here=getattr(c, "choice_that_led_here", "") or "",
                narrative_text=c.narrative_text,
                manga_page=mp,
                chapter_ending=getattr(c, "chapter_ending", "") or "",
                key_events=getattr(c, "key_events", []) or [],
                state_changes=getattr(c, "state_changes", {}) or {},
                next_options=opts,
                image_path=c.image_path,
                summary=c.summary
            ))
            
        self.session = StorySession(world_bible=bible, chapters=chapters)
        return True

    async def start_story(
            self,
            description: str,
            genre: str = "dark_fantasy",
            art_style: str = "anime",
            protagonist_name: str = "Kael",
            protagonist_description: str = "",
            target_chapters: int = 8,
            user_id: Optional[str] = None,
            progress_callback: Optional[Callable] = None,
    ) -> Chapter:
        if progress_callback: progress_callback(0.1, desc="🕯️ Đang khởi tạo thế giới...")
        bible = await init_world_bible(description, genre, art_style, protagonist_name, protagonist_description, target_chapters)
        
        self.session = StorySession(world_bible=bible)

        if progress_callback: progress_callback(0.3, desc="✍️ Đang dệt nên chương đầu tiên...")
        chapter = await generate_chapter(self.session, chosen_option="")

        if progress_callback: progress_callback(0.6, desc="🎨 Đang vẽ manga và tóm tắt...")
        # Chạy song song vẽ ảnh và tóm tắt
        img_task = asyncio.create_task(generate_manga_page(chapter, bible))
        sum_task = asyncio.create_task(summarize_chapter(chapter))
        
        chapter.image_path, chapter.summary = await asyncio.gather(img_task, sum_task)
        
        if self.session and self.session.chapters is not None:
            self.session.chapters.append(chapter)

        if self.db:
            await self._save_to_db(bible, self.session, chapter, user_id=user_id)

        return chapter

    async def next_chapter(self, chosen_option_text: str, progress_callback: Optional[Callable] = None) -> Chapter:
        if not self.session:
            raise RuntimeError("Chưa có story session.")

        if progress_callback: progress_callback(0.2, desc=" Đang viết tiếp câu chuyện...")
        chapter = await generate_chapter(self.session, chosen_option=chosen_option_text)

        if progress_callback: progress_callback(0.6, desc=" Đang vẽ manga và tóm tắt...")
        # Chạy song song vẽ ảnh và tóm tắt
        img_task = asyncio.create_task(generate_manga_page(chapter, self.session.world_bible))
        sum_task = asyncio.create_task(summarize_chapter(chapter))
        
        chapter.image_path, chapter.summary = await asyncio.gather(img_task, sum_task)
        
        if self.session and self.session.chapters is not None:
            self.session.chapters.append(chapter)

        if self.db and self.session and self.session.world_bible:
            await self._save_chapter_to_db(self.session.world_bible.story_id, chapter)

        return chapter

    async def _save_to_db(self, bible: WorldBible, session: StorySession, chapter: Chapter, user_id: Optional[str] = None):
        if not self.db: return
        db_bible = WorldBibleTable(
            id=bible.story_id,
            user_id=user_id,
            title=bible.title,
            genre=bible.genre,
            art_style=bible.art_style,
            protagonist_name=bible.protagonist.name,
            protagonist_description=bible.protagonist.appearance,
            lore={"side_characters": [asdict(c) for c in bible.side_characters], "setting": bible.setting, "lore": bible.lore}
        )
        self.db.add(db_bible)

        db_story = StoryTable(
            id=bible.story_id,
            world_bible_id=bible.story_id,
            target_chapters=bible.target_chapters
        )
        self.db.add(db_story)
        await self._save_chapter_to_db(bible.story_id, chapter)
        await self.db.commit()

    async def _save_chapter_to_db(self, story_id: str, chapter: Chapter):
        if not self.db: return
        db_chapter = ChapterTable(
            id=str(uuid.uuid4())[:8],
            story_id=story_id,
            chapter_number=chapter.chapter_number,
            title=chapter.title,
            narrative_text=chapter.narrative_text,
            image_path=chapter.image_path,
            summary=chapter.summary,
            choice_that_led_here=chapter.choice_that_led_here,
            chapter_ending=chapter.chapter_ending,
            key_events=chapter.key_events,
            state_changes=chapter.state_changes,
            manga_page_data=asdict(chapter.manga_page) if chapter.manga_page else None,
            options=[asdict(opt) for opt in chapter.next_options]
        )
        self.db.add(db_chapter)
        await self.db.commit()
        print("  [DB] Đã lưu chapter và commit thành công.")

    @property
    def story_title(self) -> str:
        return self.session.world_bible.title if self.session and self.session.world_bible else ""

    @property
    def is_finished(self) -> bool:
        if not self.session or not self.session.world_bible: return False
        return len(self.session.chapters or []) >= (self.session.world_bible.target_chapters or 8)

    def get_chapter_history(self) -> list[dict]:
        if not self.session or not self.session.chapters: return []
        return [{"number": c.chapter_number, "title": c.title, "summary": c.summary or ""} for c in self.session.chapters]

    async def export_to_pdf(self) -> str:
        """Xuất toàn bộ câu chuyện ra file PDF (Text + Ảnh)."""
        if not self.session or not self.session.world_bible:
            raise RuntimeError("Không có dữ liệu để xuất PDF.")

        bible = self.session.world_bible
        chapters = self.session.chapters or []
        
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_margins(left=15, top=15, right=15)
        effective_w = 210 - 30  # A4 width 210mm - 15mm*2 margins
        
        # Font handling cho tiếng Việt (Sử dụng NotoSans)
        font_dir = os.path.join(os.path.dirname(__file__), "..", "ui", "static", "fonts")
        os.makedirs(font_dir, exist_ok=True)
        font_path = os.path.join(font_dir, "NotoSans-Regular.ttf")
        
        # Tải font nếu chưa có hoặc file lỗi (kích thước quá nhỏ)
        is_font_valid = os.path.exists(font_path) and os.path.getsize(font_path) > 100000
        if not is_font_valid:
            # Danh sách URL dự phòng để tránh lỗi 404
            _TTS_URL = "https://api.hypereal.tech/api/v1/audio/generate"
            urls = [
                "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSans/NotoSans-Regular.ttf",
                "https://github.com/google/fonts/raw/main/ofl/notosans/NotoSans-Regular.ttf",
                "https://raw.githubusercontent.com/openmaptiles/fonts/master/fonts/noto-sans/NotoSans-Regular.ttf"
            ]
            success = False
            for url in urls:
                try:
                    r = requests.get(url, timeout=20)
                    if r.status_code == 200 and len(r.content) > 100000:
                        with open(font_path, "wb") as f: f.write(r.content)
                        logging.info(f"Đã tải font NotoSans thành công từ {url}")
                        success = True
                        break
                    else:
                        logging.warning(f"Thử tải font từ {url} thất bại: Status {r.status_code}")
                except Exception as e:
                    logging.error(f"Lỗi tải từ {url}: {e}")
            
            if not success:
                logging.error("Tất cả nguồn tải font đều thất bại.")
            
        if os.path.exists(font_path) and os.path.getsize(font_path) > 100000:
            pdf.add_font("NotoSans", "", font_path)
            pdf.set_font("NotoSans", size=12)
            font_family = "NotoSans"
        else:
            pdf.set_font("Arial", size=12)
            font_family = "Arial"

        pdf.add_page()
        pdf.set_font(font_family, size=22)
        pdf.multi_cell(effective_w, 12, f"TRUYEN: {self.story_title.upper()}", align='C', new_x="LMARGIN", new_y="NEXT")
        pdf.set_font(font_family, size=13)
        pdf.multi_cell(effective_w, 8, f"The loai: {bible.genre} | Phong cach: {bible.art_style}", align='C', new_x="LMARGIN", new_y="NEXT")
        pdf.ln(10)
        pdf.set_font(font_family, size=12)
        pdf.multi_cell(effective_w, 8, f"Nhan vat chinh: {bible.protagonist.name}", new_x="LMARGIN", new_y="NEXT")
        pdf.multi_cell(effective_w, 8, f"Mo ta: {bible.protagonist.appearance[:200]}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(10)

        for chapter in chapters:
            pdf.add_page()
            pdf.set_font(font_family, size=16)
            pdf.multi_cell(effective_w, 10, f"Chuong {chapter.chapter_number}: {chapter.title}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(4)
            
            if chapter.image_path:
                # image_path is relative "outputs/filename.png"
                img_full_path = os.path.join(os.path.dirname(__file__), "..", chapter.image_path)
                if os.path.exists(img_full_path):
                    try:
                        pdf.image(img_full_path, x=15, w=effective_w)
                        pdf.ln(5)
                    except Exception as e:
                        logging.warning(f"Loi them anh vao PDF: {e}")

            pdf.set_font(font_family, size=11)
            pdf.multi_cell(effective_w, 7, chapter.narrative_text, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(8)
            
            if chapter.chapter_ending:
                pdf.set_font(font_family, size=10)
                pdf.multi_cell(effective_w, 6, f"Ket chuong: {chapter.chapter_ending}", new_x="LMARGIN", new_y="NEXT")

        export_dir = os.path.join(os.path.dirname(__file__), "..", "ui", "static", "exports")
        os.makedirs(export_dir, exist_ok=True)
        file_path = os.path.join(export_dir, f"story_{self.session.world_bible.story_id}.pdf")
        pdf.output(file_path)
        return file_path