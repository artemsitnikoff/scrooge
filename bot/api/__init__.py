from fastapi import APIRouter

from .objects import router as objects_router
from .upload import router as upload_router
from .status import router as status_router

router = APIRouter()
router.include_router(objects_router, prefix="/objects", tags=["Objects"])
router.include_router(upload_router, prefix="/upload", tags=["Upload"])
router.include_router(status_router, prefix="/status", tags=["Status"])
