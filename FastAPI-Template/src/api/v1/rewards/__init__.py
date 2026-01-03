from fastapi import APIRouter

from .daily import router

rewards_router = APIRouter()
rewards_router.include_router(router, tags=["每日奖励"])

__all__ = ["rewards_router"]
