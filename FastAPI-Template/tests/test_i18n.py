import pytest


@pytest.mark.asyncio
async def test_default_language_is_english(async_client):
    resp = await async_client.get("/this-route-should-not-exist")
    assert resp.status_code == 404
    data = resp.json()
    assert data["code"] == 404
    # default should be English
    assert "Resource not found" in data["msg"]
    assert data["data"] is None
    assert data["error_key"] == "errors.not_found"
    assert data["error_params"] is None


@pytest.mark.asyncio
async def test_accept_language_zh(async_client):
    resp = await async_client.get(
        "/this-route-should-not-exist",
        headers={"Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"},
    )
    assert resp.status_code == 404
    data = resp.json()
    assert data["code"] == 404
    assert "请求的资源不存在" in data["msg"]
    assert data["data"] is None
    assert data["error_key"] == "errors.not_found"
    assert data["error_params"] is None


@pytest.mark.asyncio
async def test_query_param_lang_zh_overrides_header(async_client):
    resp = await async_client.get(
        "/this-route-should-not-exist?lang=zh",
        headers={"Accept-Language": "en-US"},
    )
    assert resp.status_code == 404
    data = resp.json()
    assert data["code"] == 404
    assert "请求的资源不存在" in data["msg"]
    assert data["data"] is None
    assert data["error_key"] == "errors.not_found"
    assert data["error_params"] is None
