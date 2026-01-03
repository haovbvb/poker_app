from fastapi import APIRouter

from .bankruptcy import router

welfare_router = APIRouter()
welfare_router.include_router(router, tags=["破产救济"])

__all__ = ["welfare_router"]
