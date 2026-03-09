from pydantic import BaseModel


class ObjectCreate(BaseModel):
    user_id: int
    name: str
    object_id: str


class ObjectResponse(BaseModel):
    id: int
    user_id: int
    name: str
    object_id: str
    created_at: str


class QueueStatsResponse(BaseModel):
    id: int
    name: str
    object_id: str
    pending: int
    sending: int
    sent: int
    errors: int
    last_sent: str | None


class UploadResponse(BaseModel):
    enqueued: int
    errors: list[str]
