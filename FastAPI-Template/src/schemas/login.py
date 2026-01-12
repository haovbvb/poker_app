import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class CredentialsSchema(BaseModel):
    username: str = Field(..., description="用户名称", example="admin")
    password: str = Field(..., description="密码", example="abcd1234")


class RegisterRequest(BaseModel):
    """用户注册入参（用户侧）"""

    email: EmailStr = Field(..., description="邮箱")
    username: str = Field(
        ...,
        min_length=3,
        max_length=20,
        pattern="^[a-zA-Z0-9_]+$",
        description="用户名（3-20位字母数字下划线）",
    )
    password: str = Field(..., description="密码（至少8位，包含字母和数字）")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str):
        if len(v) < 8:
            raise ValueError("密码长度至少8位")
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("密码必须包含字母")
        if not re.search(r"\d", v):
            raise ValueError("密码必须包含数字")
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str):
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("用户名只能包含字母、数字和下划线")
        return v


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
