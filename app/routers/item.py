from typing import Literal

from fastapi import APIRouter

from app.schemas.base import RouterTags

router = APIRouter(prefix="/item", tags=[RouterTags.item])


@router.get("/items/{category}", tags=[RouterTags.item], deprecated=True)
def read_item(category: Literal["food", "cafe", "drink"]):
    return {"category": category}


@router.get("/items/{item_id}", tags=[RouterTags.item], deprecated=True)
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
