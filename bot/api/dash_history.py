from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

import db
from auth import get_current_user

router = APIRouter(prefix="/history", tags=["History"])


class HistoryItem(BaseModel):
    id: int
    object_name: str
    filename: str | None
    record_count: int
    error_count: int
    utko_success: bool | None
    source: str
    created_at: str


class HistoryDetail(BaseModel):
    id: int
    object_name: str
    filename: str | None
    record_count: int
    error_count: int
    records: list[dict]
    utko_success: bool | None
    utko_response: str | None
    source: str
    created_at: str


@router.get("", response_model=list[HistoryItem])
async def list_history(
    limit: int = 50,
    offset: int = 0,
    user: dict = Depends(get_current_user),
):
    rows = await db.get_upload_history(user["user_id"], limit=limit, offset=offset)
    return [
        HistoryItem(
            id=r["id"],
            object_name=r["object_name"],
            filename=r["filename"],
            record_count=r["record_count"],
            error_count=r["error_count"],
            utko_success=bool(r["utko_success"]) if r["utko_success"] is not None else None,
            source=r["source"],
            created_at=r["created_at"],
        )
        for r in rows
    ]


@router.get("/{history_id}", response_model=HistoryDetail)
async def get_history_detail(history_id: int, user: dict = Depends(get_current_user)):
    row = await db.get_upload_history_detail(history_id, user["user_id"])
    if not row:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return HistoryDetail(
        id=row["id"],
        object_name=row["object_name"],
        filename=row["filename"],
        record_count=row["record_count"],
        error_count=row["error_count"],
        records=row["records"],
        utko_success=bool(row["utko_success"]) if row["utko_success"] is not None else None,
        utko_response=row["utko_response"],
        source=row["source"],
        created_at=row["created_at"],
    )
