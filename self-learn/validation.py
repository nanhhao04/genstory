from typing import Annotated

from fastapi import Cookie, FastAPI, Header, Path, Query

app = FastAPI()


@app.get("/items")
async def read_items(
    q: Annotated[
        str | None,
        Query(
            alias="item-query",
            description="Query string for items",
            min_length=1,
            pattern="ff",
            deprecated=True,
        ),
    ] = None,
    tags: Annotated[list[str], Query()] = [],
):
    return {"q": q, "tags": tags}


@app.get("/items/{item_id}")
async def read_item(
    item_id: Annotated[int, Path(title="Item ID", ge=1, le=1000)],
    q: str | None = None,
):
    return {"item_id": item_id, "q": q}


@app.get("/headers/")
async def read_headers(
    user_agent: Annotated[str | None, Header()] = None,
    x_token: Annotated[list[str] | None, Header()] = None,
):
    return {"User-Agent": user_agent, "X-Token": x_token}


@app.get("/cookies/")
async def read_cookies(session_id: Annotated[str | None, Cookie()] = None):
    return {"session_id": session_id}
