# --- Union response ---
from typing import Union

from fastapi import FastAPI, status
from pydantic import BaseModel

app = FastAPI()


class UserIn(BaseModel):
    username: str
    password: str  # Input model (có password)
    email: str
    full_name: str | None = None


class UserOut(BaseModel):
    username: str  # Output model (KHÔNG có password)
    email: str
    full_name: str | None = None


# response_model lọc fields, validate output, tạo docs
@app.post(
    "/user/",
    response_model=UserOut,  # Chỉ trả về fields trong UserOut
    status_code=status.HTTP_201_CREATED,
    summary="Tạo user mới",
    description="Tạo user, trả về thông tin không kèm password.",
    response_description="User vừa được tạo",
    tags=["users"],
)
async def create_user(user: UserIn) -> UserOut:
    return user  # password sẽ bị lọc bởi response_model


@app.get("/items/{item_id}", response_model=Item, response_model_exclude_unset=True)
async def read_item(item_id: str):
    # Chỉ trả về các field được SET, không trả field mặc định chưa dùng
    return items[item_id]


@app.get("/items/{item_id}", response_model=Union[PlaneItem, CarItem])
async def read_item(item_id: str):
    return items[item_id]


# --- List response ---
@app.get("/items/", response_model=list[Item])
async def read_items():
    return fake_items_db


# --- Response trực tiếp (bypass response_model) ---
from fastapi.responses import JSONResponse, RedirectResponse


@app.get("/redirect")
async def redirect():
    return RedirectResponse(url="/items/")


@app.get("/custom")
async def custom_response():
    return JSONResponse(
        content={"message": "ok"},
        status_code=200,
        headers={"X-Custom": "value"},
    )
