import json
import os
import tempfile

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel

import db
from auth import get_current_user
from services.file_parser import parse_file

router = APIRouter(prefix="/upload", tags=["Upload"])

# Временное хранение распарсенных записей (в памяти, по session)
_upload_cache: dict[str, list[dict]] = {}


class UploadPreviewResponse(BaseModel):
    records: list[dict]
    record_count: int
    errors: list[str]
    cache_key: str


class ConfirmRequest(BaseModel):
    cache_key: str


class ConfirmResponse(BaseModel):
    success: bool
    message: str
    sent_count: int = 0


@router.post("/{object_id}", response_model=UploadPreviewResponse)
async def upload_file(
    object_id: int,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    obj = await db.get_object(object_id)
    if not obj or obj["user_id"] != user["user_id"]:
        raise HTTPException(status_code=404, detail="Объект не найден")

    # Проверка формата
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in (".xlsx", ".xls", ".json"):
        raise HTTPException(status_code=400, detail="Поддерживаются .xlsx, .xls, .json")

    # Сохранение во временный файл и парсинг
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        records, errors = parse_file(tmp_path)
    finally:
        os.unlink(tmp_path)

    # Кэшируем записи для подтверждения
    import uuid
    cache_key = f"{user['user_id']}:{object_id}:{uuid.uuid4().hex[:8]}"
    _upload_cache[cache_key] = records

    return UploadPreviewResponse(
        records=records[:50],  # Первые 50 для превью
        record_count=len(records),
        errors=errors,
        cache_key=cache_key,
    )


@router.post("/{object_id}/confirm", response_model=ConfirmResponse)
async def confirm_upload(
    object_id: int,
    req: ConfirmRequest,
    user: dict = Depends(get_current_user),
):
    obj = await db.get_object(object_id)
    if not obj or obj["user_id"] != user["user_id"]:
        raise HTTPException(status_code=404, detail="Объект не найден")

    records = _upload_cache.pop(req.cache_key, None)
    if not records:
        raise HTTPException(status_code=400, detail="Нет данных для отправки. Загрузите файл заново.")

    # Проверка подписки
    active = await db.is_subscription_active(object_id)
    if not active:
        raise HTTPException(status_code=402, detail="Подписка неактивна. Оплатите подписку для отправки.")

    # Получаем ключ доступа
    key = await db.get_access_key(user["user_id"])
    if not key:
        raise HTTPException(status_code=400, detail="Ключ доступа не установлен")

    # Отправка в УТКО
    from services.utko_client import UTKOClient
    client = UTKOClient()
    try:
        success, message = await client.send_records(obj["object_id"], key, records)
    finally:
        await client.close()

    if success:
        return ConfirmResponse(success=True, message=message, sent_count=len(records))
    else:
        return ConfirmResponse(success=False, message=message)
