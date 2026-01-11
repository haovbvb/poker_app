from __future__ import annotations

import asyncio
import json
import random
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from fastapi import WebSocket

from core.exceptions import BusinessError
from poker.deck_manager import DeckManager
from poker.event_store import EventStore
from poker.hand_evaluator import rank_seven
from poker.redis_lock import RedisLock
from utils.cache import cache_manager
from poker.lobby import find_lobby_level_for_max_chips
from settings.config import settings


@dataclass(slots=True)
class MemberState:
    user_id: int
    username: str
    status: str  # spectator | seated | sitout
    buyin: int = 0
    seat_no: int | None = None


@dataclass(slots=True)
class SeatState:
    seat_no: int
    user_id: int
    username: str
    stack: int
    status: str  # seated | sitout


@dataclass(slots=True)
class TableConfig:
    sb: int = 1
    bb: int = 2
    ante: int = 0
    straddle: bool = False
    min_buyin: int = 40
    max_buyin: int = 200
    action_timeout_sec: int = 20
    timebank_sec: int = 60


@dataclass(slots=True)
class TableState:
    table_id: str
    name: str
    max_players: int
    config: TableConfig
    created_at: float
    members: dict[int, MemberState]
    seats: dict[int, SeatState]
    last_button_seat: int | None = None
    hand: "HandState | None" = None
    seq: int = 0


@dataclass(slots=True)
class HandPlayerState:
    seat_no: int
    user_id: int
    committed: int = 0  # total committed for the hand
    committed_round: int = 0  # committed in the current betting round
    folded: bool = False
    all_in: bool = False


@dataclass(slots=True)
class HandState:
    hand_id: str
    street: str  # PREFLOP
    button_seat: int
    sb_seat: int
    bb_seat: int
    pot: int
    current_bet: int
    min_raise_to: int
    acting_seat: int
    action_deadline_ms: int
    pending_to_act: set[int]
    players: dict[int, HandPlayerState]  # seat_no -> state
    hole_cards: dict[int, list[str]]  # user_id -> [c1,c2]
    board: list[str]
    deck: list[str]
    burned: list[str]
    algo_version: str
    server_seed_hash: str
    server_seed_hex: str | None
    deck_hash: str
    action_token: int = 0


