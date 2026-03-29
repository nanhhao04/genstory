# Thư mục UI — Giao diện Người dùng Gradio

Thư mục này chịu trách nhiệm hiển thị giao diện và xử lý các tương tác trực tiếp của người dùng.

## Các tệp tin chính

### 1. app.py (Ứng dụng Gradio chính)
Đây là tệp điều khiển toàn bộ giao diện của GenStory:
- **CSS**: Biến giao diện từ mặc định sang chủ đề "Nebula" mang hơi hướng vũ trụ, sử dụng Glassmorphism và màu sắc Gradient sống động.
- **on_start_story**: Hàm xử lý sự kiện khi người dùng nhấn "Bắt đầu hành trình".
- **on_next_chapter**: Hàm xử lý sự kiện khi chọn hành động mới để sang chương tiếp theo.
- **on_export_pdf**: Hàm kích hoạt quá trình tạo và cung cấp link tải PDF.
- **sidebar_html**: Sinh bố cục thông tin nhân vật và lịch sử hành trình bên thanh sidebar.
