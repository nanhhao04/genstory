from enum import Enum
from fastapi import FastAPI
from fastapi import Body

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}

class ModelName(str, Enum):
    alexnet = "AlexNet"
    resnet50 = "ResNet50"

@app.get("models/{model_name}")
async def get_model(model_name: ModelName):
    return {"model_name": model_name, "value": model_name.value}

@app.get("/items/")
async def list_items(
    skip: int = 0,
    limit: int = 10,
    q: str | None = None,          # Optional query param
    short: bool = False,
):
    return {"skip": skip, "limit": limit, "q": q}

@app.get("/users/{user_id}/items/{item_id}")
async def get_user_item(
        user_id: int,
        item_id: int,
        needy: str,
        q: str | None = None,
):
    return {"user_id": user_id, "item_id": item_id, "needy": needy}


@app.get("/users/{user_id}")
async def read_user(user_id: int):
    return {"user_id": user_id}



