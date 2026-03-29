from src.models.genstory_engine import StoryEngine
from src.models.schemas import Chapter

def _chapter_to_markdown(chapter: Chapter) -> str:
    """Chuyển chapter thành HTML để hiển thị trong Gradio."""
    # Thay thế xuống dòng thành thẻ HTML tương ứng
    narrative_html = chapter.narrative_text.replace("\n\n", "</p><p>").replace("\n", "<br>")
    
    title_html = (
        "<div style='text-align:center; margin-bottom:34px;'>"
        f"<h2 style='font-family:Cinzel,serif; font-size:28px; font-weight:700;"
        f" color:var(--p); text-shadow:0 0 25px var(--p-glow);"
        f" letter-spacing:1.5px; margin:0;'>"
        f"Chương {chapter.chapter_number} — {chapter.title}</h2>"
        "</div>"
    )
    
    body_html = (
        f"<div style='font-family: \"Crimson Pro\", Georgia, serif; font-size:20px;"
        f" line-height:1.9; color:var(--txt-2); letter-spacing:0.012em; text-align: justify;'>"
        f"<p>{narrative_html}</p></div>"
    )
    
    divider_html = "<div style='margin:38px 0; border-top:1px solid rgba(192,132,252,0.25);'></div>"
    
    ending_html = (
        f"<div style='font-family: \"Crimson Pro\", serif; font-style:italic;"
        f" font-size:19px; color:var(--pink); text-align:right;"
        f" padding-right:10px; opacity:0.95;'>"
        f"“{chapter.chapter_ending}”</div>"
    )
    
    return "\n".join([title_html, "", body_html, "", divider_html, ending_html])

def _options_choices(chapter: Chapter) -> list[str]:
    """Trả list string cho radio buttons."""
    return [
        f"{opt.id}. {opt.text}  ·  *{opt.hint}*  [{opt.consequence_type}]"
        for opt in chapter.next_options
    ]

def _sidebar_html(engine: StoryEngine) -> str:
    """Sinh HTML sidebar nhân vật + lịch sử chương."""
    if not engine.session:
        return ""
        
    bible = engine.session.world_bible
    chars = [bible.protagonist] + bible.side_characters
    state = engine.session.latest_chapter.state_changes if engine.session.latest_chapter else {}

    char_html = "".join(
        f'<div style="margin-bottom:14px; padding: 14px; background: rgba(255,255,255,0.04); border-radius: 12px; border: 1px solid var(--border);">'
        f'<strong style="color: var(--p); font-size: 15px; letter-spacing: 0.8px;">{c.name}</strong><br>'
        f'<span style="color: var(--txt-2); font-size: 12.5px; display: block; margin-top: 8px; line-height: 1.5;">{c.appearance[:110]}...</span>'
        f'</div>'
        for c in chars
    )

    history = engine.get_chapter_history()
    hist_html = "".join(
        f'<div style="font-size:12.5px; padding:11px 14px; margin-bottom:8px; border-radius:10px; border: 1px solid var(--border); '
        f'{"background: linear-gradient(90deg, #9333EA 0%, #F472B6 100%); color: white; border: none; box-shadow: 0 4px 12px rgba(168,85,247,0.3);" if i == len(history)-1 else "background: rgba(255,255,255,0.02); color: var(--txt-3);"}">'
        f'<b>{h["number"]}</b>. {h["title"]}'
        f'</div>'
        for i, h in enumerate(history)
    )

    location = state.get("location", "Khởi đầu hành trình")
    companions = ", ".join(state.get("companions", []))

    return f"""
    <div style="font-family: 'Inter', sans-serif;">
      <div style="font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:.18em; color:var(--txt-3); margin-bottom:18px; border-bottom: 1px solid var(--border); padding-bottom: 8px;">
        ✦ Nhân vật chính diện
      </div>
      {char_html}

      <div style="font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:.18em; color:var(--txt-3); margin:28px 0 16px; border-bottom: 1px solid var(--border); padding-bottom: 8px;">
        ✦ Trạng thái hiện tại
      </div>
      <div style="background: rgba(255,255,255,0.03); padding: 16px; border-radius: 14px; border: 1px solid var(--border); margin-bottom: 28px;">
          <div style="font-size:14px; color:var(--txt-2); margin-bottom:10px; display: flex; align-items: center;">
            <span style="margin-right: 12px; color: var(--cyan);">📍</span> <b>Vị trí:</b> <span style="margin-left:6px; color:var(--cyan);">{location}</span>
          </div>
          <div style="font-size:14px; color:var(--txt-2); display: flex; align-items: center;">
            <span style="margin-right: 12px; color: var(--pink);">👥</span> <b>Đồng hành:</b> <span style="margin-left:6px;">{companions or "Độc hành"}</span>
          </div>
      </div>

      <div style="font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:.18em; color:var(--txt-3); margin-bottom:18px; border-bottom: 1px solid var(--border); padding-bottom: 8px;">
        ✦ Biên niên sử
      </div>
      <div style="max-height: 380px; overflow-y: auto; padding-right: 6px;">
        {hist_html}
      </div>
    </div>
    """
