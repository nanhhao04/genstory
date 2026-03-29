# Thư mục Backend — Máy chủ & Kết nối

Thư mục này chịu trách nhiệm khởi chạy hệ thống FastAPI và các tác vụ nền (Background Tasks).

## Các tệp tin chính

### 1. main.py (Khởi chạy FastAPI)
Đây là tệp điều khiển máy chủ FastAPI của GenStory:
- **app = FastAPI()**: Khởi tạo ứng dụng web chính.
- **lifespan**: Quản lý vòng đời ứng dụng (như việc tự động kết nối cơ sở dữ liệu khi khởi động máy chủ).
- **init_db()**: Hàm khởi tạo và tạo các quan hệ trong cơ sở dữ liệu nếu bảng đó chưa tồn tại.
- **StaticFiles**: Cấu hình chia sẻ các file hình ảnh và file xuất PDF thông qua giao diện web.

## Hệ thống dịch vụ
Hệ thống sử dụng kiến trúc bất đồng bộ (Asyncio) để đảm bảo việc ghi log và lưu trữ dữ liệu không làm chậm tốc độ phản hồi của AI.
- **Dịch vụ DB**: Sử dụng AsyncSessionLocal từ thư mục models/db.py.
- **Dịch vụ PDF**: Lưu các file PDF đã tạo vào thư mục static/exports/.
