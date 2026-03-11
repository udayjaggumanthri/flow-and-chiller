from fastapi import APIRouter

from app.routers.device_presets import router as device_presets_router
from app.routers.download import router as download_router
from app.routers.reports import router as reports_router
from app.routers.settings import router as settings_router

api_router = APIRouter()

api_router.include_router(download_router)
api_router.include_router(settings_router)
api_router.include_router(device_presets_router)
api_router.include_router(reports_router)

