import os
import tempfile

from fastapi import APIRouter, HTTPException, UploadFile

import db
from services.file_parser import parse_file
from .schemas import UploadResponse

router = APIRouter()


@router.post("/{object_id}", response_model=UploadResponse)
async def upload_file(object_id: int, file: UploadFile):
    """Загрузить файл (.xlsx или .json) с данными весового контроля."""
    obj = await db.get_object(object_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in (".xlsx", ".xls", ".json"):
        raise HTTPException(status_code=400, detail="Supported formats: .xlsx, .json")

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp_path = tmp.name
        content = await file.read()
        tmp.write(content)

    try:
        valid_records, errors = parse_file(tmp_path)
    finally:
        os.unlink(tmp_path)

    if not valid_records:
        raise HTTPException(status_code=422, detail={"errors": errors})

    await db.enqueue_records(object_id, valid_records)
    return UploadResponse(enqueued=len(valid_records), errors=errors)
