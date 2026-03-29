import gradio as gr
from src.models.genstory_engine import StoryEngine
from src.models.db import AsyncSessionLocal
from src.ui.components import _chapter_to_markdown, _options_choices, _sidebar_html

# Khởi tạo engine toàn cục cho phiên làm việc hiện tại
engine = StoryEngine()
_selected_option: dict = {"text": "", "id": ""}

import requests as _http
import tempfile
import os as _os
from dotenv import load_dotenv as _load_dotenv
_load_dotenv()

_TTS_URL = "https://hypereal.tech/api/v1/audio/generate"
_TTS_KEY = _os.getenv("TTS_KEY", "")

async def on_export_pdf():
    try:
        if not engine.session:
            return None
        file_path = await engine.export_to_pdf()
        return file_path
    except Exception as e:
        print(f"Lỗi xuất PDF: {e}")
        return None

def on_tts_read():
    if not _TTS_KEY:
        print("TTS_KEY chưa được cấu hình trong .env")
        return None
    try:
        if not engine.session or not engine.session.latest_chapter:
            return None
        text = engine.session.latest_chapter.narrative_text[:1500]
        resp = _http.post(
            _TTS_URL,
            json={"model": "audio-tts", "input": {"text": text, "format": "mp3"}},
            headers={"Authorization": f"Bearer {_TTS_KEY}", "Content-Type": "application/json"},
            timeout=30,
        )
        if resp.status_code != 200:
            print(f"TTS API lỗi {resp.status_code}: {resp.text[:200]}")
            return None
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tmp.write(resp.content)
        tmp.close()
        return tmp.name
    except Exception as e:
        print(f"Lỗi TTS: {e}")
        return None

async def on_start_story(description, genre, art_style, protagonist_name, protagonist_description, target_chapters, progress=gr.Progress()):
    """Người dùng nhấn 'Bắt đầu hành trình'."""
    if not description.strip():
        yield (
            gr.update(visible=True),   # setup_col
            gr.update(visible=False),  # reader_col
            "", None, gr.update(choices=[], value=None), "", "",
            "Vui lòng nhập mô tả câu chuyện."
        )
        return

    try:
        if progress: progress(0, desc="Đang khởi tạo thế giới...")
        yield (gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), "Đang bắt đầu...")

        async with AsyncSessionLocal() as db:
            engine.db = db
            chapter = await engine.start_story(
                description=description,
                genre=genre,
                art_style=art_style,
                protagonist_name=protagonist_name or "Kael",
                protagonist_description=protagonist_description or "",
                target_chapters=int(target_chapters),
                progress_callback=progress,
            )

        yield (
            gr.update(visible=False),
            gr.update(visible=True),
            _chapter_to_markdown(chapter),
            chapter.image_path,
            gr.update(choices=_options_choices(chapter), value=None),
            f"### {engine.story_title}",
            _sidebar_html(engine),
            "Hoàn thành chương 1!"
        )
    except Exception as e:
        yield (
            gr.update(visible=True),
            gr.update(visible=False),
            f"**Lỗi:** {e}", None, gr.update(choices=[], value=None), "", "",
            f"Lỗi: {e}"
        )

def on_option_select(choice):
    """Người dùng chọn 1 option."""
    _selected_option["text"] = choice or ""

async def on_next_chapter(choice, progress=gr.Progress()):
    """Người dùng nhấn 'Sang chương tiếp theo'."""
    if not choice:
        yield (
            gr.update(),
            None,
            gr.update(),
            gr.update(),
            "Hãy chọn 1 lựa chọn trước.",
        )
        return

    # Tách lấy phần text của option (bỏ số thứ tự và hint)
    option_text = choice.split("·")[0].strip()
    if ". " in option_text:
        option_text = option_text.split(". ", 1)[1].strip()

    try:
        if progress: progress(0, desc=" Đang viết nội dung chương mới...")
        yield (gr.update(), gr.update(), gr.update(), gr.update(), " Đang xử lý...")

        async with AsyncSessionLocal() as db:
            engine.db = db
            chapter = await engine.next_chapter(option_text, progress_callback=progress)

        finished_msg = ""
        if engine.is_finished:
            finished_msg = "\n\n---\n** Câu chuyện đã kết thúc!**"

        yield (
            _chapter_to_markdown(chapter) + finished_msg,
            chapter.image_path,
            gr.update(
                choices=_options_choices(chapter) if not engine.is_finished else [],
                value=None,
            ),
            _sidebar_html(engine),
            f" Chương {chapter.chapter_number} đã sẵn sàng!",
        )
    except Exception as e:
        yield gr.update(), None, gr.update(), gr.update(), f"**Lỗi:** {e}"
