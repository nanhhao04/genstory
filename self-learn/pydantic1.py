from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from typing import Annotated, List
from fastapi import Body

app = FastAPI()

class User(BaseModel):
    name : str
    description : str | None = None
    price: float
    tax : float

@app.post("/users")
async def create_users(user: User):
    users_dict = user.dict()
    if user.tax:
        user_tax = user.price + user.tax
        users_dict.update({"user_tax": user_tax})

    return users_dict

class Product(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=100)]
    description: Annotated[str, Field(default = None, max_length=100)]
    tags: list[str]

class Image(BaseModel):
    url: Annotated[str, Field(min_length=1, max_length=100)]

class Product(BaseModel):
    name: str
    images: List[Image] = []

@app.put("/users/{user_id}")
async def update_user(
        user_id: int,
        user: User,
        q: str | None = None,

):
    result = {"user_id": user_id, **user.dict()}
    if q:
        result.update({"q": q})
    return result


@app.put("/users/{user_id}/full")
async def update_user_full(
        user_id: int,
        user: User,
        importance: Annotated[int, Field(gt=0)],
):
    return {"user_id": user_id, "importance": importance}