import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

import db
from auth import get_current_user

router = APIRouter(prefix="/objects", tags=["Objects"])

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)


class ObjectCreateRequest(BaseModel):
    object_id: str
    name: str = ""


class ObjectRenameRequest(BaseModel):
    name: str


class ObjectResponse(BaseModel):
    id: int
    name: str
    object_id: str
    expires_at: str | None = None
    subscription_active: bool = False


@router.get("", response_model=list[ObjectResponse])
async def list_objects(user: dict = Depends(get_current_user)):
    from datetime import datetime

    rows = await db.get_subscriptions_for_user(user["user_id"])
    now = datetime.utcnow().isoformat()
    return [
        ObjectResponse(
            id=r["id"],
            name=r["name"],
            object_id=r["object_id"],
            expires_at=r["expires_at"],
            subscription_active=bool(r["expires_at"] and r["expires_at"] > now),
        )
        for r in rows
    ]


@router.post("", response_model=ObjectResponse, status_code=201)
async def create_object(req: ObjectCreateRequest, user: dict = Depends(get_current_user)):
    if not _UUID_RE.match(req.object_id):
        raise HTTPException(status_code=422, detail="Неверный формат UUID объекта")

    key = await db.get_access_key(user["user_id"])
    if not key:
        raise HTTPException(status_code=400, detail="Сначала установите ключ доступа УТКО")

    name = req.name.strip() or req.object_id[:8]
    pk = await db.add_object(user["user_id"], name, req.object_id)
    return ObjectResponse(id=pk, name=name, object_id=req.object_id)


@router.patch("/{object_id}", response_model=ObjectResponse)
async def rename_object(object_id: int, req: ObjectRenameRequest, user: dict = Depends(get_current_user)):
    if not req.name.strip():
        raise HTTPException(status_code=422, detail="Название не может быть пустым")
    ok = await db.rename_object(object_id, user["user_id"], req.name.strip())
    if not ok:
        raise HTTPException(status_code=404, detail="Объект не найден")
    obj = await db.get_object(object_id)
    return ObjectResponse(id=obj["id"], name=obj["name"], object_id=obj["object_id"])


@router.delete("/{object_id}")
async def delete_object(object_id: int, user: dict = Depends(get_current_user)):
    ok = await db.delete_object(object_id, user["user_id"])
    if not ok:
        raise HTTPException(status_code=404, detail="Объект не найден")
    return {"ok": True}
