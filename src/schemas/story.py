"""
schemas.py — cấu trúc dữ liệu cho interactive visual novel
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Character:
    name: str
    role: str               # "protagonist" | "side"
    appearance: str         # mô tả ngoại hình tiếng Việt
    sd_anchor: str          # cố định cho SD prompt, không thay đổi


@dataclass
class WorldBible:
    story_id: str
    title: str
    genre: str              # dark_fantasy | isekai | thriller | romance | shonen
    art_style: str          # anime | manga_bw | dark_art | webtoon
    tone: str               # dramatic | lighthearted | mysterious | action
    setting: str            # mô tả thế giới
    protagonist: Character
    side_characters: list[Character]
    lore: str               # luật thế giới, hệ thống ma thuật, ...
    target_chapters: int    # xấp xỉ, không ràng buộc


@dataclass
class MangaPanel:
    position: str           # "top-left" | "top-right" | "bottom-left" | "bottom-right" | "full" | "wide-top" | "wide-bottom"
    scene: str              # mô tả scene trong panel
    focus: str              # "wide shot" | "medium shot" | "close-up" | "extreme close-up"
    mood: str               # "tense" | "action" | "calm" | "emotional" | "mysterious"


@dataclass
class MangaPage:
    layout: str             # "2x2" | "1top-2bottom" | "2top-1bottom" | "3x1" | "full"
    panels: list[MangaPanel]
    dominant_mood: str


@dataclass
class NextOption:
    id: str                 # "A" | "B" | "C" | "D"
    text: str               # hiển thị cho người dùng, < 15 từ
    hint: str               # gợi ý hệ quả mơ hồ
    consequence_type: str   # "combat" | "dialogue" | "exploration" | "stealth" | "magic"


@dataclass
class Chapter:
    chapter_number: int
    title: str
    choice_that_led_here: str           # option người dùng đã chọn (rỗng với chap 1)
    narrative_text: str                  # full text, xưng "bạn", ~300-400 từ
    manga_page: MangaPage
    chapter_ending: str                  # cliffhanger kết chương
    key_events: list[str]               # 3-5 bullets, dùng để tóm tắt cho chap sau
    state_changes: dict                  # location, companions, items, revelations
    next_options: list[NextOption]
    image_path: Optional[str] = None    # đường dẫn ảnh sau khi SD sinh xong
    summary: Optional[str] = None       # tóm tắt ngắn, sinh sau khi lưu


@dataclass
class StorySession:
    """Toàn bộ state của 1 session người dùng đang chơi"""
    world_bible: WorldBible
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