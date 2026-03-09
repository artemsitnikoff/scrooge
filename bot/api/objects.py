from fastapi import APIRouter, HTTPException

import db
from .schemas import ObjectCreate, ObjectResponse

router = APIRouter()


@router.post("/", response_model=ObjectResponse, status_code=201)
async def create_object(body: ObjectCreate):
    pk = await db.add_object(body.user_id, body.name, body.object_id)
    obj = await db.get_object(pk)
    return obj


@router.get("/", response_model=list[ObjectResponse])
async def list_objects(user_id: int):
    return await db.get_objects(user_id)


@router.get("/{object_id}", response_model=ObjectResponse)
async def get_object(object_id: int):
    obj = await db.get_object(object_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")
    return obj


@router.delete("/{object_id}", status_code=204)
async def delete_object(object_id: int, user_id: int):
    deleted = await db.delete_object(object_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Object not found")
