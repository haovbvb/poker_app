from fastapi import APIRouter

from .subscriptions import router

subscriptions_router = APIRouter()
subscriptions_router.include_router(router, tags=["订阅模块"])

__all__ = ["subscriptions_router"]
