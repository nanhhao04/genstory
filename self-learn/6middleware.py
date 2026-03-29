'''
Middle ware nằm giữa client và logic server.

client -> middleware -> endpoint -> middleware -> client

'''

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import time

app = FastAPI()

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response # response có thêm header


app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com", "http://localhost:3000"], # domain được gọi api
    allow_credentials=True,  # cho phép gửi cookie, auth header
    allow_methods=["*"],          # GET, POST, PUT, DELETE...
    allow_headers=["*"],
    expose_headers=["X-Process-Time"],
    max_age=600, # cache preflight request
)

# GZip cho response lớn
app.add_middleware(GZipMiddleware, minimum_size=1000) # nén nếu respone > 1000 bytes

# chỉ cho phép host hợp lệ
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["example.com", "*.example.com", "localhost"]
)