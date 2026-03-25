import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

import db
from auth import get_current_user

router = APIRouter(tags=["Access Key"])

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)


class AccessKeyResponse(BaseModel):
    access_key: str | None
    masked: str | None


class AccessKeySetRequest(BaseModel):
    access_key: str


def _mask(key: str) -> str:
    if len(key) < 12:
        return key
    return key[:8] + "..." + key[-4:]


@router.get("/access-key", response_model=AccessKeyResponse)
async def get_access_key(user: dict = Depends(get_current_user)):
    key = await db.get_access_key(user["user_id"])
    return AccessKeyResponse(
        access_key=key,
        masked=_mask(key) if key else None,
    )


@router.put("/access-key", response_model=AccessKeyResponse)
async def set_access_key(req: AccessKeySetRequest, user: dict = Depends(get_current_user)):
    if not _UUID_RE.match(req.access_key):
        raise HTTPException(status_code=422, detail="Неверный формат ключа (ожидается UUID)")
    await db.set_access_key(user["user_id"], req.access_key)
    return AccessKeyResponse(
        access_key=req.access_key,
        masked=_mask(req.access_key),
    )


@router.delete("/access-key")
async def delete_access_key(user: dict = Depends(get_current_user)):
    await db.set_access_key(user["user_id"], None)
    return {"ok": True}
