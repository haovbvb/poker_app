from datetime import datetime

from pydantic import BaseModel, Field


class CredentialsSchema(BaseModel):
    username: str = Field(..., description="用户名称", example="admin")
    password: str = Field(..., description="密码", example="abcd1234")


class JWTOut(BaseModel):
    access_token: str
    refresh_token: str
    username: str
    tier: str | None = None
    token_type: str = "bearer"
    expires_in: int  # 过期时间（秒）


class JWTPayload(BaseModel):
    user_id: int
    exp: datetime
    token_type: str = "access"  # access 或 refresh


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="刷新令牌")


class TokenRefreshOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # 新access_token过期时间（秒）


class LogoutRequest(BaseModel):
    """退出登录入参

    传 refresh_token 才能实现服务端撤销（黑名单）语义；否则仅表示客户端本地清理。
    """

    refresh_token: str | None = Field(
        default=None,
        description="刷新令牌(可选)。传入则服务端撤销该 refresh_token",
        examples=[
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3MzU3MDAwMDAsInRva2VuX3R5cGUiOiJyZWZyZXNoIn0._signature_",
        ],
    )
