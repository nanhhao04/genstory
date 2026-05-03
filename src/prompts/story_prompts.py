# WORLD BIBLE — sinh 1 lần khi bắt đầu

WORLD_BIBLE_SYSTEM = """
Bạn là nhà văn sáng tạo thế giới cho visual novel manga tương tác.
Người dùng sẽ đóng vai nhân vật chính — luôn xưng "bạn" khi kể chuyện.
Chỉ trả về JSON thuần, không có markdown, không có giải thích.
""".strip()

WORLD_BIBLE_USER = """
Từ ý tưởng sau, hãy xây dựng world bible đầy đủ:

Mô tả cốt truyện: {description}
Thể loại: {genre}
Phong cách ảnh: {art_style}
Tên nhân vật chính: {protagonist_name}
Mô tả nhân vật chính: {protagonist_description}
Độ dài: khoảng {target_chapters} chương

Trả về JSON với cấu trúc sau:
{{
  "title": "Tên truyện hấp dẫn",
  "tone": "dramatic|lighthearted|mysterious|action",
  "setting": "Mô tả thế giới, thời đại, bối cảnh (2-3 câu)",
  "protagonist": {{
    "name": "{protagonist_name}",
    "appearance": "Mô tả ngoại hình chi tiết tiếng Việt dựa trên: {protagonist_description}",
    "sd_anchor": "english description for SD: hair, eyes, outfit, body type — sẽ dùng trong mọi ảnh",
    "background": "Xuất thân, động lực (2-3 câu)"
  }},
  "side_characters": [
    {{
      "name": "Tên",
      "role": "Vai trò trong câu chuyện",
      "appearance": "Mô tả ngoại hình",
      "sd_anchor": "english SD description"
    }}
  ],
  "lore": "Luật thế giới, hệ thống ma thuật/công nghệ, phe phái (3-4 câu)",
  "opening_hook": "Câu mở đầu chương 1 gây hook mạnh cho người đọc"
}}

Lưu ý:
- sd_anchor phải bằng tiếng Anh, ngắn gọn, đặc trưng nhận dạng nhân vật
- side_characters: 4-10 nhân vật phụ quan trọng
- tone phải phù hợp với thể loại {genre}
""".strip()



CHAPTER_NARRATIVE_SYSTEM = """
Bạn là nhà văn kể chuyện cho visual novel manga tương tác.
Luôn viết theo góc nhìn thứ hai — xưng "bạn".
Chỉ trả về nội dung câu chuyện (narrative text), không có JSON, không có giải thích.
Viết khoảng 300-400 từ, chia thành 3-4 đoạn văn.
""".strip()

CHAPTER_NARRATIVE_USER = """
=== WORLD BIBLE ===
{world_bible_json}

=== TÓM TẮT HÀNH TRÌNH ({n_prev} chương trước) ===
{chapter_summaries}

=== CHƯƠNG {prev_num} VỪD ĐỌC ===
{last_chapter_text}

=== LỰA CHỌN NGƯỜI DÙNG ===
"{chosen_option}"

Hãy viết tiếp Chương {next_num}. Bắt đầu bằng hệ quả trực tiếp của lựa chọn "{chosen_option}".
Kết thúc chương bằng một câu cliffhanger kịch tính.
""".strip()

CHAPTER_METADATA_SYSTEM = """
Bạn là trợ lý biên tập cho visual novel. Nhiệm vụ của bạn là trích xuất metadata từ nội dung chương truyện.
Chỉ trả về JSON thuần, không có markdown, không có giải thích.
""".strip()

