#!/usr/bin/env python3
"""开发期：模拟多人牌桌从开局到结束，并打印日志。

这个脚本支持两种模式：

1) Engine 模式（默认）：直接在 Python 进程内创建 PokerManager/桌子并驱动一手。
    - 适合做“引擎逻辑/结算”单测式验证。

2) API 模式：连接正在运行的后端服务（HTTP + WebSocket），把机器人加进你在 App
    里“快速开始”进入的同一张桌，并自动出牌直到第一手结束，同时打印事件日志。
    - 适合做“前端联调/真实网络链路”验证。

API 模式用法（推荐，配合 App）：
  1) 在 App 里点击快速开始，进入牌桌，记下 AppBar 显示的 table_id（例如 tb_xxx）。
  2) 运行：
      python scripts/simulate_full_hand.py --table-id tb_xxx --bots 5

依赖：API 模式需要 Python 包 websockets（引擎模式不需要）。
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _bootstrap_import_path() -> None:
    root = Path(__file__).resolve().parents[1]
    src = root / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


_bootstrap_import_path()

from poker.manager import PokerManager, TableConfig, PokerTable  # noqa: E402


@dataclass
class Strategy:
    seed: int
    raise_prob: float = 0.10
    fold_prob_facing_bet: float = 0.20


def _format_event(ev: dict[str, Any]) -> str:
    et = ev.get("type")
    payload = ev.get("payload") or {}

    if et in {"HAND_STARTED", "HAND_ENDED", "SHOWDOWN", "STREET_DEALT"}:
        return f"{et} {json.dumps(payload, ensure_ascii=False)}"

    if et == "ACTION_REQUESTED":
        keys = {k: payload.get(k) for k in ["hand_id", "street", "seat_no", "user_id", "to_call", "current_bet", "min_raise_to", "action_token"]}
        return f"{et} {json.dumps(keys, ensure_ascii=False)}"

    if et == "ACTION_TAKEN":
        keys = {k: payload.get(k) for k in ["hand_id", "street", "seat_no", "user_id", "action", "amount", "contributed", "pot", "raised", "auto"]}
        return f"{et} {json.dumps(keys, ensure_ascii=False)}"

    # 其他事件默认不刷屏
    return ""


async def _drain_events(table: PokerTable, last_seq: int) -> int:
    events = await table.fetch_events_since(last_seq, limit=500)
    for ev in events:
        line = _format_event(ev)
        if line:
            print(line)
        last_seq = max(last_seq, int(ev.get("seq") or 0))
    return last_seq


def _choose_action(
    *,
    rng: random.Random,
    table: PokerTable,
) -> tuple[str, int | None]:
    hand = table.state.hand
    if hand is None:
        raise RuntimeError("no active hand")

    seat_no = hand.acting_seat
    ps = hand.players[seat_no]
    seat = table.state.seats[seat_no]

    to_call = max(0, int(hand.current_bet) - int(ps.committed_round))

    # 计算是否可加注到最小值
    can_raise = seat.stack > 0 and (ps.committed_round + seat.stack) >= int(hand.min_raise_to)

    if to_call == 0:
        if can_raise and rng.random() < 0.10:
            return "raise_to", int(hand.min_raise_to)
        return "check", None

    # facing a bet
    if rng.random() < 0.20:
        return "fold", None

    if can_raise and rng.random() < 0.10:
        return "raise_to", int(hand.min_raise_to)

    return "call", None


def _choose_action_from_action_requested(
    *,
    rng: random.Random,
    to_call: int,
    min_raise_to: int,
    raise_prob: float,
    fold_prob_facing_bet: float,
) -> tuple[str, int | None]:
    to_call = max(0, int(to_call))
    min_raise_to = max(0, int(min_raise_to))

    if to_call == 0:
        if min_raise_to > 0 and rng.random() < raise_prob:
            return "raise_to", min_raise_to
        return "check", None

    if rng.random() < fold_prob_facing_bet:
        return "fold", None

    if min_raise_to > 0 and rng.random() < raise_prob:
        return "raise_to", min_raise_to
    return "call", None


async def simulate_one_hand(
    *,
    players: int,
    buyin: int,
    sb: int,
    bb: int,
    ante: int,
    max_players: int,
    seed: int,
) -> None:
    manager = PokerManager()

    cfg = TableConfig(
        sb=sb,
        bb=bb,
        ante=ante,
        straddle=False,
        min_buyin=buyin,
        max_buyin=buyin,
        action_timeout_sec=60,
        timebank_sec=0,
    )
    table = await manager.create_table(name=f"SIM {players}p", max_players=max_players, config=cfg)

    last_seq = 0

    # 创建玩家并坐下
    for i in range(1, players + 1):
        uid = i
        await table.ensure_member(uid, f"P{uid}")
        await table.buyin(uid, buyin)
        await table.sit(uid, i)

    last_seq = await _drain_events(table, last_seq)

    # 等待第一手开始（sit() 会触发 _maybe_start_hand）
    t0 = time.time()
    while table.state.hand is None:
        if time.time() - t0 > 5:
            raise RuntimeError("hand did not start (need >=2 active seated players)")
        await asyncio.sleep(0.01)

    target_hand_id = table.state.hand.hand_id

    # 关键：只跑这一手，禁止自动开下一手
    table.set_auto_start_hands(False)

    rng = random.Random(seed)

    # 主循环：驱动行动直到 HAND_ENDED
    while True:
        last_seq = await _drain_events(table, last_seq)

        hand = table.state.hand
        if hand is None:
            break

        if hand.hand_id != target_hand_id:
            # 理论上不会发生（已关闭自动开下一手）
            break

        seat_no = hand.acting_seat
        acting_uid = table.state.seats[seat_no].user_id

        action, amount = _choose_action(rng=rng, table=table)

        await table.handle_action(
            user_id=acting_uid,
            action=action,
            amount=amount,
            client_action_id=None,
            action_token=int(hand.action_token),
            is_auto=False,
        )

    last_seq = await _drain_events(table, last_seq)

    print("\nFINAL_STACKS")
    for seat_no in sorted(table.state.seats.keys()):
        seat = table.state.seats[seat_no]
        print(f"seat {seat_no}: user {seat.user_id} stack={seat.stack}")


def _ws_url(base_url: str, table_id: str, *, last_seq: int = 0) -> str:
    http = base_url.rstrip("/")
    if http.startswith("https://"):
        ws = "wss://" + http[len("https://") :]
    elif http.startswith("http://"):
        ws = "ws://" + http[len("http://") :]
    else:
        ws = http

    url = f"{ws}/api/v1/poker/tables/{table_id}/ws"
    if last_seq > 0:
        url += f"?last_seq={int(last_seq)}"
    return url


async def _api_login(*, client: Any, base_url: str, username: str, password: str) -> str:
    r = await client.post(
        f"{base_url.rstrip('/')}/api/v1/base/access_token",
        json={"username": username, "password": password},
        timeout=20,
    )
    r.raise_for_status()
    body = r.json()
    data = body.get("data") or {}
    token = data.get("access_token")
    if not token:
        raise RuntimeError(f"login failed for {username}: {body}")
    return str(token)


async def _api_post(
    *,
    client: Any,
    base_url: str,
    token: str,
    path: str,
    json_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    r = await client.post(
        f"{base_url.rstrip('/')}{path}",
        headers={"Authorization": f"Bearer {token}"},
        json=json_body,
        timeout=20,
    )
    r.raise_for_status()
    return dict(r.json())


async def _api_get(
    *,
    client: Any,
    base_url: str,
    token: str,
    path: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    r = await client.get(
        f"{base_url.rstrip('/')}{path}",
        headers={"Authorization": f"Bearer {token}"},
        params=params,
        timeout=20,
    )
    r.raise_for_status()
    return dict(r.json())


async def _ensure_bot_users(
    *,
    client: Any,
    base_url: str,
    admin_token: str,
    bots: int,
    password: str,
) -> list[str]:
    usernames: list[str] = []
    for i in range(1, bots + 1):
        username = f"bot_{i}"
        email = f"bot_{i}@example.com"
        payload = {
            "email": email,
            "username": username,
            "password": password,
            "is_active": True,
            "is_superuser": False,
            "role_ids": [],
            "dept_id": 0,
        }
        try:
            await _api_post(
                client=client,
                base_url=base_url,
                token=admin_token,
                path="/api/v1/users/create",
                json_body=payload,
            )
            print(f"CREATED_USER {username}")
        except Exception:
            # 已存在/校验失败等：不阻塞模拟；后续 login 会给出更明确的错误。
            pass
        usernames.append(username)
    return usernames


def _find_free_seats(snapshot: dict[str, Any]) -> list[int]:
    table = snapshot.get("table") or {}
    max_players = int(table.get("max_players") or 9)

    occupied: set[int] = set()
    for s in snapshot.get("seats") or []:
        try:
            occupied.add(int(s.get("seat_no") or 0))
        except Exception:
            pass

    free: list[int] = []
    for i in range(1, max_players + 1):
        if i not in occupied:
            free.append(i)
    return free


async def _bot_ws_loop(
    *,
    base_url: str,
    table_id: str,
    token: str,
    bot_label: str,
    bot_user_id: int,
    strategy: Strategy,
    stop_event: asyncio.Event,
) -> None:
    try:
        import websockets  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "API 模式需要安装 websockets：pip install websockets"
        ) from e

    rng = random.Random(strategy.seed + bot_user_id)
    ws_url = _ws_url(base_url, table_id, last_seq=0)

    async with websockets.connect(
        ws_url,
        extra_headers={"Authorization": f"Bearer {token}"},
        ping_interval=None,
        close_timeout=2,
        open_timeout=10,
    ) as ws:
        await ws.send(json.dumps({"type": "RESUME", "last_seq": 0}))

        while not stop_event.is_set():
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=0.5)
            except asyncio.TimeoutError:
                continue

            if raw is None:
                continue

            if isinstance(raw, (bytes, bytearray)):
                continue

            text = str(raw).strip()
            if not text:
                continue

            try:
                msg = json.loads(text)
            except Exception:
                continue

            if not isinstance(msg, dict):
                continue

            if str(msg.get("type") or "").upper() != "ACTION_REQUESTED":
                continue

            payload = msg.get("payload") or {}
            if not isinstance(payload, dict):
                continue

            user_id = payload.get("user_id")
            if int(user_id or 0) != int(bot_user_id):
                continue

            action_token = int(payload.get("action_token") or 0)
            to_call = int(payload.get("to_call") or 0)
            min_raise_to = int(payload.get("min_raise_to") or 0)

            action, amount = _choose_action_from_action_requested(
                rng=rng,
                to_call=to_call,
                min_raise_to=min_raise_to,
                raise_prob=strategy.raise_prob,
                fold_prob_facing_bet=strategy.fold_prob_facing_bet,
            )

            out: dict[str, Any] = {
                "type": "ACTION",
                "action_token": action_token,
                "action": action,
                "client_action_id": f"{bot_label}-{time.time_ns()}",
            }
            if amount is not None:
                out["amount"] = int(amount)
            await ws.send(json.dumps(out))
            print(
                f"BOT_ACTION {bot_label} user={bot_user_id} token={action_token} {action}"
                + (f" amount={amount}" if amount is not None else "")
            )


async def simulate_one_hand_api(
    *,
    base_url: str,
    table_id: str,
    bots: int,
    admin_username: str,
    admin_password: str,
    bot_password: str,
    buyin: int | None,
    seed: int,
    max_seconds: int,
) -> None:
    try:
        import httpx  # type: ignore
    except Exception as e:
        raise RuntimeError("需要安装 httpx") from e

    strategy = Strategy(seed=seed)
    stop_event = asyncio.Event()

    async with httpx.AsyncClient() as client:
        admin_token = await _api_login(
            client=client,
            base_url=base_url,
            username=admin_username,
            password=admin_password,
        )

        # 机器人账号准备（默认会创建 bot_1..bot_N；已存在则忽略错误）。
        bot_usernames = await _ensure_bot_users(
            client=client,
            base_url=base_url,
            admin_token=admin_token,
            bots=bots,
            password=bot_password,
        )

        # admin 也加入桌子（保证我们能 poll events 打日志）
        await _api_post(
            client=client,
            base_url=base_url,
            token=admin_token,
            path=f"/api/v1/poker/tables/{table_id}/join",
            json_body=None,
        )

        snap_admin = await _api_get(
            client=client,
            base_url=base_url,
            token=admin_token,
            path=f"/api/v1/poker/tables/{table_id}",
        )
        snapshot = snap_admin.get("data") or {}
        if not isinstance(snapshot, dict):
            raise RuntimeError(f"unexpected snapshot: {snap_admin}")

        cfg = snapshot.get("config") or {}
        if not isinstance(cfg, dict):
            cfg = {}

        min_buyin = int(cfg.get("min_buyin") or 0)
        max_buyin = int(cfg.get("max_buyin") or 0)
        chosen_buyin = int(buyin or 0)
        if chosen_buyin <= 0:
            chosen_buyin = min_buyin if min_buyin > 0 else 200
        if max_buyin > 0:
            chosen_buyin = min(chosen_buyin, max_buyin)
        if min_buyin > 0:
            chosen_buyin = max(chosen_buyin, min_buyin)

        free_seats = _find_free_seats(snapshot)
        if len(free_seats) < bots:
            raise RuntimeError(
                f"not enough free seats: need {bots}, free={len(free_seats)}"
            )

        # 登录 bots + join/buyin/seat，并为每个 bot 开 WS 自动行动。
        ws_tasks: list[asyncio.Task] = []
        bot_infos: list[tuple[str, int, str]] = []  # (label, user_id, token)

        for idx, username in enumerate(bot_usernames, start=1):
            token = await _api_login(
                client=client,
                base_url=base_url,
                username=username,
                password=bot_password,
            )

            await _api_post(
                client=client,
                base_url=base_url,
                token=token,
                path=f"/api/v1/poker/tables/{table_id}/join",
                json_body=None,
            )
            await _api_post(
                client=client,
                base_url=base_url,
                token=token,
                path=f"/api/v1/poker/tables/{table_id}/buyin",
                json_body={"amount": chosen_buyin},
            )

            seat_no = free_seats[idx - 1]
            await _api_post(
                client=client,
                base_url=base_url,
                token=token,
                path=f"/api/v1/poker/tables/{table_id}/seat",
                json_body={"seat_no": seat_no},
            )

            # 通过 bot 自己的 snapshot 得到 user_id（用于匹配 ACTION_REQUESTED）。
            bot_snap = await _api_get(
                client=client,
                base_url=base_url,
                token=token,
                path=f"/api/v1/poker/tables/{table_id}",
            )
            bot_snapshot = bot_snap.get("data") or {}
            you = bot_snapshot.get("you") if isinstance(bot_snapshot, dict) else None
            bot_user_id = int((you or {}).get("user_id") or 0) if isinstance(you, dict) else 0
            if bot_user_id <= 0:
                raise RuntimeError(f"cannot resolve bot user_id for {username}: {bot_snap}")

            label = f"{username}@{seat_no}"
            bot_infos.append((label, bot_user_id, token))
            print(f"BOT_READY {label} user_id={bot_user_id} buyin={chosen_buyin}")

            ws_tasks.append(
                asyncio.create_task(
                    _bot_ws_loop(
                        base_url=base_url,
                        table_id=table_id,
                        token=token,
                        bot_label=label,
                        bot_user_id=bot_user_id,
                        strategy=strategy,
                        stop_event=stop_event,
                    )
                )
            )

        # 事件 watcher：用 admin token 按 seq 拉增量并打印。
        last_seq = 0
        saw_hand_started = False
        t0 = time.time()
        print(f"WATCHING table={table_id} buyin={chosen_buyin} bots={bots}")

        while True:
            if int(time.time() - t0) > max_seconds:
                print(f"TIMEOUT after {max_seconds}s")
                break

            body = await _api_get(
                client=client,
                base_url=base_url,
                token=admin_token,
                path=f"/api/v1/poker/tables/{table_id}/events",
                params={"since_seq": last_seq, "limit": 200},
            )
            data = body.get("data") or {}
            events = data.get("events") if isinstance(data, dict) else None
            if not isinstance(events, list):
                await asyncio.sleep(0.2)
                continue

            for ev in events:
                if not isinstance(ev, dict):
                    continue
                seq = int(ev.get("seq") or 0)
                if seq > last_seq:
                    last_seq = seq

                line = _format_event(ev)
                if line:
                    print(f"EV#{seq} {line}")

                et = ev.get("type")
                if et == "HAND_STARTED":
                    saw_hand_started = True
                if saw_hand_started and et == "HAND_ENDED":
                    print("HAND_ENDED (stop)")
                    stop_event.set()
                    break

            if stop_event.is_set():
                break

            await asyncio.sleep(0.2)

        stop_event.set()
        for t in ws_tasks:
            t.cancel()
        await asyncio.gather(*ws_tasks, return_exceptions=True)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="模拟 N 人打一整局（单手牌）")
    p.add_argument("--players", type=int, default=6, help="(Engine) 玩家数 N（>=2）")
    p.add_argument("--max-players", type=int, default=9, help="桌子最大座位数")
    p.add_argument("--buyin", type=int, default=200, help="每人买入")
    p.add_argument("--sb", type=int, default=1, help="小盲")
    p.add_argument("--bb", type=int, default=2, help="大盲")
    p.add_argument("--ante", type=int, default=0, help="前注")
    p.add_argument("--seed", type=int, default=42, help="随机种子（复现用）")

    # API mode
    p.add_argument("--table-id", type=str, default="", help="(API) 目标 table_id（从 App 牌桌页标题复制）")
    p.add_argument("--base-url", type=str, default="http://localhost:8000", help="(API) 后端 baseUrl")
    p.add_argument("--bots", type=int, default=0, help="(API) 需要加入并自动行动的机器人数量")
    p.add_argument("--admin-username", type=str, default="admin", help="(API) 管理员账号")
    p.add_argument("--admin-password", type=str, default="abcd1234", help="(API) 管理员密码")
    p.add_argument("--bot-password", type=str, default="BotPass1234", help="(API) 机器人账号密码（需满足强度校验）")
    p.add_argument("--max-seconds", type=int, default=120, help="(API) 最长运行秒数")
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    if args.table_id:
        if args.bots <= 0:
            raise SystemExit("API 模式需要指定 --bots（例如 --bots 5）")
        asyncio.run(
            simulate_one_hand_api(
                base_url=args.base_url,
                table_id=args.table_id,
                bots=args.bots,
                admin_username=args.admin_username,
                admin_password=args.admin_password,
                bot_password=args.bot_password,
                buyin=args.buyin if args.buyin > 0 else None,
                seed=args.seed,
                max_seconds=args.max_seconds,
            )
        )
        return

    # Engine mode (default)
    if args.players < 2:
        raise SystemExit("--players 必须 >= 2")
    if args.players > args.max_players:
        raise SystemExit("--players 不能大于 --max-players")
    asyncio.run(
        simulate_one_hand(
            players=args.players,
            buyin=args.buyin,
            sb=args.sb,
            bb=args.bb,
            ante=args.ante,
            max_players=args.max_players,
            seed=args.seed,
        )
    )


if __name__ == "__main__":
    main()
