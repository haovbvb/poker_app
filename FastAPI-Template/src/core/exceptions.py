import json
import traceback
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response
from tortoise.exceptions import DoesNotExist, IntegrityError

from log import logger
from settings.config import settings
from i18n import t


class SettingNotFound(Exception):
    pass


class BusinessError(Exception):
    """A unified business exception.

    - `code`: business-level error code (also returned as response `code`)
    - `i18n_key`: translation key
    - `params`: string formatting params for the translation
    - `http_status`: HTTP status code for the response
    """

    def __init__(
        self,
        code: int = 400,
        i18n_key: str = "errors.bad_request",
        params: dict[str, object] | None = None,
        http_status: int = 400,
    ) -> None:
        super().__init__(i18n_key)
        self.code = code
        self.i18n_key = i18n_key
        self.params = params or {}
        self.http_status = http_status


async def BusinessErrorHandle(request: Request, exc: BusinessError) -> JSONResponse:
    logger.bind(
        method=request.method,
        path=request.url.path,
        status_code=exc.http_status,
        error_code=exc.code,
        error_key=exc.i18n_key,
        error_params=exc.params,
    ).warning("BusinessError")

    msg = t(exc.i18n_key, **exc.params)
    return JSONResponse(
        status_code=exc.http_status,
        content={
            "code": exc.code,
            "msg": msg,
            "data": None,
            "error_key": exc.i18n_key,
            "error_params": exc.params,
        },
    )


async def DoesNotExistHandle(req: Request, exc: DoesNotExist) -> JSONResponse:
    # 记录详细的错误信息到日志
    error_details = {
        "method": req.method,
        "url": str(req.url),
        "path": req.url.path,
        "query_params": dict(req.query_params),
        "client_ip": req.client.host if req.client else None,
        "user_agent": req.headers.get("user-agent"),
        "exception_type": type(exc).__name__,
        "exception_msg": str(exc),
        "traceback": traceback.format_exc(),
    }

    # 构建详细的错误信息
    error_message = f"DoesNotExist异常: {req.method} {req.url.path} - {exc}\n"
    error_message += f"Exception Type: {type(exc).__name__}\n"
    error_message += f"Exception Message: {str(exc)}\n"
    error_message += (
        f"\nStack Trace:\n{error_details.get('traceback', 'No traceback available')}\n"
    )
    error_message += f"\nRequest Context:\n"
    for key, value in error_details.items():
        if key != "traceback":
            if isinstance(value, dict):
                error_message += (
                    f"  {key}: {json.dumps(value, indent=2, ensure_ascii=False)}\n"
                )
            else:
                error_message += f"  {key}: {value}\n"
    error_message += "=" * 80

    logger.error(error_message)

    # 多语言错误信息（默认英文）
    base_msg = t("errors.not_found")
    if settings.DEBUG:
        msg = f"{base_msg}: {exc}, query_params: {req.query_params}"
    else:
        msg = base_msg

    content = {
        "code": 404,
        "msg": msg,
        "data": None,
        "error_key": "errors.not_found",
        "error_params": None,
    }
    return JSONResponse(content=content, status_code=404)


async def HttpExcHandle(request: Request, exc: HTTPException | StarletteHTTPException):
    # 记录HTTP异常详情
    error_details = {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "status_code": exc.status_code,
        "exception_type": type(exc).__name__,
        "exception_msg": str(exc.detail),
        "traceback": traceback.format_exc(),
    }

    # 根据状态码决定日志级别
    if exc.status_code >= 500:
        logger.bind(**error_details).error(
            f"HTTP {exc.status_code}异常: {request.method} {request.url.path} - {exc.detail}"
        )
    elif exc.status_code >= 400:
        logger.bind(**error_details).warning(
            f"HTTP {exc.status_code}异常: {request.method} {request.url.path} - {exc.detail}"
        )

    if exc.status_code == 401 and exc.headers and "WWW-Authenticate" in exc.headers:
        return Response(status_code=exc.status_code, headers=exc.headers)

    def _as_str(detail: object) -> str:
        if detail is None:
            return ""
        return detail if isinstance(detail, str) else str(detail)

    status_key_map: dict[int, str] = {
        400: "errors.bad_request",
        401: "errors.unauthorized",
        403: "errors.forbidden",
        404: "errors.not_found",
        422: "errors.request_validation",
        500: "errors.internal",
    }

    error_key: str | None = None
    error_params: dict[str, object] | None = None
    detail_str = _as_str(exc.detail)

    # Support structured i18n payload: {"i18n_key": "...", "params": {...}}
    if isinstance(exc.detail, dict) and "i18n_key" in exc.detail:
        error_key = str(exc.detail.get("i18n_key"))
        raw_params = exc.detail.get("params")
        error_params = raw_params if isinstance(raw_params, dict) else {}
        msg = t(error_key, **(error_params or {}))

    # Support i18n marker string: "i18n:..."
    elif detail_str.startswith("i18n:"):
        error_key = detail_str.removeprefix("i18n:")
        error_params = {}
        msg = t(error_key)

    # Starlette routing errors often carry generic English detail; localize them.
    elif (
        isinstance(exc, StarletteHTTPException)
        and exc.status_code in status_key_map
        and detail_str
        in {
            "Not Found",
            "Method Not Allowed",
            "",
        }
    ):
        error_key = status_key_map[exc.status_code]
        error_params = None
        msg = t(error_key)

    # Preserve explicit non-i18n detail to avoid unexpected behavior changes.
    elif detail_str:
        msg = detail_str

    # Otherwise, localize by status code when we have a known mapping.
    elif exc.status_code in status_key_map:
        error_key = status_key_map[exc.status_code]
        error_params = None
        msg = t(error_key)

    else:
        msg = t("errors.http")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "msg": msg,
            "data": None,
            "error_key": error_key,
            "error_params": error_params,
        },
    )


