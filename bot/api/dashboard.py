from fastapi import APIRouter

from .auth import router as auth_router
from .dash_access_key import router as access_key_router
from .dash_objects import router as objects_router
from .dash_upload import router as upload_router
from .dash_subscription import router as subscription_router
from .dash_history import router as history_router

router = APIRouter()

# Auth — без JWT (публичные эндпоинты)
router.include_router(auth_router)

# Dashboard — с JWT (через get_current_user в каждом роутере)
router.include_router(access_key_router)
router.include_router(objects_router)
router.include_router(upload_router)
router.include_router(subscription_router)
router.include_router(history_router)
