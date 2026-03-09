from fastapi import APIRouter

import db
from .schemas import QueueStatsResponse

router = APIRouter()


@router.get("/", response_model=list[QueueStatsResponse])
async def get_status(user_id: int):
    """Статус объектов и очереди для пользователя."""
    return await db.get_queue_stats(user_id)