class PokerTable:
    def __init__(
        self,
        table_id: str,
        name: str,
        max_players: int,
        config: TableConfig,
        *,
        event_store: EventStore,
    ):
        self.state = TableState(
            table_id=table_id,
            name=name,
            max_players=max_players,
            config=config,
            created_at=time.time(),
            members={},
            seats={},
            last_button_seat=None,
            hand=None,
            seq=0,
        )
        self._lock = asyncio.Lock()
        self._connections: dict[int, WebSocket] = {}
        self._event_store = event_store
        self._redis = event_store.redis
        self._redis_state_key = f"poker:table:{table_id}:state"
        self._redis_tables_key = "poker:tables"
        self._redis_lock_key = f"poker:table:{table_id}:lock"
        self._stream_last_id: str = "0-0"
        self._stream_task: asyncio.Task | None = None
        # Default: behave like production (auto-start hands when possible).
        # Dev scripts can disable this to stop after a single hand.
        self._auto_start_hands: bool = True

        # Bot ids are negative and table-local.
        self._next_bot_id: int = -1

    def set_auto_start_hands(self, enabled: bool) -> None:
        self._auto_start_hands = bool(enabled)

    def _dump_state(self) -> dict[str, Any]:
        cfg = self.state.config
        hand = self.state.hand
        hand_dict: dict[str, Any] | None = None
        if hand is not None:
            hand_dict = {
                "hand_id": hand.hand_id,
                "street": hand.street,
                "button_seat": hand.button_seat,
                "sb_seat": hand.sb_seat,
                "bb_seat": hand.bb_seat,
                "pot": hand.pot,
                "current_bet": hand.current_bet,
                "min_raise_to": hand.min_raise_to,
                "acting_seat": hand.acting_seat,
                "action_deadline_ms": hand.action_deadline_ms,
                "pending_to_act": list(hand.pending_to_act),
                "players": {
                    str(seat_no): {
                        "seat_no": ps.seat_no,
                        "user_id": ps.user_id,
                        "committed": ps.committed,
                        "committed_round": ps.committed_round,
                        "folded": ps.folded,
                        "all_in": ps.all_in,
                    }
                    for seat_no, ps in hand.players.items()
                },
                "hole_cards": {
                    str(uid): cards for uid, cards in hand.hole_cards.items()
                },
                "board": list(hand.board),
                "deck": list(hand.deck),
                "burned": list(hand.burned),
                "algo_version": hand.algo_version,
                "server_seed_hash": hand.server_seed_hash,
                "server_seed_hex": hand.server_seed_hex,
                "deck_hash": hand.deck_hash,
                "action_token": hand.action_token,
            }

        return {
            "table": {
                "table_id": self.state.table_id,
                "name": self.state.name,
                "max_players": self.state.max_players,
                "created_at": self.state.created_at,
                "seq": self.state.seq,
                "last_button_seat": self.state.last_button_seat,
            },
            "config": {
                "sb": cfg.sb,
                "bb": cfg.bb,
                "ante": cfg.ante,
                "straddle": cfg.straddle,
                "min_buyin": cfg.min_buyin,
                "max_buyin": cfg.max_buyin,
                "action_timeout_sec": cfg.action_timeout_sec,
                "timebank_sec": cfg.timebank_sec,
            },
            "members": {
                str(uid): {
                    "user_id": m.user_id,
                    "username": m.username,
                    "status": m.status,
                    "buyin": m.buyin,
                    "seat_no": m.seat_no,
                }
                for uid, m in self.state.members.items()
            },
            "seats": {
                str(seat_no): {
                    "seat_no": s.seat_no,
                    "user_id": s.user_id,
                    "username": s.username,
                    "stack": s.stack,
                    "status": s.status,
                }
                for seat_no, s in self.state.seats.items()
            },
            "hand": hand_dict,
        }

    def _load_state(self, data: dict[str, Any]) -> None:
        table = data.get("table") or {}
        cfg = data.get("config") or {}

        self.state.table_id = str(table.get("table_id") or self.state.table_id)
        self.state.name = str(table.get("name") or self.state.name)
        self.state.max_players = int(table.get("max_players") or self.state.max_players)
        self.state.created_at = float(table.get("created_at") or self.state.created_at)
        self.state.seq = int(table.get("seq") or self.state.seq)
        lbs = table.get("last_button_seat")
        self.state.last_button_seat = int(lbs) if lbs is not None else None

        self.state.config = TableConfig(
            sb=int(cfg.get("sb") or self.state.config.sb),
            bb=int(cfg.get("bb") or self.state.config.bb),
            ante=int(cfg.get("ante") or self.state.config.ante),
            straddle=bool(
                cfg.get("straddle") if "straddle" in cfg else self.state.config.straddle
            ),
            min_buyin=int(cfg.get("min_buyin") or self.state.config.min_buyin),
            max_buyin=int(cfg.get("max_buyin") or self.state.config.max_buyin),
            action_timeout_sec=int(
                cfg.get("action_timeout_sec") or self.state.config.action_timeout_sec
            ),
            timebank_sec=int(cfg.get("timebank_sec") or self.state.config.timebank_sec),
        )

        members_raw = data.get("members") or {}
        seats_raw = data.get("seats") or {}

        self.state.members = {
            int(uid): MemberState(
                user_id=int(m.get("user_id")),
                username=str(m.get("username")),
                status=str(m.get("status")),
                buyin=int(m.get("buyin") or 0),
                seat_no=int(m.get("seat_no")) if m.get("seat_no") is not None else None,
            )
            for uid, m in members_raw.items()
        }

        self.state.seats = {
            int(seat_no): SeatState(
                seat_no=int(s.get("seat_no")),
                user_id=int(s.get("user_id")),
                username=str(s.get("username")),
                stack=int(s.get("stack") or 0),
                status=str(s.get("status")),
            )
            for seat_no, s in seats_raw.items()
        }

        hand_raw = data.get("hand")
        if not hand_raw:
            self.state.hand = None
            return

        players_raw = hand_raw.get("players") or {}
        pending_raw = hand_raw.get("pending_to_act") or []
        hole_raw = hand_raw.get("hole_cards") or {}
        players: dict[int, HandPlayerState] = {}
        for seat_no_s, p in players_raw.items():
            seat_no = int(seat_no_s)
            players[seat_no] = HandPlayerState(
                seat_no=int(p.get("seat_no") or seat_no),
                user_id=int(p.get("user_id")),
                committed=int(p.get("committed") or 0),
                committed_round=int(
                    p.get("committed_round")
                    if p.get("committed_round") is not None
                    else (p.get("committed") or 0)
                ),
                folded=bool(p.get("folded")),
                all_in=bool(p.get("all_in")),
            )
        hole_cards = {int(uid): list(cards) for uid, cards in hole_raw.items()}

        self.state.hand = HandState(
            hand_id=str(hand_raw.get("hand_id")),
            street=str(hand_raw.get("street")),
            button_seat=int(hand_raw.get("button_seat")),
            sb_seat=int(hand_raw.get("sb_seat")),
            bb_seat=int(hand_raw.get("bb_seat")),
            pot=int(hand_raw.get("pot") or 0),
            current_bet=int(hand_raw.get("current_bet") or 0),
            min_raise_to=int(hand_raw.get("min_raise_to") or 0),
            acting_seat=int(hand_raw.get("acting_seat") or 0),
            action_deadline_ms=int(hand_raw.get("action_deadline_ms") or 0),
            pending_to_act={int(x) for x in pending_raw},
            players=players,
            hole_cards=hole_cards,
            board=list(hand_raw.get("board") or []),
            deck=list(hand_raw.get("deck") or []),
            burned=list(hand_raw.get("burned") or []),
            algo_version=str(hand_raw.get("algo_version") or "fy-hmac-sha256-v1"),
            server_seed_hash=str(hand_raw.get("server_seed_hash") or ""),
            server_seed_hex=(
                str(hand_raw.get("server_seed_hex"))
                if hand_raw.get("server_seed_hex") is not None
                else None
            ),
            deck_hash=str(hand_raw.get("deck_hash") or ""),
            action_token=int(hand_raw.get("action_token") or 0),
        )

    async def _refresh_from_redis_unlocked(self) -> None:
        if self._redis is None:
            return
        raw = await self._redis.get(self._redis_state_key)
        if not raw:
            return
        try:
            data = json.loads(raw)
        except Exception:
            return
        self._load_state(data)

    async def _persist_to_redis_unlocked(self) -> None:
        if self._redis is None:
            return
        data = self._dump_state()
        raw = json.dumps(data, ensure_ascii=False)
        await self._redis.set(self._redis_state_key, raw)
        # Track table ids for multi-instance discovery.
        try:
            await self._redis.sadd(self._redis_tables_key, self.state.table_id)
        except Exception:
            return

    @asynccontextmanager
    async def _locked_state(self):
        if self._redis is None:
            async with self._lock:
                yield
            return

        lock = RedisLock(self._redis, self._redis_lock_key, ttl_ms=15000)
        token = await lock.acquire(timeout_ms=8000)
        try:
            async with self._lock:
                await self._refresh_from_redis_unlocked()
                yield
                await self._persist_to_redis_unlocked()
        finally:
            await lock.release(token)

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections[user_id] = websocket
            if self._stream_task is None and self._event_store.redis is not None:
                # Forward events created on other instances to local WS clients.
                self._stream_last_id = await self._event_store.get_latest_id(
                    self.state.table_id
                )
                self._stream_task = asyncio.create_task(self._stream_forward_loop())

    async def disconnect(self, user_id: int) -> None:
        async with self._lock:
            self._connections.pop(user_id, None)

            # If no local connections remain, stop forwarding.
            if not self._connections and self._stream_task is not None:
                self._stream_task.cancel()
                self._stream_task = None

    def _filter_event_for_user(
        self, event: dict[str, Any], user_id: int
    ) -> dict[str, Any] | None:
        visibility = event.get("visibility") or "public"
        if visibility == "public":
            return event

        audience = event.get("audience") or {}
        user_ids = audience.get("user_ids") or []
        if user_id in user_ids:
            return event

        public_payload = event.get("public_payload")
        if public_payload is None:
            return None

        # Return a redacted copy.
        ev = dict(event)
        ev["payload"] = public_payload
        ev.pop("public_payload", None)
        return ev

    async def _dispatch_event(self, event: dict[str, Any]) -> None:
        dead: list[int] = []
        for uid, ws in list(self._connections.items()):
            try:
                ev = self._filter_event_for_user(event, uid)
                if ev is None:
                    continue
                await ws.send_json(ev)
            except Exception:
                dead.append(uid)
        for uid in dead:
            self._connections.pop(uid, None)

    async def _stream_forward_loop(self) -> None:
        try:
            while True:
                last_id, events = await self._event_store.read_blocking(
                    self.state.table_id,
                    last_id=self._stream_last_id,
                    block_ms=5000,
                    count=100,
                )
                self._stream_last_id = last_id
                for event in events:
                    # Best-effort forward; local emit already broadcasts.
                    await self._dispatch_event(event)
        except asyncio.CancelledError:
            return
        except Exception:
            # Don't crash the app because of stream forwarding.
            return

    def _next_seq(self) -> int:
        self.state.seq += 1
        return self.state.seq

    async def emit(
        self,
        event_type: str,
        payload: dict[str, Any],
        *,
        visibility: str = "public",
        audience_user_ids: list[int] | None = None,
        public_payload: dict[str, Any] | None = None,
    ) -> None:
        message: dict[str, Any] = {
            "type": event_type,
            "seq": self._next_seq(),
            "server_ts": int(time.time() * 1000),
            "visibility": visibility,
            "payload": payload,
        }
        if visibility == "private":
            message["audience"] = {"user_ids": list(audience_user_ids or [])}
            if public_payload is not None:
                message["public_payload"] = public_payload
        try:
            self._stream_last_id = await self._event_store.append(
                self.state.table_id, seq=int(message["seq"]), event=message
            )
        except Exception:
            # Persistence is best-effort; still broadcast.
            pass
        await self._dispatch_event(message)

    async def fetch_events_since(
        self, last_seq: int, limit: int = 200
    ) -> list[dict[str, Any]]:
        return await self._event_store.fetch_since(
            self.state.table_id, last_seq=last_seq, limit=limit
        )

    async def fetch_events_since_for_user(
        self, *, user_id: int, last_seq: int, limit: int = 200
    ) -> list[dict[str, Any]]:
        events = await self.fetch_events_since(last_seq, limit=limit)
        out: list[dict[str, Any]] = []
        for ev in events:
            filtered = self._filter_event_for_user(ev, user_id)
            if filtered is not None:
                out.append(filtered)
        return out

    async def snapshot_for(self, user_id: int) -> dict[str, Any]:
        async with self._lock:
            await self._refresh_from_redis_unlocked()
        # Only include private cards for the requesting user.
        seats = [
            {
                "seat_no": s.seat_no,
                "user_id": s.user_id,
                "username": s.username,
                "stack": s.stack,
                "status": s.status,
            }
            for s in sorted(self.state.seats.values(), key=lambda x: x.seat_no)
        ]
        members = [
            {
                "user_id": m.user_id,
                "username": m.username,
                "status": m.status,
                "buyin": m.buyin,
                "seat_no": m.seat_no,
            }
            for m in sorted(self.state.members.values(), key=lambda x: x.user_id)
        ]
        cfg = self.state.config
        hand = self.state.hand
        hand_public: dict[str, Any] | None = None
        your_cards: list[str] | None = None
        if hand is not None:
            hand_public = {
                "hand_id": hand.hand_id,
                "street": hand.street,
                "button_seat": hand.button_seat,
                "sb_seat": hand.sb_seat,
                "bb_seat": hand.bb_seat,
                "board": list(hand.board),
                "pot": hand.pot,
                "current_bet": hand.current_bet,
                "min_raise_to": hand.min_raise_to,
                "acting_seat": hand.acting_seat,
                "action_deadline_ms": hand.action_deadline_ms,
                "players": {
                    str(seat_no): {
                        "user_id": ps.user_id,
                        "committed": ps.committed,
                        "committed_round": ps.committed_round,
                        "folded": ps.folded,
                        "all_in": ps.all_in,
                    }
                    for seat_no, ps in hand.players.items()
                },
            }
            your_cards = hand.hole_cards.get(user_id)

        return {
            "table": {
                "table_id": self.state.table_id,
                "name": self.state.name,
                "max_players": self.state.max_players,
                "created_at": self.state.created_at,
                "seq": self.state.seq,
            },
            "config": {
                "sb": cfg.sb,
                "bb": cfg.bb,
                "ante": cfg.ante,
                "straddle": cfg.straddle,
                "min_buyin": cfg.min_buyin,
                "max_buyin": cfg.max_buyin,
                "action_timeout_sec": cfg.action_timeout_sec,
                "timebank_sec": cfg.timebank_sec,
            },
            "seats": seats,
            "members": members,
            "hand": hand_public,
            "you": {"user_id": user_id, "hole_cards": your_cards},
        }

    async def ensure_member(self, user_id: int, username: str) -> None:
        async with self._locked_state():
            if user_id in self.state.members:
                return
            self.state.members[user_id] = MemberState(
                user_id=user_id,
                username=username,
                status="spectator",
                buyin=0,
                seat_no=None,
            )
            await self.emit("PLAYER_JOINED", {"user_id": user_id, "username": username})

    async def leave(self, user_id: int) -> None:
        async with self._locked_state():
            member = self.state.members.get(user_id)
            if not member:
                return

            if member.seat_no is not None and self.state.hand is not None:
                ps = self.state.hand.players.get(member.seat_no)
                if ps is not None and not ps.folded:
                    if ps.all_in:
                        raise BusinessError(
                            code=409, i18n_key="poker.cannot_leave_allin_hand"
                        )
                    await self._force_fold_locked(member.seat_no, reason="leave")

            if member.seat_no is not None:
                self.state.seats.pop(member.seat_no, None)
            self.state.members.pop(user_id, None)
            await self.emit("PLAYER_LEFT", {"user_id": user_id})
        if self._auto_start_hands:
            await self._maybe_fill_bots_for_start()
            await self._maybe_start_hand()

    async def buyin(self, user_id: int, amount: int) -> None:
        async with self._locked_state():
            member = self.state.members.get(user_id)
            if not member:
                raise BusinessError(code=404, i18n_key="poker.not_in_table")
            cfg = self.state.config
            if amount < cfg.min_buyin or amount > cfg.max_buyin:
                raise BusinessError(
                    code=400,
                    i18n_key="poker.buyin_out_of_range",
                    params={"min": cfg.min_buyin, "max": cfg.max_buyin},
                )
            member.buyin = amount
            await self.emit("BUYIN_OK", {"user_id": user_id, "amount": amount})

    async def sit(self, user_id: int, seat_no: int) -> None:
        async with self._locked_state():
            if seat_no < 1 or seat_no > self.state.max_players:
                raise BusinessError(
                    code=400,
                    i18n_key="poker.invalid_seat",
                    params={"seat": seat_no, "max": self.state.max_players},
                )
            if seat_no in self.state.seats:
                raise BusinessError(code=400, i18n_key="poker.seat_taken")

            member = self.state.members.get(user_id)
            if not member:
                raise BusinessError(code=404, i18n_key="poker.not_in_table")
            if member.buyin <= 0:
                raise BusinessError(code=400, i18n_key="poker.buyin_required")

            # Free old seat if any
            if member.seat_no is not None:
                self.state.seats.pop(member.seat_no, None)

            self.state.seats[seat_no] = SeatState(
                seat_no=seat_no,
                user_id=user_id,
                username=member.username,
                stack=member.buyin,
                status="seated",
            )
            member.seat_no = seat_no
            member.status = "seated"

            await self.emit(
                "PLAYER_SEATED",
                {"user_id": user_id, "seat_no": seat_no, "stack": member.buyin},
            )
        if self._auto_start_hands:
            await self._maybe_fill_bots_for_start()
            await self._maybe_start_hand()

    async def spectate(self, user_id: int) -> None:
        async with self._locked_state():
            member = self.state.members.get(user_id)
            if not member:
                raise BusinessError(code=404, i18n_key="poker.not_in_table")

            if member.seat_no is not None and self.state.hand is not None:
                ps = self.state.hand.players.get(member.seat_no)
                if ps is not None and not ps.folded:
                    if ps.all_in:
                        raise BusinessError(
                            code=409, i18n_key="poker.cannot_leave_allin_hand"
                        )
                    await self._force_fold_locked(member.seat_no, reason="spectate")

            if member.seat_no is not None:
                self.state.seats.pop(member.seat_no, None)
                member.seat_no = None
            member.status = "spectator"
            await self.emit("PLAYER_SPECTATE", {"user_id": user_id})
        if self._auto_start_hands:
            await self._maybe_fill_bots_for_start()
            await self._maybe_start_hand()

    async def sitout(self, user_id: int) -> None:
        async with self._locked_state():
            member = self.state.members.get(user_id)
            if not member:
                raise BusinessError(code=404, i18n_key="poker.not_in_table")

            if member.seat_no is not None and self.state.hand is not None:
                ps = self.state.hand.players.get(member.seat_no)
                if ps is not None and not ps.folded:
                    if ps.all_in:
                        raise BusinessError(
                            code=409, i18n_key="poker.cannot_leave_allin_hand"
                        )
                    await self._force_fold_locked(member.seat_no, reason="sitout")

            member.status = "sitout"
            if member.seat_no is not None and member.seat_no in self.state.seats:
                seat = self.state.seats[member.seat_no]
                seat.status = "sitout"
            await self.emit("PLAYER_SITOUT", {"user_id": user_id})
        if self._auto_start_hands:
            await self._maybe_fill_bots_for_start()
            await self._maybe_start_hand()

    def _bot_target_players(self) -> int:
        try:
            target = int(getattr(settings, "POKER_BOTS_TARGET_PLAYERS", 2))
        except Exception:
            target = 2
        return max(2, min(int(self.state.max_players), target))

    def _bots_enabled(self) -> bool:
        return bool(getattr(settings, "POKER_BOTS_ENABLED", False))

    async def _maybe_fill_bots_for_start(self) -> None:
        """人数不够时自动补位机器人，让单人也能开局。

        - 机器人用负数 user_id 表示
        - 仅在当前没有进行中的 hand 时补位
        - 仅当桌上至少存在 1 个真人（user_id > 0）的活跃座位时补位
        """

        if not self._bots_enabled():
            return

        async with self._locked_state():
            if self.state.hand is not None:
                return

            active = self._active_seat_nos()
            if not active:
                return

            human_active = [s for s in active if int(self.state.seats[s].user_id) > 0]
            if not human_active:
                return

            target_players = self._bot_target_players()
            need = max(0, int(target_players) - int(len(active)))
            if need <= 0:
                return

            cfg = self.state.config
            bot_buyin = int(getattr(settings, "POKER_BOTS_BUYIN", 0) or 0)
            if bot_buyin <= 0:
                # Default bot stack should be large enough to post blinds and still act.
                # If we default to min_buyin (which can be very small in tests), the bot
                # may become all-in on the blind and never generate actions.
                bot_buyin = max(int(cfg.min_buyin), int(cfg.bb) * 2)
            bot_buyin = max(int(cfg.min_buyin), min(int(cfg.max_buyin), int(bot_buyin)))

            prefix = str(getattr(settings, "POKER_BOTS_USERNAME_PREFIX", "bot") or "bot")
            await self._fill_bots_locked(count=need, buyin=bot_buyin, username_prefix=prefix)

    async def _fill_bots_locked(self, *, count: int, buyin: int, username_prefix: str) -> list[int]:
        """在持有 table lock 的情况下创建并坐下机器人，避免中途触发 auto-start。"""

        bot_ids: list[int] = []
        count_i = max(0, int(count))
        if count_i <= 0:
            return bot_ids

        buyin_i = int(buyin)
        max_players = int(self.state.max_players)

        for _ in range(count_i):
            taken = set(self.state.seats.keys())
            seat_no: int | None = None
            for s in range(1, max_players + 1):
                if s not in taken:
                    seat_no = s
                    break
            if seat_no is None:
                break

            bot_id = int(self._next_bot_id)
            self._next_bot_id -= 1

            username = f"{username_prefix}_{abs(bot_id)}"
            self.state.members[bot_id] = MemberState(
                user_id=bot_id,
                username=username,
                status="seated",
                buyin=buyin_i,
                seat_no=seat_no,
            )
            self.state.seats[seat_no] = SeatState(
                seat_no=seat_no,
                user_id=bot_id,
                username=username,
                stack=buyin_i,
                status="seated",
            )

            await self.emit("PLAYER_JOINED", {"user_id": bot_id, "username": username})
            await self.emit("BUYIN_OK", {"user_id": bot_id, "amount": buyin_i})
            await self.emit(
                "PLAYER_SEATED",
                {"user_id": bot_id, "seat_no": seat_no, "stack": buyin_i},
            )
            bot_ids.append(bot_id)

        return bot_ids

    async def _force_fold_locked(self, seat_no: int, *, reason: str) -> None:
        hand = self.state.hand
        if hand is None:
            return
        ps = hand.players.get(seat_no)
        if ps is None:
            return
        if ps.folded or ps.all_in:
            return

        ps.folded = True
        hand.pending_to_act.discard(seat_no)

        now_ms = int(time.time() * 1000)
        await self.emit(
            "ACTION_TAKEN",
            {
                "hand_id": hand.hand_id,
                "seat_no": seat_no,
                "user_id": ps.user_id,
                "action": "fold",
                "amount": None,
                "contributed": 0,
                "pot": hand.pot,
                "client_action_id": None,
                "auto": True,
                "raised": False,
                "forced_reason": reason,
            },
        )

        await self._advance_after_action_locked(now_ms)
        if self.state.hand is not None:
            await self._emit_action_request()

    def _active_seat_nos(self) -> list[int]:
        # Only seated players with positive stack are active.
        seat_nos = []
        for seat_no, seat in self.state.seats.items():
            if seat.status != "seated":
                continue
            if seat.stack <= 0:
                continue
            seat_nos.append(seat_no)
        return sorted(seat_nos)

    def _next_active_seat(self, start_after: int) -> int:
        active = self._active_seat_nos()
        if not active:
            raise BusinessError(code=400, i18n_key="poker.no_active_players")
        for s in active:
            if s > start_after:
                return s
        return active[0]

    def _first_to_act_preflop(
        self, *, active: list[int], bb_seat: int, sb_seat: int, button: int
    ) -> int:
        # Heads-up: SB (button) acts first preflop.
        if len(active) == 2:
            return sb_seat
        return self._next_active_seat(bb_seat)

    def _first_to_act_postflop(
        self, *, active: list[int], button: int, bb_seat: int
    ) -> int:
        # Heads-up: BB acts first postflop.
        if len(active) == 2:
            return bb_seat
        return self._next_active_seat(button)

    def _active_in_hand(self, hand: HandState) -> list[int]:
        return sorted([s for s, p in hand.players.items() if not p.folded])

    def _active_can_act(self, hand: HandState) -> list[int]:
        return sorted(
            [s for s, p in hand.players.items() if not p.folded and not p.all_in]
        )

    def _reset_betting_round(self, *, hand: HandState, acting_seat: int) -> None:
        for ps in hand.players.values():
            ps.committed_round = 0
        hand.current_bet = 0
        hand.min_raise_to = max(1, int(self.state.config.bb))
        hand.acting_seat = acting_seat
        # Everyone who can act (including acting_seat) must take an action.
        hand.pending_to_act = set(self._active_can_act(hand))
        now_ms = int(time.time() * 1000)
        hand.action_deadline_ms = now_ms + int(
            self.state.config.action_timeout_sec * 1000
        )
        hand.action_token += 1

    def _compute_side_pots(self, hand: HandState) -> list[dict[str, Any]]:
        contrib = {seat_no: ps.committed for seat_no, ps in hand.players.items()}
        levels = sorted({amt for amt in contrib.values() if amt > 0})
        pots: list[dict[str, Any]] = []
        prev = 0
        for lvl in levels:
            participants = [s for s, a in contrib.items() if a >= lvl]
            if not participants:
                continue
            amount = (lvl - prev) * len(participants)
            eligible = [s for s in participants if not hand.players[s].folded]
            pots.append({"amount": amount, "eligible_seats": eligible})
            prev = lvl
        return pots

    async def _maybe_start_hand(self) -> None:
        async with self._locked_state():
            if self.state.hand is not None:
                return
            active = self._active_seat_nos()
            if len(active) < 2:
                return

            # Determine button.
            if self.state.last_button_seat is None:
                button = active[0]
            else:
                button = self._next_active_seat(self.state.last_button_seat)
            if len(active) == 2:
                sb_seat = button
                bb_seat = self._next_active_seat(sb_seat)
            else:
                sb_seat = self._next_active_seat(button)
                bb_seat = self._next_active_seat(sb_seat)

            cfg = self.state.config
            pot = 0
            players: dict[int, HandPlayerState] = {}
            for seat_no in active:
                seat = self.state.seats[seat_no]
                players[seat_no] = HandPlayerState(
                    seat_no=seat_no,
                    user_id=seat.user_id,
                    committed=0,
                    committed_round=0,
                    folded=False,
                    all_in=False,
                )

            hand_id = uuid.uuid4().hex

            # Commit–reveal + deterministic deck.
            used_player_ids = [self.state.seats[s].user_id for s in active]
            deck_mgr = DeckManager(
                table_id=self.state.table_id,
                hand_id=hand_id,
                used_player_ids=used_player_ids,
            )
            audit = deck_mgr.commit()
            deck = list(deck_mgr._deck or [])
            server_seed_hex = deck_mgr.reveal()

            # Post antes
            if int(cfg.ante) > 0:
                for seat_no in active:
                    ante_amt = min(int(cfg.ante), self.state.seats[seat_no].stack)
                    self.state.seats[seat_no].stack -= ante_amt
                    players[seat_no].committed += ante_amt
                    players[seat_no].committed_round += ante_amt
                    pot += ante_amt
                    if self.state.seats[seat_no].stack == 0:
                        players[seat_no].all_in = True

            # Post blinds
            sb_amt = min(cfg.sb, self.state.seats[sb_seat].stack)
            bb_amt = min(cfg.bb, self.state.seats[bb_seat].stack)

            self.state.seats[sb_seat].stack -= sb_amt
            self.state.seats[bb_seat].stack -= bb_amt
            players[sb_seat].committed += sb_amt
            players[bb_seat].committed += bb_amt
            players[sb_seat].committed_round += sb_amt
            players[bb_seat].committed_round += bb_amt
            if self.state.seats[sb_seat].stack == 0:
                players[sb_seat].all_in = True
            if self.state.seats[bb_seat].stack == 0:
                players[bb_seat].all_in = True
            pot += sb_amt + bb_amt

            # Optional straddle
            straddle_seat: int | None = None
            straddle_amt: int = 0
            if bool(cfg.straddle) and len(active) >= 3:
                straddle_seat = self._next_active_seat(bb_seat)
                straddle_amt = min(
                    int(cfg.bb) * 2, self.state.seats[straddle_seat].stack
                )
                self.state.seats[straddle_seat].stack -= straddle_amt
                players[straddle_seat].committed += straddle_amt
                players[straddle_seat].committed_round += straddle_amt
                if self.state.seats[straddle_seat].stack == 0:
                    players[straddle_seat].all_in = True
                pot += straddle_amt

            # Deal hole cards (private per user)
            hole_cards: dict[int, list[str]] = {}
            for seat_no in active:
                uid = self.state.seats[seat_no].user_id
                hole_cards[uid] = [deck.pop(), deck.pop()]

            # Determine first to act.
            current_bet = int(bb_amt)
            if straddle_seat is not None and straddle_amt > current_bet:
                current_bet = int(straddle_amt)
            acting = self._first_to_act_preflop(
                active=active, bb_seat=bb_seat, sb_seat=sb_seat, button=button
            )
            # Everyone who can act (including acting) must take an action.
            pending = {s for s, p in players.items() if not p.folded and not p.all_in}

            now_ms = int(time.time() * 1000)
            deadline = now_ms + int(cfg.action_timeout_sec * 1000)

            hand = HandState(
                hand_id=hand_id,
                street="PREFLOP",
                button_seat=button,
                sb_seat=sb_seat,
                bb_seat=bb_seat,
                pot=pot,
                current_bet=current_bet,
                min_raise_to=(
                    max(current_bet * 2, current_bet + int(cfg.bb))
                    if current_bet > 0
                    else int(cfg.bb)
                ),
                acting_seat=acting,
                action_deadline_ms=deadline,
                pending_to_act=pending,
                players=players,
                hole_cards=hole_cards,
                board=[],
                deck=deck,
                burned=[],
                algo_version=audit.algo_version,
                server_seed_hash=audit.server_seed_hash,
                server_seed_hex=server_seed_hex,
                deck_hash=audit.deck_hash,
                action_token=0,
            )
            self.state.hand = hand
            self.state.last_button_seat = button

            await self.emit(
                "HAND_SEED_COMMIT",
                {
                    "hand_id": hand.hand_id,
                    "algo_version": audit.algo_version,
                    "server_seed_hash": audit.server_seed_hash,
                },
            )
            await self.emit(
                "HAND_DECK_COMMIT",
                {
                    "hand_id": hand.hand_id,
                    "deck_hash": audit.deck_hash,
                    "used_player_ids": used_player_ids,
                },
            )

            await self.emit(
                "HAND_STARTED",
                {
                    "hand_id": self.state.hand.hand_id,
                    "street": "PREFLOP",
                    "button_seat": button,
                    "sb_seat": sb_seat,
                    "bb_seat": bb_seat,
                },
            )
            await self.emit(
                "BLINDS_POSTED",
                {
                    "hand_id": self.state.hand.hand_id,
                    "ante": int(cfg.ante),
                    "sb_seat": sb_seat,
                    "sb": sb_amt,
                    "bb_seat": bb_seat,
                    "bb": bb_amt,
                    "straddle_seat": straddle_seat,
                    "straddle": straddle_amt if straddle_seat is not None else 0,
                    "pot": pot,
                },
            )

            # Emit private hole cards per user with public redaction.
            for seat_no in active:
                uid = self.state.seats[seat_no].user_id
                cards = hole_cards.get(uid) or []
                await self.emit(
                    "HOLE_CARDS_DEALT",
                    {
                        "hand_id": hand.hand_id,
                        "seat_no": seat_no,
                        "user_id": uid,
                        "cards": cards,
                    },
                    visibility="private",
                    audience_user_ids=[uid],
                    public_payload={
                        "hand_id": hand.hand_id,
                        "seat_no": seat_no,
                        "user_id": uid,
                        "count": len(cards),
                    },
                )

            await self._emit_action_request()

    async def _emit_action_request(self) -> None:
        hand = self.state.hand
        if hand is None:
            return
        seat = self.state.seats.get(hand.acting_seat)
        if seat is None:
            return
        ps = hand.players.get(hand.acting_seat)
        if ps is None:
            return
        to_call = max(0, hand.current_bet - ps.committed_round)
        await self.emit(
            "ACTION_REQUESTED",
            {
                "hand_id": hand.hand_id,
                "seat_no": hand.acting_seat,
                "user_id": seat.user_id,
                "action_token": hand.action_token,
                "to_call": to_call,
                "current_bet": hand.current_bet,
                "min_raise_to": hand.min_raise_to,
                "deadline_ms": hand.action_deadline_ms,
                "street": hand.street,
            },
        )

        # Dev/testing: auto-act for bot users (user_id < 0) to keep hands flowing.
        if int(seat.user_id) < 0:
            asyncio.create_task(
                self._bot_auto_act_if_needed(
                    user_id=int(seat.user_id),
                    expected_hand_id=str(hand.hand_id),
                    expected_action_token=int(hand.action_token),
                )
            )

    async def _bot_auto_act_if_needed(
        self,
        *,
        user_id: int,
        expected_hand_id: str,
        expected_action_token: int,
    ) -> None:
        # Yield once to let the current lock section finish.
        await asyncio.sleep(0)

        delay_ms = int(getattr(settings, "POKER_BOTS_ACTION_DELAY_MS", 0) or 0)
        if delay_ms > 0:
            await asyncio.sleep(delay_ms / 1000.0)

        try:
            async with self._lock:
                hand = self.state.hand
                if hand is None:
                    return
                if str(hand.hand_id) != str(expected_hand_id):
                    return
                if int(hand.action_token) != int(expected_action_token):
                    return

                seat = self.state.seats.get(int(hand.acting_seat))
                if seat is None or int(seat.user_id) != int(user_id):
                    return

                ps = hand.players.get(int(hand.acting_seat))
                if ps is None or ps.folded or ps.all_in:
                    return

                to_call = max(0, int(hand.current_bet) - int(ps.committed_round))
                min_raise_to = max(0, int(hand.min_raise_to))
                can_raise = (
                    int(seat.stack) > 0
                    and (int(ps.committed_round) + int(seat.stack)) >= int(min_raise_to)
                    and int(min_raise_to) > 0
                )

                raise_prob = float(getattr(settings, "POKER_BOTS_RAISE_PROB", 0.10) or 0.10)
                fold_prob = float(
                    getattr(settings, "POKER_BOTS_FOLD_PROB_FACING_BET", 0.20) or 0.20
                )

                rng = random.Random(f"{hand.hand_id}:{user_id}:{hand.action_token}")
                action: str
                amount: int | None

                if to_call == 0:
                    if can_raise and rng.random() < raise_prob:
                        action, amount = "raise_to", int(min_raise_to)
                    else:
                        action, amount = "check", None
                else:
                    if rng.random() < fold_prob:
                        action, amount = "fold", None
                    elif can_raise and rng.random() < raise_prob:
                        action, amount = "raise_to", int(min_raise_to)
                    else:
                        action, amount = "call", None

            await self.handle_action(
                user_id=user_id,
                action=action,
                amount=amount,
                client_action_id=None,
                action_token=expected_action_token,
                is_auto=True,
            )
        except Exception:
            # Best-effort; ignore if state moved on.
            return

    async def dev_fill_bots(
        self,
        *,
        count: int,
        buyin: int,
        username_prefix: str = "bot",
    ) -> list[int]:
        """Dev/testing helper: create and seat bot players.

        Bots are represented by negative user_ids (e.g., -1, -2, ...).
        """
        async with self._locked_state():
            return await self._fill_bots_locked(
                count=int(count),
                buyin=int(buyin),
                username_prefix=str(username_prefix),
            )

    async def handle_action(
        self,
        *,
        user_id: int,
        action: str,
        amount: int | None = None,
        client_action_id: str | None = None,
        action_token: int | None = None,
        is_auto: bool = False,
    ) -> None:
        action_norm = str(action or "").lower()
        if action_norm not in {"fold", "call", "check", "raise_to"}:
            raise BusinessError(
                code=400,
                i18n_key="poker.invalid_action",
                params={"action": action_norm},
            )

        async with self._locked_state():
            hand = self.state.hand
            if hand is None:
                raise BusinessError(code=409, i18n_key="poker.no_active_hand")

            seat_no = None
            for s_no, s in self.state.seats.items():
                if s.user_id == user_id:
                    seat_no = s_no
                    break
            if seat_no is None:
                raise BusinessError(code=404, i18n_key="poker.not_in_table")

            if seat_no != hand.acting_seat:
                raise BusinessError(code=409, i18n_key="poker.not_your_turn")

            if not is_auto and action_token is not None:
                try:
                    token_i = int(action_token)
                except Exception:
                    raise BusinessError(code=400, i18n_key="poker.invalid_action_token")
                if token_i != int(hand.action_token):
                    raise BusinessError(code=409, i18n_key="poker.invalid_action_token")

            now_ms = int(time.time() * 1000)
            if not is_auto and now_ms > hand.action_deadline_ms:
                raise BusinessError(code=409, i18n_key="poker.action_timeout")

            ps = hand.players[seat_no]
            if ps.folded or ps.all_in:
                raise BusinessError(code=409, i18n_key="poker.player_not_active")

            seat = self.state.seats[seat_no]
            to_call = max(0, hand.current_bet - ps.committed_round)

            contributed = 0
            raised = False

            if action_norm == "fold":
                ps.folded = True
                hand.pending_to_act.discard(seat_no)

            elif action_norm == "check":
                if to_call != 0:
                    raise BusinessError(code=400, i18n_key="poker.cannot_check")
                hand.pending_to_act.discard(seat_no)

            elif action_norm == "call":
                pay = min(to_call, seat.stack)
                seat.stack -= pay
                contributed = pay
                ps.committed += pay
                ps.committed_round += pay
                hand.pot += pay
                if seat.stack == 0:
                    ps.all_in = True
                hand.pending_to_act.discard(seat_no)

            elif action_norm == "raise_to":
                if amount is None:
                    raise BusinessError(code=400, i18n_key="poker.amount_required")
                target = int(amount)
                if target <= hand.current_bet:
                    raise BusinessError(code=400, i18n_key="poker.raise_too_small")
                if target < hand.min_raise_to:
                    raise BusinessError(
                        code=400,
                        i18n_key="poker.raise_below_min",
                        params={"min_raise_to": hand.min_raise_to},
                    )

                # target is bet size for this round.
                need = max(0, target - ps.committed_round)
                pay = min(need, seat.stack)
                seat.stack -= pay
                contributed = pay
                ps.committed += pay
                ps.committed_round += pay
                hand.pot += pay

                prev_bet = hand.current_bet
                new_bet = ps.committed_round
                if new_bet > prev_bet:
                    raise_size = new_bet - prev_bet
                    hand.current_bet = new_bet
                    hand.min_raise_to = new_bet + raise_size
                    raised = True
                if seat.stack == 0:
                    ps.all_in = True

                # Reset pending to act on raise.
                active = {
                    s for s, p in hand.players.items() if not p.folded and not p.all_in
                }
                hand.pending_to_act = set(active)
                hand.pending_to_act.discard(seat_no)

            await self.emit(
                "ACTION_TAKEN",
                {
                    "hand_id": hand.hand_id,
                    "seat_no": seat_no,
                    "user_id": user_id,
                    "street": hand.street,
                    "action": action_norm,
                    "amount": amount,
                    "contributed": contributed,
                    "pot": hand.pot,
                    "client_action_id": client_action_id,
                    "auto": is_auto,
                    "raised": raised,
                },
            )

            # If player is all-in, they no longer need actions.
            if ps.all_in:
                hand.pending_to_act.discard(seat_no)

            # Advance game.
            await self._advance_after_action_locked(now_ms)

            # If still running, request next action.
            if self.state.hand is not None:
                await self._emit_action_request()

        # Auto-continue: if the hand ended, try to start the next one.
        # This must run outside the locked section to avoid deadlocks.
        if self._auto_start_hands and self.state.hand is None:
            await self._maybe_start_hand()

    async def _advance_after_action_locked(self, now_ms: int) -> None:
        hand = self.state.hand
        if hand is None:
            return

        # Check if only one player remains.
        active_seats = [s for s, p in hand.players.items() if not p.folded]
        if len(active_seats) <= 1:
            winner_seat = active_seats[0] if active_seats else None
            if winner_seat is not None:
                self.state.seats[winner_seat].stack += hand.pot
            winner_user_id = (
                self.state.seats[winner_seat].user_id if winner_seat else None
            )
            hand_id = hand.hand_id
            pot = hand.pot
            # Reveal seed even if ended by folds.
            await self.emit(
                "HAND_SEED_REVEALED",
                {
                    "hand_id": hand.hand_id,
                    "algo_version": hand.algo_version,
                    "server_seed_hash": hand.server_seed_hash,
                    "server_seed": hand.server_seed_hex,
                    "deck_hash": hand.deck_hash,
                },
            )
            self.state.hand = None
            await self.emit(
                "HAND_ENDED",
                {
                    "hand_id": hand_id,
                    "winner_seat": winner_seat,
                    "winner_user_id": winner_user_id,
                    "pot": pot,
                },
            )
            return

        # If no one can act (everyone left is all-in), auto-runout to showdown.
        if not self._active_can_act(hand):
            await self._runout_to_showdown_locked(now_ms)
            return

        # Betting round ended when no pending seats.
        if not hand.pending_to_act:
            await self._advance_street_locked(now_ms)
            return

        # Move to next active seat.
        next_seat = hand.acting_seat
        for _ in range(self.state.max_players + 1):
            next_seat = self._next_active_seat(next_seat)
            p = hand.players.get(next_seat)
            if p is None:
                continue
            if p.folded or p.all_in:
                continue
            if next_seat not in hand.pending_to_act:
                continue
            hand.acting_seat = next_seat
            hand.action_deadline_ms = now_ms + int(
                self.state.config.action_timeout_sec * 1000
            )
            hand.action_token += 1
            return

        # Fallback: if can't find a seat, end round.
        hand.pending_to_act.clear()

    async def _advance_street_locked(self, now_ms: int) -> None:
        hand = self.state.hand
        if hand is None:
            return

        # Round milestone.
        await self.emit(
            f"{hand.street}_COMPLETED",
            {"hand_id": hand.hand_id, "street": hand.street},
        )

        # Move to next street or showdown.
        if hand.street == "PREFLOP":
            hand.street = "FLOP"
            # burn 1, deal 3
            if hand.deck:
                hand.burned.append(hand.deck.pop())
            flop = [hand.deck.pop(), hand.deck.pop(), hand.deck.pop()]
            hand.board.extend(flop)
            await self.emit(
                "STREET_DEALT",
                {"hand_id": hand.hand_id, "street": "FLOP", "board": list(hand.board)},
            )
        elif hand.street == "FLOP":
            hand.street = "TURN"
            if hand.deck:
                hand.burned.append(hand.deck.pop())
            turn = hand.deck.pop()
            hand.board.append(turn)
            await self.emit(
                "STREET_DEALT",
                {"hand_id": hand.hand_id, "street": "TURN", "board": list(hand.board)},
            )
        elif hand.street == "TURN":
            hand.street = "RIVER"
            if hand.deck:
                hand.burned.append(hand.deck.pop())
            river = hand.deck.pop()
            hand.board.append(river)
            await self.emit(
                "STREET_DEALT",
                {"hand_id": hand.hand_id, "street": "RIVER", "board": list(hand.board)},
            )
        elif hand.street == "RIVER":
            await self._showdown_locked()
            return
        else:
            await self._showdown_locked()
            return

        # Setup next betting round.
        active = self._active_in_hand(hand)
        acting = self._first_to_act_postflop(
            active=active, button=hand.button_seat, bb_seat=hand.bb_seat
        )
        self._reset_betting_round(hand=hand, acting_seat=acting)
        # Caller will emit ACTION_REQUESTED.

    async def _runout_to_showdown_locked(self, now_ms: int) -> None:
        hand = self.state.hand
        if hand is None:
            return

        # Deal remaining streets with burns.
        if hand.street == "PREFLOP":
            # FLOP
            if hand.deck:
                hand.burned.append(hand.deck.pop())
            hand.board.extend([hand.deck.pop(), hand.deck.pop(), hand.deck.pop()])
            hand.street = "FLOP"
            await self.emit(
                "STREET_DEALT",
                {"hand_id": hand.hand_id, "street": "FLOP", "board": list(hand.board)},
            )
        if hand.street == "FLOP":
            if hand.deck:
                hand.burned.append(hand.deck.pop())
            hand.board.append(hand.deck.pop())
            hand.street = "TURN"
            await self.emit(
                "STREET_DEALT",
                {"hand_id": hand.hand_id, "street": "TURN", "board": list(hand.board)},
            )
        if hand.street == "TURN":
            if hand.deck:
                hand.burned.append(hand.deck.pop())
            hand.board.append(hand.deck.pop())
            hand.street = "RIVER"
            await self.emit(
                "STREET_DEALT",
                {"hand_id": hand.hand_id, "street": "RIVER", "board": list(hand.board)},
            )

        await self._showdown_locked()

    async def _showdown_locked(self) -> None:
        hand = self.state.hand
        if hand is None:
            return

        eligible_seats = [s for s, p in hand.players.items() if not p.folded]
        side_pots = self._compute_side_pots(hand)

        payouts: dict[int, int] = {s: 0 for s in hand.players.keys()}
        ranks: dict[int, tuple[int, tuple[int, ...]]] = {}

        for seat_no in eligible_seats:
            uid = hand.players[seat_no].user_id
            hole = hand.hole_cards.get(uid) or []
            cards7 = list(hole) + list(hand.board)
            if len(cards7) != 7:
                continue
            ranks[seat_no] = rank_seven(cards7).as_tuple()

        for pot in side_pots:
            amount = int(pot["amount"])
            eligible = [s for s in pot["eligible_seats"] if s in ranks]
            if not eligible:
                continue
            best = max(ranks[s] for s in eligible)
            winners = sorted([s for s in eligible if ranks[s] == best])
            if not winners:
                continue
            share = amount // len(winners)
            rem = amount - (share * len(winners))
            for s in winners:
                payouts[s] += share
            # Deterministic remainder distribution: from lowest seat_no.
            for i in range(rem):
                payouts[winners[i % len(winners)]] += 1

        # Apply payouts
        for seat_no, amt in payouts.items():
            if amt <= 0:
                continue
            if seat_no in self.state.seats:
                self.state.seats[seat_no].stack += amt

        await self.emit(
            "SHOWDOWN",
            {
                "hand_id": hand.hand_id,
                "board": list(hand.board),
                "payouts": {str(k): v for k, v in payouts.items() if v > 0},
                "side_pots": side_pots,
            },
        )

        # Reveal seed now (commit–reveal)
        await self.emit(
            "HAND_SEED_REVEALED",
            {
                "hand_id": hand.hand_id,
                "algo_version": hand.algo_version,
                "server_seed_hash": hand.server_seed_hash,
                "server_seed": hand.server_seed_hex,
                "deck_hash": hand.deck_hash,
            },
        )

        hand_id = hand.hand_id
        self.state.hand = None
        await self.emit(
            "HAND_ENDED",
            {
                "hand_id": hand_id,
                "payouts": {str(k): v for k, v in payouts.items() if v > 0},
            },
        )

    async def check_and_handle_timeout(self, now_ms: int) -> bool:
        """Return True if an auto action was performed."""
        async with self._lock:
            hand = self.state.hand
            if hand is None:
                return False
            if now_ms <= hand.action_deadline_ms:
                return False
            seat_no = hand.acting_seat
            ps = hand.players.get(seat_no)
            if ps is None or ps.folded or ps.all_in:
                return False
            to_call = max(0, hand.current_bet - ps.committed)
            auto_action = "check" if to_call == 0 else "fold"
            acting_user_id = self.state.seats[seat_no].user_id

        await self.handle_action(
            user_id=acting_user_id,
            action=auto_action,
            amount=None,
            client_action_id=None,
            action_token=None,
            is_auto=True,
        )
        return True