async def IntegrityHandle(request: Request, exc: IntegrityError):
    # 记录数据完整性错误详情
    error_details = {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "exception_type": type(exc).__name__,
        "exception_msg": str(exc),
        "traceback": traceback.format_exc(),
    }

    logger.bind(**error_details).error(
        f"数据完整性错误: {request.method} {request.url.path} - {exc}"
    )

    base_msg = t("errors.integrity")
    if settings.DEBUG:
        msg = f"{base_msg}: {exc}"
    else:
        msg = base_msg

    content = {
        "code": 500,
        "msg": msg,
        "data": None,
        "error_key": "errors.integrity",
        "error_params": None,
    }
    return JSONResponse(content=content, status_code=500)


async def RequestValidationHandle(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    # 记录请求验证错误详情
    error_details = {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "exception_type": type(exc).__name__,
        "exception_msg": str(exc),
        "validation_errors": exc.errors(),
        "traceback": traceback.format_exc(),
    }

    logger.bind(**error_details).warning(
        f"请求参数验证失败: {request.method} {request.url.path} - {len(exc.errors())}个错误"
    )

    base_msg = t("errors.request_validation")
    if settings.DEBUG:
        msg = f"{base_msg}: {exc.errors()}"
    else:
        msg = base_msg

    content = {
        "code": 422,
        "msg": msg,
        "data": None,
        "error_key": "errors.request_validation",
        "error_params": None,
    }
    return JSONResponse(content=content, status_code=422)


async def ResponseValidationHandle(
    request: Request, exc: ResponseValidationError
) -> JSONResponse:
    # 记录响应验证错误详情
    error_details = {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "exception_type": type(exc).__name__,
        "exception_msg": str(exc),
        "validation_errors": exc.errors(),
        "traceback": traceback.format_exc(),
    }

    logger.bind(**error_details).error(
        f"响应格式验证错误: {request.method} {request.url.path} - {len(exc.errors())}个错误"
    )

    base_msg = t("errors.response_validation")
    if settings.DEBUG:
        msg = f"{base_msg}: {exc.errors()}"
    else:
        msg = base_msg

    content = {
        "code": 500,
        "msg": msg,
        "data": None,
        "error_key": "errors.response_validation",
        "error_params": None,
    }
    return JSONResponse(content=content, status_code=500)


async def UnhandledExceptionHandle(request: Request, exc: Exception) -> JSONResponse:
    """处理所有未捕获的异常"""
    # 记录未处理异常的详细信息
    error_details = {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "exception_type": type(exc).__name__,
        "exception_msg": str(exc),
        "exception_module": getattr(exc, "__module__", "unknown"),
        "traceback": traceback.format_exc(),
    }

    # 尝试获取请求体信息（如果可能）
    try:
        if hasattr(request, "_body"):
            error_details["request_body_size"] = (
                len(request._body) if request._body else 0
            )
    except Exception:
        pass

    logger.bind(**error_details).critical(
        f"未处理的异常: {request.method} {request.url.path} - {type(exc).__name__}: {exc}"
    )

    base_msg = t("errors.internal")
    if settings.DEBUG:
        msg = f"{base_msg}: {type(exc).__name__}: {exc}"
    else:
        msg = base_msg

    content = {
        "code": 500,
        "msg": msg,
        "data": None,
        "error_key": "errors.internal",
        "error_params": None,
    }
    return JSONResponse(content=content, status_code=500)
