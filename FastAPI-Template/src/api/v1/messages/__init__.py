from fastapi import APIRouter

from .messages import router

messages_router = APIRouter()
messages_router.include_router(router, tags=["消息模块"])

__all__ = ["messages_router"]
