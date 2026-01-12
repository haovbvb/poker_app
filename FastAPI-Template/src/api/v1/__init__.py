from fastapi import APIRouter

from core.dependency import DependPermisson

from .apis import apis_router
from .base import base_router
from .files import files_router
from .roles import roles_router
from .messages import messages_router
from .users import users_router
from .poker import poker_router
from .subscriptions import subscriptions_router
from .rewards import rewards_router
from .welfare import welfare_router
from .analysis import router as analysis_router
from .wallet import wallet_router

v1_router = APIRouter()

v1_router.include_router(base_router, prefix="/base")
v1_router.include_router(analysis_router, tags=["Analysis"])
v1_router.include_router(users_router, prefix="/users", dependencies=[DependPermisson])
v1_router.include_router(roles_router, prefix="/role", dependencies=[DependPermisson])
# v1_router.include_router(
#     menus_router, prefix="/menu", dependencies=[DependPermisson]
# )
v1_router.include_router(apis_router, prefix="/api", dependencies=[DependPermisson])
# 消息模块：用户侧使用JWT即可；管理端接口在路由内部单独加权限依赖
v1_router.include_router(messages_router, prefix="/messages")
# v1_router.include_router(
#     depts_router, prefix="/dept", dependencies=[DependPermisson]
# )
# v1_router.include_router(
#     auditlog_router, prefix="/auditlog", dependencies=[DependPermisson]
# )
v1_router.include_router(files_router, prefix="/files", dependencies=[DependPermisson])

# Poker/Texas Hold'em - requires JWT auth (not RBAC permission)
v1_router.include_router(poker_router, prefix="/poker")

# Subscriptions/Billing - requires JWT auth
v1_router.include_router(subscriptions_router, prefix="/subscriptions")

# Daily rewards - requires JWT auth
v1_router.include_router(rewards_router, prefix="/rewards")

# Welfare / bankruptcy relief - requires JWT auth
v1_router.include_router(welfare_router, prefix="/welfare")

# Wallet - requires JWT auth
v1_router.include_router(wallet_router, prefix="/wallet")

__all__ = ["v1_router"]
