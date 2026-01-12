from fastapi import APIRouter

from .wallet import router

wallet_router = APIRouter()
wallet_router.include_router(router, tags=["钱包"])

__all__ = ["wallet_router"]