CHAPTER_METADATA_USER = """
Dựa trên nội dung chương {next_num} sau đây:

"{narrative_text}"

Hãy sinh metadata JSON:
{{
  "chapter_title": "Tên chương hấp dẫn",
  "manga_page": {{
    "layout": "2x2|1top-2bottom|2top-1bottom|3x1|full",
    "panels": [
      {{
        "position": "top-left|top-right|bottom-left|bottom-right|wide-top|wide-bottom|full",
        "scene": "Mô tả scene cho SD (tiếng Anh). Phải bao gồm cả bối cảnh vật lý của scene.",
        "focus": "wide shot|medium shot|close-up|extreme close-up",
        "mood": "tense|action|calm|emotional|mysterious|dramatic"
      }}
    ],
    "dominant_mood": "dark|action|emotional|mysterious|dramatic|hopeful"
  }},
  "chapter_ending": "Trích dẫn chính xác câu cliffhanger cuối chương",
  "key_events": ["Sự kiện 1", "Sự kiện 2", "Sự kiện 3"],
  "state_changes": {{
    "location": "Vị trí hiện tại",
    "companions": ["Tên đồng hành"],
    "new_info": ["Bí mật mới"]
  }},
  "next_options": [
    {{"id": "A", "text": "Lựa chọn 1 (<12 từ)", "hint": "Gợi ý", "consequence_type": "..."}},
    {{"id": "B", "text": "...", "hint": "...", "consequence_type": "..."}},
    {{"id": "C", "text": "...", "hint": "...", "consequence_type": "..."}},
    {{"id": "D", "text": "...", "hint": "...", "consequence_type": "..."}}
  ]
}}
""".strip()

# ---------------------------------------------------------------------------
# CHAPTER GENERATION — system and user prompts for generating a new chapter
# ---------------------------------------------------------------------------

CHAPTER_SYSTEM = """
Bạn là nhà văn sáng tạo cốt truyện và trợ lý biên tập cho visual novel manga.
Nhiệm vụ của bạn là viết nội dung chương truyện và đồng thời trích xuất các metadata cần thiết.

CHỈ TRẢ VỀ JSON THUẦN, KHÔNG CÓ MARKDOWN, KHÔNG CÓ GIẢI THÍCH.
""".strip()

CHAPTER_USER = """
Dựa trên World Bible và lịch sử câu chuyện, hãy viết Chương {next_num}.

=== WORLD BIBLE ===
{world_bible_json}

=== TÓM TẮT CÁC CHƯƠNG TRƯỚC ===
{chapter_summaries}

=== CHƯƠNG GẦN NHẤT ===
{last_chapter_text}

=== LỰA CHỌN CỦA NGƯỜI DÙNG ===
"{chosen_option}"

Yêu cầu nội dung chương:
- Viết khoảng 300-400 từ, chia 3-4 đoạn văn.
- Xưng "bạn" (góc nhìn thứ hai).
- Kết thúc bằng 1 câu cliffhanger mạnh.

Trả về JSON theo cấu trúc:
{{
  "chapter_title": "Tên chương",
  "narrative_text": "Nội dung câu chuyện đầy đủ",
  "manga_page": {{
    "layout": "2x2|1top-2bottom|2top-1bottom|3x1|full",
    "panels": [
      {{
        "position": "top-left|top-right|...",
        "scene": "Detailed scene description in English for Stable Diffusion",
        "focus": "wide shot|medium shot|close-up",
        "mood": "..."
      }}
    ],
    "dominant_mood": "..."
  }},
  "chapter_ending": "Câu cliffhanger cuối",
  "key_events": ["Sự kiện 1", "Sự kiện 2"],
  "state_changes": {{ "location": "...", "companions": [], "new_info": [] }},
  "next_options": [
    {{ "id": "A", "text": "Lựa chọn 1", "hint": "Gợi ý", "consequence_type": "..." }}
  ]
}}
""".strip()

# ---------------------------------------------------------------------------
# CHAPTER SUMMARIZER — tóm tắt chương cũ để tiết kiệm token
# ---------------------------------------------------------------------------

SUMMARIZE_SYSTEM = """
Tóm tắt ngắn gọn nội dung chương truyện.
Chỉ trả về JSON thuần.
""".strip()