class PokerManager:
    def __init__(self) -> None:
        self._tables: dict[str, PokerTable] = {}
        self._lock = asyncio.Lock()
        self._event_store: EventStore | None = None
        self._timeout_task: asyncio.Task | None = None

    async def start(self) -> None:
        self._event_store = EventStore(redis=cache_manager.redis)

        async def _timeout_loop() -> None:
            try:
                while True:
                    await asyncio.sleep(0.5)
                    now_ms = int(time.time() * 1000)
                    async with self._lock:
                        tables = list(self._tables.values())
                    for t in tables:
                        try:
                            await t.check_and_handle_timeout(now_ms)
                        except Exception:
                            continue
            except asyncio.CancelledError:
                return

        self._timeout_task = asyncio.create_task(_timeout_loop())

    async def stop(self) -> None:
        if self._timeout_task is not None:
            self._timeout_task.cancel()
            self._timeout_task = None

    async def reset_for_tests(self) -> None:
        async with self._lock:
            self._tables = {}
        # Keep redis data intact in tests (redis is typically disabled).

    async def timeout_tick_for_tests(self, now_ms: int) -> None:
        async with self._lock:
            tables = list(self._tables.values())
        for t in tables:
            await t.check_and_handle_timeout(now_ms)

    async def create_table(
        self, name: str, max_players: int, config: TableConfig
    ) -> PokerTable:
        table_id = uuid.uuid4().hex
        if self._event_store is None:
            self._event_store = EventStore(redis=cache_manager.redis)
        table = PokerTable(
            table_id=table_id,
            name=name,
            max_players=max_players,
            config=config,
            event_store=self._event_store,
        )
        async with self._lock:
            self._tables[table_id] = table

        # Persist the initial state for multi-instance discovery.
        try:
            async with table._locked_state():
                pass
        except Exception:
            pass
        return table

    def _is_match_for_max_chips(self, *, cfg: TableConfig, max_chips: int) -> bool:
        return cfg.min_buyin <= max_chips <= cfg.max_buyin

    def _table_has_capacity(self, *, max_players: int, seated_count: int) -> bool:
        return seated_count < max_players

    async def quick_start_table(self, *, max_chips: int) -> PokerTable:
        """Pick a suitable table for the player based on max chips (buy-in range).

        Preference: existing table where min_buyin <= max_chips <= max_buyin and has capacity.
        Tie-break: smaller max_buyin first, then fewer seated players.
        If none matches, create a new table sized to (min_buyin..max_buyin) around max_chips.
        """

        if max_chips <= 0:
            raise BusinessError(code=400, i18n_key="errors.bad_request")

        best_id: str | None = None
        best_key: tuple[int, int] | None = None  # (max_buyin, seated_count)

        # Multi-instance: scan redis registry if available.
        if cache_manager.redis is not None:
            ids = await cache_manager.redis.smembers("poker:tables")
            for table_id in ids:
                raw = await cache_manager.redis.get(f"poker:table:{table_id}:state")
                if not raw:
                    continue
                try:
                    data = json.loads(raw)
                    cfg = data.get("config") or {}
                    t = data.get("table") or {}
                    seats = data.get("seats") or {}
                    max_players = int(t.get("max_players") or 0)
                    seated_count = len(seats)
                    table_cfg = TableConfig(
                        sb=int(cfg.get("sb") or 1),
                        bb=int(cfg.get("bb") or 2),
                        ante=int(cfg.get("ante") or 0),
                        straddle=bool(cfg.get("straddle") or False),
                        min_buyin=int(cfg.get("min_buyin") or 40),
                        max_buyin=int(cfg.get("max_buyin") or 200),
                        action_timeout_sec=int(cfg.get("action_timeout_sec") or 20),
                        timebank_sec=int(cfg.get("timebank_sec") or 60),
                    )
                except Exception:
                    continue

                if max_players <= 0:
                    continue
                if not self._table_has_capacity(
                    max_players=max_players, seated_count=seated_count
                ):
                    continue
                if not self._is_match_for_max_chips(cfg=table_cfg, max_chips=max_chips):
                    continue

                key = (int(table_cfg.max_buyin), int(seated_count))
                if best_key is None or key < best_key:
                    best_key = key
                    best_id = str(table_id)

            if best_id:
                return await self.get_table(best_id)

        # Single-instance in-memory scan.
        async with self._lock:
            tables = list(self._tables.values())

        for t in tables:
            cfg = t.state.config
            if not self._table_has_capacity(
                max_players=t.state.max_players, seated_count=len(t.state.seats)
            ):
                continue
            if not self._is_match_for_max_chips(cfg=cfg, max_chips=max_chips):
                continue
            key = (int(cfg.max_buyin), int(len(t.state.seats)))
            if best_key is None or key < best_key:
                best_key = key
                best_id = t.state.table_id

        if best_id:
            return await self.get_table(best_id)

        # No match: create a table.
        # Prefer PRD lobby levels when the bankroll falls into a defined range.
        lvl = find_lobby_level_for_max_chips(max_chips)
        if lvl is not None:
            return await self.create_table(name=lvl.name, max_players=9, config=lvl.config)

        # Fallback: size to the player's bankroll (legacy behavior / dev).
        min_buyin = min(40, max_chips)
        if min_buyin <= 0:
            min_buyin = 1
        max_buyin = max_chips
        if min_buyin > max_buyin:
            min_buyin = max_buyin

        cfg = TableConfig(min_buyin=min_buyin, max_buyin=max_buyin)
        name = f"QS {min_buyin}-{max_buyin}"
        return await self.create_table(name=name, max_players=9, config=cfg)

    async def get_table(self, table_id: str) -> PokerTable:
        async with self._lock:
            table = self._tables.get(table_id)
        if table:
            return table

        # Multi-instance: lazy-load from redis snapshot when available.
        if cache_manager.redis is not None:
            raw = await cache_manager.redis.get(f"poker:table:{table_id}:state")
            if raw:
                if self._event_store is None:
                    self._event_store = EventStore(redis=cache_manager.redis)
                tmp = PokerTable(
                    table_id=table_id,
                    name="(loaded)",
                    max_players=9,
                    config=TableConfig(),
                    event_store=self._event_store,
                )
                try:
                    tmp._load_state(json.loads(raw))
                except Exception:
                    raise BusinessError(code=404, i18n_key="poker.table_not_found")
                async with self._lock:
                    self._tables[table_id] = tmp
                return tmp

        raise BusinessError(code=404, i18n_key="poker.table_not_found")

    async def list_tables(self) -> list[dict[str, Any]]:
        # Multi-instance: if redis is available, list tables from registry.
        if cache_manager.redis is not None:
            ids = await cache_manager.redis.smembers("poker:tables")
            result: list[dict[str, Any]] = []
            for table_id in sorted(ids):
                raw = await cache_manager.redis.get(f"poker:table:{table_id}:state")
                if not raw:
                    continue
                try:
                    data = json.loads(raw)
                    t = data.get("table") or {}
                    members = data.get("members") or {}
                    seats = data.get("seats") or {}
                    result.append(
                        {
                            "table_id": str(t.get("table_id") or table_id),
                            "name": str(t.get("name") or ""),
                            "max_players": int(t.get("max_players") or 0),
                            "players_count": len(members),
                            "seated_count": len(seats),
                            "created_at": float(t.get("created_at") or 0),
                        }
                    )
                except Exception:
                    continue
            return result

        async with self._lock:
            tables = list(self._tables.values())
        return [
            {
                "table_id": t.state.table_id,
                "name": t.state.name,
                "max_players": t.state.max_players,
                "players_count": len(t.state.members),
                "seated_count": len(t.state.seats),
                "created_at": t.state.created_at,
            }
            for t in tables
        ]


poker_manager = PokerManager()
