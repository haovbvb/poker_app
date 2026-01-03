from __future__ import annotations

from typing import Any


def patch_openapi_schema(openapi_schema: dict[str, Any]) -> dict[str, Any]:
    """Patch generated OpenAPI schema with documentation for non-HTTP surfaces.

    FastAPI does not include WebSocket routes in OpenAPI; we inject a doc-only
    path item so app clients can discover the WS contract from /openapi.json.
    """

    paths: dict[str, Any] = openapi_schema.setdefault("paths", {})

    ws_path = "/api/v1/poker/tables/{table_id}/ws"

    # Do not overwrite if the project later adds an HTTP route with same path.
    if ws_path in paths:
        return openapi_schema

    paths[ws_path] = {
        "get": {
            "tags": ["扑克桌模块"],
            "summary": "牌桌 WebSocket 事件流",
            "description": (
                "该端点为 WebSocket（非传统 HTTP JSON）。\n\n"
                "握手：使用 HTTP GET 升级协议（Upgrade: websocket），并在 Header 中携带 JWT：\n"
                "`Authorization: Bearer <access_token>`。\n\n"
                "可选断线续传：在 query 里带 `last_seq`，服务端会尝试补发事件；无事件则先推送 `TABLE_SNAPSHOT`。\n\n"
                "注意：OpenAPI 标准不支持 WebSocket，本条目仅用于文档展示（vendor extension）。"
            ),
            "parameters": [
                {
                    "name": "table_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"},
                    "description": "牌桌ID",
                    "example": "tb_123",
                },
                {
                    "name": "last_seq",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "integer", "minimum": 0},
                    "description": "断线续传：最后收到的事件序号（可选）",
                    "example": 123,
                },
                {
                    "name": "Authorization",
                    "in": "header",
                    "required": True,
                    "schema": {"type": "string"},
                    "description": "JWT 访问令牌：Bearer <access_token>",
                    "example": "Bearer eyJhbGciOi...",
                },
            ],
            "responses": {
                "101": {"description": "Switching Protocols (WebSocket Upgrade)"},
                "401": {"description": "Unauthorized (握手期鉴权失败会 close 1008)"},
            },
            # Vendor extension: message contract examples for clients.
            "x-websocket": {
                "url": "ws(s)://<host>/api/v1/poker/tables/{table_id}/ws",
                "handshake": {
                    "headers": {"Authorization": "Bearer <access_token>"},
                    "query": {"last_seq": "<int, optional>"},
                },
                "client_messages": [
                    {"type": "PING"},
                    {"type": "RESUME", "last_seq": 123},
                    {
                        "type": "ACTION",
                        "action_token": 1,
                        "action": "fold|call|check|raise_to",
                        "amount": 123,
                        "client_action_id": "uuid-optional",
                    },
                ],
                "server_messages": [
                    {"type": "PONG"},
                    {
                        "type": "TABLE_SNAPSHOT",
                        "seq": 12,
                        "server_ts": None,
                        "payload": {
                            "table": {"table_id": "tb_123", "name": "Texas Table"},
                            "you": {"user_id": 1002, "hole_cards": ["As", "Kd"]},
                        },
                    },
                    {
                        "type": "PLAYER_JOINED",
                        "seq": 10,
                        "server_ts": 1735180000123,
                        "payload": {"user_id": 1001, "username": "alice"},
                    },
                    {
                        "type": "ERROR",
                        "seq": 12,
                        "server_ts": None,
                        "payload": {
                            "code": 400,
                            "msg": "...",
                            "error_key": "poker.ws_unknown_message",
                            "error_params": None,
                        },
                    },
                ],
                "close_codes": {
                    "1008": "Policy Violation (握手鉴权失败等)",
                    "1011": "Internal Error",
                },
            },
        }
    }

    return openapi_schema