SUMMARIZE_USER = """
Tóm tắt chương sau thành đúng 4-5 bullet points.
Chỉ giữ: sự kiện quan trọng, thay đổi nhân vật, địa điểm, bí mật phát hiện.
Bỏ: cảm xúc chi tiết, hội thoại dài, mô tả phong cảnh.

{chapter_text}

Trả về: {{"summary": ["bullet 1", "bullet 2", "bullet 3", "bullet 4"]}}
""".strip()


# ---------------------------------------------------------------------------
# SD PROMPT BUILDER
# ---------------------------------------------------------------------------

LAYOUT_KEYWORDS = {
    "2x2":          "4-panel manga page, 2x2 grid layout, equal panels",
    "1top-2bottom": "3-panel manga page, one large panel on top, two smaller panels on bottom",
    "2top-1bottom": "3-panel manga page, two smaller panels on top, one large panel on bottom",
    "3x1":          "3-panel manga page, three horizontal panels stacked vertically",
    "full":         "single full-page manga panel",
}

MOOD_KEYWORDS = {
    "dark":       "dark atmosphere, heavy shadows, dramatic chiaroscuro lighting",
    "action":     "dynamic poses, speed lines, motion blur, kinetic energy",
    "emotional":  "soft lighting, detailed facial expressions, intimate framing",
    "mysterious": "foggy atmosphere, moonlight, long shadows, silhouettes",
    "dramatic":   "low angle shot, strong contrast, intense expressions",
    "hopeful":    "warm lighting, open space, uplifting composition",
}

ART_STYLE_KEYWORDS = {
    "anime":    "anime style, vibrant colors, clean linework, detailed shading",
    "manga_bw": "black and white manga, clean ink linework, screentone shading, no color",
    "dark_art": "dark fantasy illustration, muted colors, painterly style, atmospheric",
    "webtoon":  "webtoon style, flat clean colors, simple linework, bright palette",
}

SD_NEGATIVE = (
    "deformed, ugly, bad anatomy, extra limbs, missing limbs, "
    "blurry, low quality, watermark, text, logo, "
    "inconsistent character, wrong eye color, wrong hair color, "
    "merged panels without borders, nsfw"
)


def build_sd_prompt(manga_page: dict, world_bible: dict, art_style: str) -> dict:
    """
    Tạo SD prompt từ manga_page JSON và world bible.
    Trả về dict với prompt, negative_prompt, width, height, seed.
    """
    layout      = manga_page.get("layout", "2x2")
    dom_mood    = manga_page.get("dominant_mood", "dramatic")
    panels      = manga_page.get("panels", [])
    protagonist = world_bible.get("protagonist", {})
    anchor      = protagonist.get("sd_anchor", "")

    # Lấy sd_anchor của tất cả side chars có mặt
    side_anchors = []
    for char in world_bible.get("side_characters", []):
        # Kiểm tra xem nhân vật phụ có xuất hiện trong panels không
        char_name = char.get("name", "").lower()
        for panel in panels:
            if char_name in panel.get("scene", "").lower():
                side_anchors.append(char.get("sd_anchor", ""))
                break

    # Mô tả từng panel
    panel_descs = []
    for i, panel in enumerate(panels, 1):
        focus = panel.get("focus", "medium shot")
        scene = panel.get("scene", "")
        panel_descs.append(f"panel {i} [{focus}]: {scene}")

    # Ghép prompt
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

    # Seed cố định per story → style nhất quán toàn bộ story
    story_id    = world_bible.get("story_id", "default")
    stable_seed = abs(hash(story_id)) % (2 ** 31)

    return {
        "prompt":          prompt,
        "negative_prompt": SD_NEGATIVE,
        "width":           768,
        "height":          1024,    # tỉ lệ đứng như trang manga
        "num_inference_steps": 28,
        "guidance_scale":  7.5,
        "seed":            stable_seed,
    }