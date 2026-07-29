from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()


@app.get("/items/{item_id}")
async def read_items(item_id: str):
    if item_id not in fake_items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return fake_items_db[item_id]


class UnicornException(Exception):
    def __init__(self, name: str):
        self.name = name


@app.exception_handler(UnicornException)
async def unicorn_exception_handler(request: Request, exc: UnicornException):
    return JSONResponse(status_code=404, content={"error": str(exc)})


@app.get("/unicorns/{name}")
async def read_unicorn(name: str):
    if name == "yolo":
        raise UnicornException(name=name)
    return {"unicorn_name": name}
