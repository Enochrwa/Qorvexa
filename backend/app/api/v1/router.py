"""Aggregates all v1 routers."""

from fastapi import APIRouter

from app.modules.auth.router import router as auth_router
from app.modules.catalog.admin_router import router as admin_router
from app.modules.catalog.router import router as catalog_router
from app.modules.media.router import admin_router as media_admin_router
from app.modules.media.router import webhook_router
from app.modules.profiles.router import router as profiles_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(profiles_router)
api_router.include_router(catalog_router)
api_router.include_router(admin_router)
api_router.include_router(media_admin_router)
api_router.include_router(webhook_router)
