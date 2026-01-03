from __future__ import annotations

from typing import Any


def ok_response_example(data: Any, *, code: int = 200, msg: str = "OK") -> dict[int, Any]:
    """FastAPI `responses=` helper for standard Success payload."""

    return {
        code: {
            "description": "OK",
            "content": {
                "application/json": {
                    "example": {"code": code, "msg": msg, "data": data}
                }
            },
        }
    }


def page_response_example(
    data: Any,
    *,
    total: int,
    page: int,
    page_size: int,
    code: int = 200,
    msg: str = "OK",
) -> dict[int, Any]:
    """FastAPI `responses=` helper for standard paging payload."""

    return {
        code: {
            "description": "OK",
            "content": {
                "application/json": {
                    "example": {
                        "code": code,
                        "msg": msg,
                        "data": data,
                        "total": total,
                        "page": page,
                        "page_size": page_size,
                    }
                }
            },
        }
    }


def error_response_example(
    code: int,
    *,
    error_key: str,
    msg: str = "Error",
    error_params: dict[str, Any] | None = None,
) -> dict[int, Any]:
    """FastAPI `responses=` helper for standard Fail payload."""

    return {
        code: {
            "description": "Error",
            "content": {
                "application/json": {
                    "example": {
                        "code": code,
                        "msg": msg,
                        "data": None,
                        "error_key": error_key,
                        "error_params": error_params,
                    }
                }
            },
        }
    }


def examples_param(value: Any, *, summary: str = "示例") -> dict[str, Any]:
    """FastAPI Query/Body `examples=` helper."""

    return {"default": {"summary": summary, "value": value}}
