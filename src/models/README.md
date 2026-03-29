# Thư mục Models — Logic Cốt lõi & Dữ liệu

Thư mục này chứa toàn bộ logic xử lý dữ liệu, kết nối AI và quản lý cơ sở dữ liệu của hệ thống GenStory.

## Các tệp tin chính

### 1. genstory_engine.py (Engine chính)
Đây là tệp quan trọng nhất của hệ thống, điều khiển luồng hoạt động của truyện:
- **start_story**: Khởi tạo thế giới truyện, nhân vật và sinh chương 1.
- **next_chapter**: Tiếp nhận lựa chọn của người dùng và sinh chương tiếp theo.
- **generate_manga_image**: Tự động tạo prompt và gọi API để sinh ảnh minh họa.
- **export_to_pdf**: Tổng hợp dữ liệu và xuất file PDF (hỗ trợ tiếng Việt).
- **Hệ thống Parse JSON**: Đảm bảo phản hồi từ AI luôn đúng định dạng cấu trúc.

### 2. tables.py (Cơ sở dữ liệu)
Định nghĩa các bảng dữ liệu sử dụng SQLAlchemy:
- **WorldBible**: Lưu trữ thông tin cốt lõi về thế giới, nhân vật chính và nhân vật phụ.
- **StorySession**: Lưu trữ thông tin phiên làm việc, tiêu đề và trạng thái kết thúc của truyện.
- **Chapter**: Lưu trữ nội dung văn bản, ảnh minh họa và các lựa chọn cho từng chương.

### 3. schemas.py (Định dạng dữ liệu)
Định nghĩa các Pydantic models để kiểm tra tính hợp lệ của dữ liệu (Validation) khi giao tiếp giữa AI và hệ thống.

### 4. prompts.py (Mẫu câu lệnh AI)
Chứa các Template Prompts tinh chỉnh dành cho Gemini để đảm bảo văn phong kể chuyện hấp dẫn và mô tả tranh minh họa chi tiết.

### 5. db.py (Kết nối DB)
Cấu hình kết nối tới PostgreSQL và quản lý Session bất đồng bộ (AsyncSession).

### 6. config_llm.py
Cấu hình các tham số cho mô hình ngôn ngữ lớn (Gemini), bao gồm API Key và các thiết lập an toàn.

## Hệ thống hàm (Hàm chính)
- **StoryEngine.export_to_pdf()**: Hàm xuất toàn bộ truyện ra PDF.
- **StoryEngine._call_gemini_async()**: Hàm trung gian gọi API Gemini một cách an toàn.
- **StoryEngine.create_chapter()**: Hàm nội bộ để tạo và lưu trữ một chương truyện mới.
