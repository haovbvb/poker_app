import pytest


@pytest.mark.asyncio
async def test_business_error_contract(async_client):
    from src import app
    from core.exceptions import BusinessError

    async def _raise_business_error():
        raise BusinessError(
            code=10001,
            i18n_key="auth.permission_denied",
            params={"method": "GET", "path": "/x"},
            http_status=403,
        )

    path = "/__test__/business-error"
    if not any(getattr(r, "path", None) == path for r in app.routes):
        app.add_api_route(path, _raise_business_error, methods=["GET"])

    resp = await async_client.get(path)
    assert resp.status_code == 403
    body = resp.json()
    assert body == {
        "code": 10001,
        "msg": "Permission denied (method: GET, path: /x)",
        "data": None,
        "error_key": "auth.permission_denied",
        "error_params": {"method": "GET", "path": "/x"},
    }


@pytest.mark.asyncio
async def test_fail_error_key_contract(async_client):
    from src import app
    from schemas.base import Fail

    async def _fail():
        # error_key drives the localized msg
        return Fail(code=400, error_key="errors.bad_request", error_params=None)

    path = "/__test__/fail"
    if not any(getattr(r, "path", None) == path for r in app.routes):
        app.add_api_route(path, _fail, methods=["GET"])

    resp = await async_client.get(path)
    assert resp.status_code == 400
    body = resp.json()
    assert body["code"] == 400
    assert body["msg"] == "Bad request"
    assert body["data"] is None
    assert body["error_key"] == "errors.bad_request"
    assert body["error_params"] is None
