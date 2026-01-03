from datetime import UTC, datetime, timedelta
import hashlib
from typing import Final

import jwt

from schemas.login import JWTPayload
from settings.config import settings

from utils.cache import cache_manager


_REVOKED_REFRESH_PREFIX: Final[str] = "jwt:revoked:refresh"
_revoked_refresh_local: dict[str, float] = {}


def _token_sha256(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _revoked_refresh_key(token: str) -> str:
    return f"{_REVOKED_REFRESH_PREFIX}:{_token_sha256(token)}"


def _purge_local_revocations(now_ts: float) -> None:
    expired = [k for k, exp in _revoked_refresh_local.items() if exp <= now_ts]
    for k in expired:
        _revoked_refresh_local.pop(k, None)


async def revoke_refresh_token(token: str) -> None:
    """Revoke (invalidate) a refresh token until its expiry.

    Uses Redis if available; falls back to in-memory revocation in this process.
    """

    # Decode without exp verification so logout can revoke even near/after expiry.
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        options={"verify_exp": False},
    )

    if payload.get("token_type") != "refresh":
        raise jwt.InvalidTokenError("Invalid token type. Expected refresh")

    exp_raw = payload.get("exp")
    now = datetime.now(UTC)
    ttl = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    if exp_raw is not None:
        try:
            exp_dt = datetime.fromtimestamp(float(exp_raw), tz=UTC)
            ttl = max(1, int((exp_dt - now).total_seconds()))
        except Exception:
            ttl = max(1, ttl)

    key = _revoked_refresh_key(token)
    _purge_local_revocations(now.timestamp())
    _revoked_refresh_local[key] = now.timestamp() + float(ttl)

    # Best-effort Redis store (shared across processes).
    await cache_manager.set(key, {"revoked": True}, ttl=ttl)


async def is_refresh_token_revoked(token: str) -> bool:
    """Check whether a refresh token has been revoked."""

    key = _revoked_refresh_key(token)
    now_ts = datetime.now(UTC).timestamp()
    _purge_local_revocations(now_ts)
    exp_ts = _revoked_refresh_local.get(key)
    if exp_ts is not None and exp_ts > now_ts:
        return True

    return await cache_manager.exists(key)


def create_access_token(*, data: JWTPayload):
    """创建访问令牌"""
    payload = data.model_dump().copy()
    # 确保token_type为access
    payload["token_type"] = "access"
    encoded_jwt = jwt.encode(
        payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(user_id: int) -> str:
    """创建刷新令牌"""
    expire = datetime.now(UTC) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    payload = JWTPayload(
        user_id=user_id,
        exp=expire,
        token_type="refresh",
    )

    payload_dict = payload.model_dump()
    # 确保token_type为refresh
    payload_dict["token_type"] = "refresh"

    return jwt.encode(
        payload_dict, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def verify_token(token: str, token_type: str = "access") -> JWTPayload:
    """验证令牌并返回载荷"""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )

        # 检查令牌类型
        if payload.get("token_type") != token_type:
            raise jwt.InvalidTokenError(f"Invalid token type. Expected {token_type}")

        return JWTPayload(**payload)

    except jwt.ExpiredSignatureError as e:
        raise jwt.ExpiredSignatureError("Token has expired") from e
    except jwt.InvalidTokenError as e:
        raise jwt.InvalidTokenError("Invalid token") from e


def create_token_pair(user_id: int) -> tuple[str, str]:
    """创建访问令牌和刷新令牌对"""
    # 创建访问令牌
    access_expire = datetime.now(UTC) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    access_payload = JWTPayload(
        user_id=user_id,
        exp=access_expire,
        token_type="access",
    )
    access_token = create_access_token(data=access_payload)

    # 创建刷新令牌
    refresh_token = create_refresh_token(user_id)

    return access_token, refresh_token
