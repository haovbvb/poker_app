from typing import Any

from fastapi.responses import JSONResponse

from i18n import t


class Success(JSONResponse):
    def __init__(
        self,
        code: int = 200,
        msg: str | None = None,
        data: Any | None = None,
        **kwargs,
    ):
        # 确保msg不为None
        if msg is None:
            msg = t("common.ok")
        content = {"code": code, "msg": msg, "data": data}
        content.update(kwargs)
        super().__init__(content=content, status_code=code)


class Fail(JSONResponse):
    def __init__(
        self,
        code: int = 400,
        msg: str | None = None,
        data: Any | None = None,
        error_key: str | None = None,
        error_params: dict[str, Any] | None = None,
        **kwargs,
    ):
        # 确保msg不为None
        if msg is None and error_key:
            msg = t(error_key, **(error_params or {}))
        if msg is None:
            msg = t("common.error")
        content = {
            "code": code,
            "msg": msg,
            "data": data,
            "error_key": error_key,
            "error_params": error_params,
        }
        content.update(kwargs)
        super().__init__(content=content, status_code=code)


class SuccessExtra(JSONResponse):
    def __init__(
        self,
        code: int = 200,
        msg: str | None = None,
        data: Any | None = None,
        total: int = 0,
        page: int = 1,
        page_size: int = 20,
        **kwargs,
    ):
        # 确保msg不为None
        if msg is None:
            msg = t("common.ok")
        content = {
            "code": code,
            "msg": msg,
            "data": data,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
        content.update(kwargs)
        super().__init__(content=content, status_code=code)
