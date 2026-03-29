import gradio as gr
from src.models.db import init_db

# Import các thành phần modular
from src.ui.styles import CSS, GALAXY_HTML
from src.ui.components import _sidebar_html, _chapter_to_markdown, _options_choices
from src.ui.handlers import (
    engine,
    on_start_story,
    on_option_select,
    on_next_chapter,
    on_export_pdf,
    on_tts_read,
)

FORCE_DARK_JS = """
function() {
    document.documentElement.classList.add('dark');
    document.body.classList.add('dark');
}
"""

with gr.Blocks(
    title="GenStory — Interactive Visual Novel",
    css=CSS,
    theme=gr.themes.Base(),
    js=FORCE_DARK_JS
) as app:

    # Khởi tạo Galaxy Canvas & Header
    gr.HTML(GALAXY_HTML)

    gr.HTML("""
    <div style="text-align:center; padding:52px 0 36px; position:relative; z-index:2;">
      <h1 style="
        font-family:'Cinzel',serif;
        font-size:clamp(36px,6vw,64px);
        font-weight:900;
        margin:0;
        background: linear-gradient(135deg, #C084FC 0%, #F472B6 45%, #67E8F9 100%);
        -webkit-background-clip:text;
        -webkit-text-fill-color:transparent;
        background-clip:text;
        letter-spacing:4px;
        filter:drop-shadow(0 0 24px rgba(192,132,252,0.5));
      ">GENSTORY</h1>
      <p style="
        color:#C084FC;
        font-size:13px;
        margin-top:12px;
        font-weight:600;
        letter-spacing:4px;
        text-transform:uppercase;
        opacity:0.85;
      ">✦ AI Interactive Visual Novel ✦</p>
    </div>
    """)

    with gr.Column(visible=True, elem_classes="glass-card") as setup_col:
        with gr.Row():
            with gr.Column(scale=2):
                description = gr.Textbox(
                    label="Mô tả câu chuyện",
                    placeholder="Ví dụ: Bạn là một pháp sư trẻ bị trục xuất khỏi học viện...",
                    lines=3,
                )
            with gr.Column(scale=1):
                protagonist_name = gr.Textbox(
                    label="Tên nhân vật chính",
                    placeholder="Ví dụ: Kael",
                )
                protagonist_description = gr.Textbox(
                    label="Mô tả nhân vật chính",
                    placeholder="Ví dụ: Tóc bạch kim, mắt tím, mang vết sẹo...",
                    lines=2,
                )
                target_chapters = gr.Slider(
                    label="Độ dài (số chương xấp xỉ)",
                    minimum=4, maximum=20, value=8, step=1,
                )

        with gr.Row():
            genre = gr.Dropdown(
                label="Thể loại",
                choices=[
                    "dark_fantasy",
                    "fantasy",
                    "isekai",
                    "thriller",
                    "romance",
                    "shonen",
                    "seinen",
                    "sci_fi",
                    "harem",
                    "slice_of_life",
                    "adventure",
                    "mystery",
                    "action",
                    "supernatural",
                    "historical",
                    "post_apocalyptic",
                    "psychological",
                    "school",
                    "comedy"
                ],
                value="dark_fantasy",
            )
            art_style = gr.Dropdown(
                label="Phong cách ảnh",
                choices=[
                    "anime",
                    "manga_bw",
                    "webtoon",
                    "dark_art",
                    "realistic_anime",
                    "semi_realistic",
                    "comic_book",
                    "watercolor",
                    "pixel_art",
                    "cyberpunk",
                    "fantasy_art",
                    "ghibli_style",
                    "manhwa_style",
                    "sketch",
                    "oil_painting"
                ],
                value="anime",
            )

        start_btn = gr.Button("✨ Bắt đầu hành trình ✨", variant="primary", size="lg")
        status_msg_start = gr.Markdown("Sẵn sàng cho cuộc phiêu lưu của bạn...", elem_id="status-msg-start")

    with gr.Column(visible=False) as reader_col:
        story_title_md = gr.Markdown("")

        with gr.Row():
            # Cột chính (Nội dung truyện)
            with gr.Column(scale=3):
                with gr.Group():
                    chapter_md  = gr.HTML("", elem_id="chapter-content")
                    manga_image = gr.Image(
                        label="Trang manga",
                        show_label=False,
                        height=600,
                        elem_id="manga-image"
                    )

                with gr.Column(elem_classes="glass-card"):
                    options_radio = gr.Radio(
                        label="Bạn sẽ làm gì tiếp theo?",
                        choices=[],
                        interactive=True,
                    )
                    status_msg_next = gr.Markdown("", elem_id="status-msg-next")
                    next_btn = gr.Button("Tiếp tục câu chuyện →", variant="primary", size="lg")

            # Sidebar (Thông tin bổ trợ + Công cụ)
            with gr.Column(scale=1, elem_classes="glass-card"):
                sidebar_html = gr.HTML("")
                
                gr.HTML("<hr style='border-color: var(--border); margin: 20px 0;'>")
                gr.HTML("<div style='font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:.15em; color:var(--txt-3); margin-bottom:14px;'>✦ Công cụ</div>")
                
                tts_btn  = gr.Button("ĐỌC CHƯƠNG NÀY", variant="secondary")
                tts_audio = gr.Audio(
                    label="Giọng đọc AI",
                    type="filepath",
                    visible=False,
                    autoplay=True,
                )
                
                export_btn  = gr.Button("TẢI PDF TRUYỆN", variant="secondary", elem_classes="export-btn")
                export_file = gr.File(label="File PDF", visible=False)

    start_btn.click(
        fn=on_start_story,
        inputs=[description, genre, art_style, protagonist_name, protagonist_description, target_chapters],
        outputs=[setup_col, reader_col, chapter_md, manga_image,
                 options_radio, story_title_md, sidebar_html, status_msg_start],
    )

    options_radio.change(
        fn=on_option_select,
        inputs=[options_radio],
        outputs=[],
    )

    next_btn.click(
        fn=on_next_chapter,
        inputs=[options_radio],
        outputs=[chapter_md, manga_image, options_radio, sidebar_html, status_msg_next],
    )

    tts_btn.click(
        fn=on_tts_read,
        inputs=[],
        outputs=[tts_audio],
    ).then(
        fn=lambda: gr.update(visible=True),
        inputs=[],
        outputs=[tts_audio],
    )

    export_btn.click(
        fn=on_export_pdf,
        inputs=[],
        outputs=[export_file]
    ).then(
        fn=lambda: gr.update(visible=True),
        inputs=[],
        outputs=[export_file]
    )

    app.load(init_db)

if __name__ == "__main__":
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
    )