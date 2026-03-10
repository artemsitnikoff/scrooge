from aiogram import Router


def setup_routers() -> Router:
    root = Router()

    from .start import router as start_router
    from .settings import router as settings_router
    from .add_object import router as add_object_router
    from .upload import router as upload_router
    from .subscription import router as subscription_router

    root.include_router(start_router)
    root.include_router(settings_router)
    root.include_router(add_object_router)
    root.include_router(upload_router)
    root.include_router(subscription_router)
    return root
