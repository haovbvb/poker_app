from fastapi import APIRouter

from .tables import router as tables_router
from .ws import router as ws_router

poker_router = APIRouter()

poker_router.include_router(tables_router, prefix="/tables", tags=["扑克桌模块"])
# websocket routes also live under /tables
poker_router.include_router(ws_router, prefix="/tables", tags=["扑克桌模块"])

__all__ = ["poker_router"]
