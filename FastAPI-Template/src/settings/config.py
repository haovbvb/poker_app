import json
import os
import secrets

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
    VERSION: str = "0.1.0"
    APP_TITLE: str = os.getenv("APP_TITLE", "Vue FastAPI Admin")
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Vue FastAPI Admin")
    APP_DESCRIPTION: str = "Description"

    CORS_ORIGINS: str = os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://localhost:8080"
    )

    @property
    def CORS_ORIGINS_LIST(self) -> list[str]:
        """将CORS_ORIGINS字符串转换为列表"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = [
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "OPTIONS",
    ]
    CORS_ALLOW_HEADERS: list = [
        "Content-Type",
        "Authorization",
        "X-Requested-With",
    ]

    DEBUG: bool = True
    APP_ENV: str = "development"

    PROJECT_ROOT: str = os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir)
    )
    BASE_DIR: str = os.path.abspath(os.path.join(PROJECT_ROOT, os.pardir))
    LOGS_ROOT: str = os.path.join(BASE_DIR, "app/logs")
    SECRET_KEY: str = os.getenv("SECRET_KEY") or secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 4  # 4 hours
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7 days for refresh token
    # 数据库配置
    DB_ENGINE: str = "postgres"  # 默认使用PostgreSQL
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = "fastapi_backend"

    @property
    def TORTOISE_ORM(self) -> dict:
        """动态生成Tortoise ORM配置"""
        if self.DB_ENGINE == "postgres":
            return {
                "connections": {
                    "default": {
                        "engine": "tortoise.backends.asyncpg",
                        "credentials": {
                            "host": self.DB_HOST,
                            "port": self.DB_PORT,
                            "user": self.DB_USER,
                            "password": self.DB_PASSWORD,
                            "database": self.DB_NAME,
                            # 连接池配置
                            "minsize": 1,
                            "maxsize": 20,
                            "max_queries": 50000,
                            "max_inactive_connection_lifetime": 300,
                            "timeout": 60,
                            "command_timeout": 60,
                        },
                    }
                },
                "apps": {
                    "models": {
                        "models": ["models", "aerich.models"],
                        "default_connection": "default",
                    },
                },
                "use_tz": False,
                "timezone": "Asia/Shanghai",
            }
        else:
            # SQLite fallback configuration
            return {
                "connections": {
                    "default": {
                        "engine": "tortoise.backends.sqlite",
                        "credentials": {"file_path": f"{self.BASE_DIR}/db.sqlite3"},
                    }
                },
                "apps": {
                    "models": {
                        "models": ["models", "aerich.models"],
                        "default_connection": "default",
                    },
                },
                "use_tz": False,
                "timezone": "Asia/Shanghai",
            }

    DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    # Swagger
    SWAGGER_UI_USERNAME: str = os.getenv("SWAGGER_UI_USERNAME", "admin")
    SWAGGER_UI_PASSWORD: str = os.getenv(
        "SWAGGER_UI_PASSWORD", "149efed4fce807a6bbc1c221"
    )
    COMPANY_ROLE_MAPPING: dict[str, list[int]] = {"default": []}

    # Redis配置
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CACHE_TTL: int = 300  # 默认缓存过期时间（秒）

    # Subscription / Billing
    SUBSCRIPTION_WEBHOOK_SECRET: str = os.getenv("SUBSCRIPTION_WEBHOOK_SECRET", "")

    # Optional mapping: {"<product_id>": "pro"|"gold"|"diamond"|"svip"}
    SUBSCRIPTION_PRODUCT_TIER_MAP: dict[str, str] = {}

    # Welfare / Bankruptcy relief
    BANKRUPTCY_THRESHOLD_CHIPS: int = int(os.getenv("BANKRUPTCY_THRESHOLD_CHIPS", "5000000"))
    BANKRUPTCY_MAX_CLAIMS_PER_DAY: int = int(os.getenv("BANKRUPTCY_MAX_CLAIMS_PER_DAY", "2"))
    BANKRUPTCY_PROMPT_SUBSCRIBE_STREAK_DAYS: int = int(
        os.getenv("BANKRUPTCY_PROMPT_SUBSCRIBE_STREAK_DAYS", "3")
    )

    # Poker bots (陪玩/补位机器人)
    # 默认开启（产品体验：单人入桌也能自动补 2 个机器人开局）；
    # 如需关闭可在环境变量中设置 POKER_BOTS_ENABLED=false
    POKER_BOTS_ENABLED: bool = True
    # 当桌上已有真人且活跃人数不足时，自动补到的目标人数（至少 2，最多 max_players）
    POKER_BOTS_TARGET_PLAYERS: int = int(os.getenv("POKER_BOTS_TARGET_PLAYERS", "2"))
    # 机器人补位买入；<=0 表示使用桌子的 min_buyin
    POKER_BOTS_BUYIN: int = int(os.getenv("POKER_BOTS_BUYIN", "0"))
    # 机器人行动延迟（毫秒），让节奏更自然；测试可设为 0
    POKER_BOTS_ACTION_DELAY_MS: int = int(os.getenv("POKER_BOTS_ACTION_DELAY_MS", "15000"))
    # 简单策略参数（并非真正 AI）：
    POKER_BOTS_RAISE_PROB: float = float(os.getenv("POKER_BOTS_RAISE_PROB", "0"))
    POKER_BOTS_FOLD_PROB_FACING_BET: float = float(
        os.getenv("POKER_BOTS_FOLD_PROB_FACING_BET", "0")
    )
    POKER_BOTS_USERNAME_PREFIX: str = os.getenv("POKER_BOTS_USERNAME_PREFIX", "bot")

    # Apple StoreKit / App Store Server
    APPLE_BUNDLE_ID: str = os.getenv("APPLE_BUNDLE_ID", "")

    # Google Play
    GOOGLE_PLAY_PACKAGE_NAME: str = os.getenv("GOOGLE_PLAY_PACKAGE_NAME", "")
    GOOGLE_PLAY_SERVICE_ACCOUNT_JSON: str = os.getenv(
        "GOOGLE_PLAY_SERVICE_ACCOUNT_JSON", ""
    )

    @field_validator("COMPANY_ROLE_MAPPING", mode="before")
    @classmethod
    def parse_company_role_mapping(cls, v):
        """解析 COMPANY_ROLE_MAPPING 环境变量"""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {"default": []}
        return v

    @field_validator("SUBSCRIPTION_PRODUCT_TIER_MAP", mode="before")
    @classmethod
    def parse_subscription_product_tier_map(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v

    @field_validator("DB_PASSWORD")
    @classmethod
    def validate_db_password(cls, v):
        """验证数据库密码"""
        app_env = os.getenv("APP_ENV", "development")
        # 测试和开发环境允许空密码
        if not v and app_env == "production":
            raise ValueError("生产环境必须设置数据库密码")
        return v

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v):
        """验证SECRET_KEY强度"""
        if len(v) < 32:
            raise ValueError("SECRET_KEY长度至少32字符")
        return v

    @field_validator("SWAGGER_UI_PASSWORD")
    @classmethod
    def validate_swagger_password(cls, v):
        """验证Swagger访问密码"""
        import os

        # 测试环境允许空密码
        if os.getenv("APP_ENV") == "testing":
            return v or "test_password"
        if not v:
            raise ValueError("SWAGGER_UI_PASSWORD必须设置")
        if len(v) < 8:
            raise ValueError("Swagger访问密码长度至少8位")
        return v

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 额外的环境特定验证
        if self.APP_ENV == "production":
            self._validate_production_config()

    def _validate_production_config(self):
        """生产环境特定配置验证"""
        if self.DEBUG:
            raise ValueError("生产环境不能启用DEBUG模式")

        if self.DB_ENGINE == "sqlite":
            raise ValueError("生产环境建议使用PostgreSQL而非SQLite")

        if "localhost" in self.CORS_ORIGINS:
            raise ValueError("生产环境不应允许localhost的CORS访问")


settings = Settings()
