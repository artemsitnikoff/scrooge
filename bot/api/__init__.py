from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import settings
from .objects import router as objects_router
from .upload import router as upload_router
from .status import router as status_router

_security = HTTPBearer()


async def _verify_token(creds: HTTPAuthorizationCredentials = Security(_security)):
    if not settings.api_token:
        raise HTTPException(status_code=403, detail="API disabled: no token configured")
    if creds.credentials != settings.api_token:
        raise HTTPException(status_code=401, detail="Invalid API token")


router = APIRouter(dependencies=[Depends(_verify_token)])
router.include_router(objects_router, prefix="/objects", tags=["Objects"])
router.include_router(upload_router, prefix="/upload", tags=["Upload"])
router.include_router(status_router, prefix="/status", tags=["Status"])
