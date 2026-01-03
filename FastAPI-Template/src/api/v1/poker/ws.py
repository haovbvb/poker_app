import json

import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.exceptions import BusinessError
from i18n import t
from poker import poker_manager
from settings.config import settings

router = APIRouter()


def _err_payload(*, code: int, error_key: str, error_params: dict | None) -> dict:
    return {
        "code": code,
        "msg": t(error_key, **(error_params or {})),
        "error_key": error_key,
        "error_params": error_params,
    }


async def _ws_auth(websocket: WebSocket) -> tuple[int, str]:
    auth = websocket.headers.get("authorization") or websocket.headers.get(
        "Authorization"
    )
    if not auth:
        raise BusinessError(code=401, i18n_key="auth.missing_token", http_status=401)

    token = auth
    if token.lower().startswith("bearer "):
        token = token[7:]

    try:
        data = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except Exception as e:
        raise BusinessError(code=401, i18n_key="auth.failed", http_status=401) from e

    user_id = data.get("user_id")
    username = data.get("username")
    if not user_id:
        raise BusinessError(code=401, i18n_key="auth.failed", http_status=401)

    return int(user_id), str(username or user_id)


# PING → 返回 {"type":"PONG"}。
# RESUME：{"type":"RESUME","last_seq":123}，服务端尝试补发事件；无事件则回 TABLE_SNAPSHOT。
# ACTION：{"type":"ACTION","action_token":1,"action":"fold|call|check|raise_to",
# "amount":123,"client_action_id":"uuid-optional"}；
# 只有 raise_to 需要 amount，其余无需；action_token 必填且为当前轮服务端下发的 token。
# 错误返回（不会直接断开）：{"type":"ERROR","seq":<current_seq>,"server_ts":null,
# "payload":{"code":400|403|...,"msg":"...","error_key":"...","error_params":{...}}}。
# 断线/鉴权失败：握手期错误会先 send_json(type=ERROR) 然后 close(1008)。
@router.websocket("/{table_id}/ws")
async def table_ws(websocket: WebSocket, table_id: str):
    user_id: int | None = None
    username: str | None = None
    table = None

    # Setup / auth errors are fatal (close the socket).
    try:
        user_id, username = await _ws_auth(websocket)
        await websocket.accept()

        # Optional resume hint in query: ?last_seq=123
        last_seq_q = websocket.query_params.get("last_seq")
        last_seq_hint = int(last_seq_q) if last_seq_q and last_seq_q.isdigit() else None

        table = await poker_manager.get_table(table_id)
        await table.ensure_member(user_id=user_id, username=username)
        await table.connect(user_id=user_id, websocket=websocket)

        if last_seq_hint is not None and last_seq_hint > 0:
            events = await table.fetch_events_since_for_user(
                user_id=user_id,
                last_seq=last_seq_hint,
                limit=200,
            )
            if events:
                for ev in events:
                    await websocket.send_json(ev)
            else:
                snapshot = await table.snapshot_for(user_id=user_id)
                await websocket.send_json(
                    {
                        "type": "TABLE_SNAPSHOT",
                        "seq": table.state.seq,
                        "server_ts": None,
                        "payload": snapshot,
                    }
                )
        else:
            snapshot = await table.snapshot_for(user_id=user_id)
            await websocket.send_json(
                {
                    "type": "TABLE_SNAPSHOT",
                    "seq": table.state.seq,
                    "server_ts": None,
                    "payload": snapshot,
                }
            )
    except BusinessError as e:
        if not websocket.client_state.name == "CONNECTED":
            try:
                await websocket.accept()
            except Exception:
                pass
        await websocket.send_json(
            {
                "type": "ERROR",
                "seq": 0,
                "server_ts": None,
                "payload": _err_payload(
                    code=e.code, error_key=e.i18n_key, error_params=e.params
                ),
            }
        )
        try:
            await websocket.close(code=1008)
        except Exception:
            pass
        return

    # Main loop: message-level errors should not kill the connection.
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except Exception:
                await websocket.send_json(
                    {
                        "type": "ERROR",
                        "seq": table.state.seq,
                        "server_ts": None,
                        "payload": _err_payload(
                            code=400,
                            error_key="errors.bad_request",
                            error_params=None,
                        ),
                    }
                )
                continue

            mtype = str(msg.get("type", "")).upper()
            if mtype == "PING":
                await websocket.send_json({"type": "PONG"})
                continue

            if mtype == "RESUME":
                try:
                    last_seq = msg.get("last_seq")
                    try:
                        last_seq_i = int(last_seq) if last_seq is not None else 0
                    except Exception:
                        last_seq_i = 0

                    if last_seq_i > 0:
                        events = await table.fetch_events_since_for_user(
                            user_id=user_id,
                            last_seq=last_seq_i,
                            limit=200,
                        )
                        if events:
                            for ev in events:
                                await websocket.send_json(ev)
                            continue

                    snapshot = await table.snapshot_for(user_id=user_id)
                    await websocket.send_json(
                        {
                            "type": "TABLE_SNAPSHOT",
                            "seq": table.state.seq,
                            "server_ts": None,
                            "payload": snapshot,
                        }
                    )
                except BusinessError as e:
                    await websocket.send_json(
                        {
                            "type": "ERROR",
                            "seq": table.state.seq,
                            "server_ts": None,
                            "payload": _err_payload(
                                code=e.code,
                                error_key=e.i18n_key,
                                error_params=e.params,
                            ),
                        }
                    )
                continue

            if mtype == "ACTION":
                try:
                    action = msg.get("action")
                    amount = msg.get("amount")
                    client_action_id = msg.get("client_action_id")
                    if "action_token" not in msg:
                        raise BusinessError(
                            code=400, i18n_key="poker.missing_action_token"
                        )
                    try:
                        action_token = int(msg.get("action_token"))
                    except Exception:
                        raise BusinessError(
                            code=400, i18n_key="poker.invalid_action_token"
                        )
                    await table.handle_action(
                        user_id=user_id,
                        action=str(action or ""),
                        amount=int(amount) if amount is not None else None,
                        client_action_id=(
                            str(client_action_id)
                            if client_action_id is not None
                            else None
                        ),
                        action_token=action_token,
                    )
                except BusinessError as e:
                    await websocket.send_json(
                        {
                            "type": "ERROR",
                            "seq": table.state.seq,
                            "server_ts": None,
                            "payload": _err_payload(
                                code=e.code,
                                error_key=e.i18n_key,
                                error_params=e.params,
                            ),
                        }
                    )
                continue

            await websocket.send_json(
                {
                    "type": "ERROR",
                    "seq": table.state.seq,
                    "server_ts": None,
                    "payload": _err_payload(
                        code=400,
                        error_key="poker.ws_unknown_message",
                        error_params=None,
                    ),
                }
            )
    except WebSocketDisconnect:
        # client disconnected
        try:
            if table is not None and user_id is not None:
                await table.disconnect(user_id=user_id)
        except Exception:
            pass
    except Exception:
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
