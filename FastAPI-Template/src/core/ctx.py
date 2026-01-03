import contextvars

from starlette.background import BackgroundTasks

CTX_USER_ID: contextvars.ContextVar[int] = contextvars.ContextVar("user_id", default=0)
CTX_BG_TASKS: contextvars.ContextVar[BackgroundTasks] = contextvars.ContextVar(
    "bg_task", default=None
)

# Request locale (default: English)
CTX_LANG: contextvars.ContextVar[str] = contextvars.ContextVar("lang", default="en")
