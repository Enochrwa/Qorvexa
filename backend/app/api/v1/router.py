"""Aggregates all v1 routers."""

from fastapi import APIRouter

from app.modules.auth.router import router as auth_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
