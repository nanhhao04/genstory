from google import genai

API_KEY = "AIzaSyDfSRAuOM52y8oL61zuzNoojQ_OKbv-K84"
client = genai.Client(api_key=API_KEY)

print("Các model hỗ trợ tạo ảnh khả dụng cho API Key của bạn:")
print("-" * 50)

# Duyệt qua danh sách tất cả các model
for model in client.models.list():
    # Lọc ra những model có chữ 'imagen' trong tên
    if "imagen" in model.name.lower():
        print(f"Tên model: {model.name}")
        print(f"Mô tả: {model.description}")
        print("-" * 50)
