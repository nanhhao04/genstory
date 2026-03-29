# GenStory FastAPI — Hệ thống Visual Novel AI

GenStory là một nền tảng tạo câu chuyện tương tác và visual novel sử dụng trí tuệ nhân tạo (Gemini). Hệ thống cho phép người dùng nhập mô tả thế giới, nhân vật và phong cách vẽ để AI tự động sinh cốt truyện, lời thoại và tranh minh họa manga.

##  Tính năng chính
- **Sinh truyện thông minh:** Sử dụng Google Gemini để tạo nội dung phong phú và nhất quán.
- **Minh họa Manga/Anime:** Tự động tạo prompt và gọi API để vẽ tranh cho từng chương.
- **Lựa chọn tương tác:** Người dùng quyết định hành động tiếp theo, AI sinh tiếp chương mới dựa trên lựa chọn đó.
- **Xuất bản PDF:** Xuất toàn bộ hành trình câu chuyện (chữ + ảnh) ra file PDF chất lượng cao, hỗ trợ tiếng Việt Unicode.
- **Giao diện "Nebula":** Giao diện vũ trụ hiện đại, tối giản và lôi cuốn người đọc.

##  Công nghệ sử dụng
- **Ngôn ngữ:** Python 3.11+
- **Backend:** FastAPI (Hỗ trợ bất đồng bộ, hiệu năng cao)
- **Frontend:** Gradio (Giao diện người dùng thời thực)
- **Database:** PostgreSQL (Lưu trữ session, chương truyện và world bible)
- **Cache/Queue:** Redis (Quản lý trạng thái và hàng đợi)
- **Containerization:** Docker & Docker Compose

##  Cấu trúc thư mục
- `/src/models`: Chứa logic cốt lõi, schemas dữ liệu và engine sinh truyện.
- `/src/ui`: Mã nguồn cho giao diện Gradio.
- `/src/backend`: Cấu hình máy chủ API và cơ sở dữ liệu.
- `/static`: Chứa ảnh đã sinh, fonts và các file xuất bản PDF.

##  Hướng dẫn khởi động
Yêu cầu: Đã cài đặt Docker và Docker Compose.

```bash
# Khởi động toàn bộ hệ thống
docker-compose up --build -d

# Xem log ứng dụng
docker logs genstory_app -f
```

Ứng dụng sẽ chạy tại: `http://localhost:7860`
