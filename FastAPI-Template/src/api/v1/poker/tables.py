import json

from fastapi import APIRouter

from core.dependency import DependAuth
from poker.manager import TableConfig
from poker import poker_manager
from poker.lobby import DEFAULT_LOBBY_LEVELS, find_lobby_level_for_config, find_lobby_level_for_max_chips
from core.exceptions import BusinessError
from schemas import Success
from schemas.poker import (
    PokerBuyInIn,
    PokerJoinOut,
    PokerQuickStartIn,
    PokerSeatIn,
    PokerTableCreateIn,
)
from services.subscription_tier import (
    SubscriptionTier,
    TIER_POLICY,
    get_user_effective_tier,
    require_user_min_tier,
    require_within_wallet_cap,
)
from repositories.wallet import user_wallet_repository
from settings.config import settings

router = APIRouter()


def _ok_response_example(data):
    return {
        200: {
            "description": "OK",
            "content": {
                "application/json": {
                    "example": {"code": 200, "msg": "OK", "data": data}
                }
            },
        }
    }


def _fail_response_example(code: int, error_key: str):
    return {
        code: {
            "description": "Error",
            "content": {
                "application/json": {
                    "example": {
                        "code": code,
                        "msg": "Error",
                        "data": None,
                        "error_key": error_key,
                        "error_params": None,
                    }
                }
            },
        }
    }


@router.get(
    "/list",
    summary="牌桌列表",
    dependencies=[DependAuth],
    responses=_ok_response_example(
        [
            {
                "table_id": "tb_123",
                "name": "Texas Table",
                "max_players": 9,
                "players_count": 3,
                "seated_count": 2,
                "created_at": 1735180000.123,
            }
        ]
    ),
)
async def list_tables():
    tables = await poker_manager.list_tables()
    result = Success(data=tables)
    return json.loads(result.body)


@router.get(
    "/lobby_levels",
    summary="大厅桌档位(按筹码区间分配)",
    dependencies=[DependAuth],
    responses=_ok_response_example(
        [
            {
                "level": 1,
                "min_buyin": 150000,
                "max_buyin": 750000,
                "sb": 2500,
                "bb": 5000,
                "ante": 1500,
                "is_vip": False,
            }
        ]
    ),
)
async def lobby_levels():
    result = Success(
        data=[
            {
                "level": lvl.level,
                "min_buyin": lvl.min_buyin,
                "max_buyin": lvl.max_buyin,
                "sb": lvl.sb,
                "bb": lvl.bb,
                "ante": lvl.ante,
                "is_vip": lvl.is_vip,
            }
            for lvl in DEFAULT_LOBBY_LEVELS
        ]
    )
    return json.loads(result.body)


@router.post(
    "/create",
    summary="创建牌桌",
    dependencies=[DependAuth],
    responses=_ok_response_example({"table_id": "tb_123"}),
)
async def create_table(body: PokerTableCreateIn):
    cfg = TableConfig(**body.config.model_dump())
    table = await poker_manager.create_table(
        name=body.name, max_players=body.max_players, config=cfg
    )
    result = Success(data={"table_id": table.state.table_id})
    return json.loads(result.body)


@router.post(
    "/quick_start",
    summary="快速开始(自动分配牌桌)",
    dependencies=[DependAuth],
    responses=_ok_response_example({"table_id": "tb_123"}),
)
async def quick_start(body: PokerQuickStartIn, user=DependAuth):
    await require_within_wallet_cap(user_id=user.id, requested_chips=body.max_chips)

    lvl = find_lobby_level_for_max_chips(int(body.max_chips))
    if lvl is None:
        raise BusinessError(
            code=400,
            http_status=400,
            i18n_key="poker.max_chips_out_of_range",
            params={
                "min": DEFAULT_LOBBY_LEVELS[0].min_buyin,
                "max": DEFAULT_LOBBY_LEVELS[-1].max_buyin,
            },
        )

    if lvl.is_vip:
        await require_user_min_tier(user_id=user.id, required=SubscriptionTier.PRO, reason="vip_table")

    table = await poker_manager.quick_start_table(max_chips=int(body.max_chips))
    await table.ensure_member(user_id=user.id, username=user.username)

    # Optional automation helpers for testing.
    if body.auto_buyin is not None or bool(body.auto_seat) or int(body.fill_bots or 0) > 0:
        cfg = table.state.config
        desired_buyin = int(body.auto_buyin) if body.auto_buyin is not None else int(body.max_chips)
        # Clamp into table buy-in range.
        buyin_amount = max(int(cfg.min_buyin), min(int(cfg.max_buyin), desired_buyin))
        await require_within_wallet_cap(user_id=user.id, requested_chips=buyin_amount)
        await table.buyin(user_id=user.id, amount=buyin_amount)

        if bool(body.auto_seat):
            seat_no = None
            taken = {s.seat_no for s in table.state.seats.values()}
            for s in range(1, int(table.state.max_players) + 1):
                if s not in taken:
                    seat_no = s
                    break
            if seat_no is not None:
                await table.sit(user_id=user.id, seat_no=int(seat_no))

        fill_bots = int(body.fill_bots or 0)
        if fill_bots > 0:
            # Bot injection is intended for local testing only.
            if not bool(getattr(settings, "DEBUG", False)):
                raise BusinessError(code=403, http_status=403, i18n_key="common.forbidden")

            bot_buyin_raw = int(body.bot_buyin) if body.bot_buyin is not None else buyin_amount
            bot_buyin = max(int(cfg.min_buyin), min(int(cfg.max_buyin), bot_buyin_raw))
            await table.dev_fill_bots(count=fill_bots, buyin=bot_buyin)
    result = Success(data=PokerJoinOut(table_id=table.state.table_id).model_dump())
    return json.loads(result.body)


@router.get(
    "/{table_id}/config",
    summary="获取牌桌规则配置",
    dependencies=[DependAuth],
    responses=_ok_response_example(
        {
            "sb": 1,
            "bb": 2,
            "ante": 0,
            "straddle": False,
            "min_buyin": 40,
            "max_buyin": 200,
            "action_timeout_sec": 20,
            "timebank_sec": 60,
        }
    ),
)
async def get_table_config(table_id: str):
    table = await poker_manager.get_table(table_id)
    cfg = table.state.config
    result = Success(
        data={
            "sb": cfg.sb,
            "bb": cfg.bb,
            "ante": cfg.ante,
            "straddle": cfg.straddle,
            "min_buyin": cfg.min_buyin,
            "max_buyin": cfg.max_buyin,
            "action_timeout_sec": cfg.action_timeout_sec,
            "timebank_sec": cfg.timebank_sec,
        }
    )
    return json.loads(result.body)


@router.get(
    "/{table_id}",
    summary="获取牌桌快照",
    dependencies=[DependAuth],
    responses=_ok_response_example(
        {
            "table": {
                "table_id": "tb_123",
                "name": "Texas Table",
                "max_players": 9,
                "created_at": 1735180000.123,
                "seq": 12,
            },
            "config": {
                "sb": 1,
                "bb": 2,
                "ante": 0,
                "straddle": False,
                "min_buyin": 40,
                "max_buyin": 200,
                "action_timeout_sec": 20,
                "timebank_sec": 60,
            },
            "seats": [
                {
                    "seat_no": 3,
                    "user_id": 1002,
                    "username": "bob",
                    "stack": 180,
                    "status": "seated",
                }
            ],
            "members": [
                {
                    "user_id": 1001,
                    "username": "alice",
                    "status": "spectator",
                    "buyin": 0,
                    "seat_no": None,
                }
            ],
            "hand": {
                "hand_id": "hand_abc",
                "street": "PREFLOP",
                "button_seat": 6,
                "sb_seat": 7,
                "bb_seat": 8,
                "pot": 3,
                "current_bet": 2,
                "min_raise_to": 4,
                "acting_seat": 3,
                "action_deadline_ms": 1735180005123,
                "players": {
                    "3": {
                        "user_id": 1002,
                        "committed": 2,
                        "folded": False,
                        "all_in": False,
                    }
                },
            },
            "you": {"user_id": 1002, "hole_cards": ["As", "Kd"]},
        }
    ),
)
async def get_table_snapshot(table_id: str, user=DependAuth):
    table = await poker_manager.get_table(table_id)
    snapshot = await table.snapshot_for(user_id=user.id)
    result = Success(data=snapshot)
    return json.loads(result.body)


@router.get(
    "/{table_id}/events",
    summary="获取牌桌事件增量",
    dependencies=[DependAuth],
    responses={
        **_ok_response_example(
            {
                "events": [
                    {
                        "type": "PLAYER_JOINED",
                        "seq": 10,
                        "server_ts": 1735180000123,
                        "payload": {"user_id": 1001, "username": "alice"},
                    }
                ]
            }
        ),
        **_fail_response_example(400, "poker.invalid_since_seq"),
        **_fail_response_example(400, "poker.invalid_limit"),
    },
)
async def get_table_events(
    table_id: str, since_seq: int = 0, limit: int = 200, user=DependAuth
):
    if since_seq < 0:
        raise BusinessError(code=400, i18n_key="poker.invalid_since_seq")
    if limit <= 0:
        raise BusinessError(code=400, i18n_key="poker.invalid_limit")
    limit = min(int(limit), 500)

    table = await poker_manager.get_table(table_id)
    events = await table.fetch_events_since_for_user(
        user_id=user.id,
        last_seq=int(since_seq),
        limit=limit,
    )
    result = Success(data={"events": events})
    return json.loads(result.body)


@router.post(
    "/{table_id}/join",
    summary="进入牌桌(默认观战)",
    dependencies=[DependAuth],
    responses=_ok_response_example({"table_id": "tb_123"}),
)
async def join_table(table_id: str, user=DependAuth):
    table = await poker_manager.get_table(table_id)

    lvl = find_lobby_level_for_config(table.state.config)
    if lvl is not None and lvl.is_vip:
        await require_user_min_tier(user_id=user.id, required=SubscriptionTier.PRO, reason="vip_table")
    await table.ensure_member(user_id=user.id, username=user.username)
    result = Success(data=PokerJoinOut(table_id=table_id).model_dump())
    return json.loads(result.body)


@router.post(
    "/{table_id}/leave",
    summary="离开牌桌",
    dependencies=[DependAuth],
    responses=_ok_response_example(None),
)
async def leave_table(table_id: str, user=DependAuth):
    table = await poker_manager.get_table(table_id)

    cashout = await table.leave(user_id=user.id)
    if cashout > 0:
        wallet = await user_wallet_repository.get_or_create(user_id=user.id)
        tier_enum = await get_user_effective_tier(user_id=user.id)
        cap = int(TIER_POLICY[tier_enum].wallet_chip_cap)
        wallet.chips = min(int(wallet.chips) + int(cashout), cap)
        await wallet.save()
    result = Success(data=None)
    return json.loads(result.body)


@router.post(
    "/{table_id}/buyin",
    summary="买入/带入筹码",
    dependencies=[DependAuth],
    responses=_ok_response_example(None),
)
async def buyin(table_id: str, body: PokerBuyInIn, user=DependAuth):
    table = await poker_manager.get_table(table_id)

    # 买入触发点：超过钱包上限或 VIP 桌等级不足时，引导订阅升级
    await require_within_wallet_cap(user_id=user.id, requested_chips=body.amount)

    lvl = find_lobby_level_for_config(table.state.config)
    if lvl is not None and lvl.is_vip:
        await require_user_min_tier(user_id=user.id, required=SubscriptionTier.PRO, reason="vip_table")
    await table.ensure_member(user_id=user.id, username=user.username)

    # Validate buyin range before wallet mutation.
    cfg = table.state.config
    if int(body.amount) < int(cfg.min_buyin) or int(body.amount) > int(cfg.max_buyin):
        raise BusinessError(
            code=400,
            http_status=400,
            i18n_key="poker.buyin_out_of_range",
            params={"min": int(cfg.min_buyin), "max": int(cfg.max_buyin)},
        )

    # Wallet debit
    wallet = await user_wallet_repository.get_or_create(user_id=user.id)
    balance = int(wallet.chips)
    need = int(body.amount)
    if balance < need:
        raise BusinessError(
            code=400,
            http_status=400,
            i18n_key="wallet.insufficient_chips",
            params={"balance": balance, "required": need},
        )
    wallet.chips = balance - need
    await wallet.save()

    await table.buyin(user_id=user.id, amount=body.amount)
    result = Success(data=None)
    return json.loads(result.body)


@router.post(
    "/{table_id}/seat",
    summary="坐下",
    dependencies=[DependAuth],
    responses=_ok_response_example(None),
)
async def seat(table_id: str, body: PokerSeatIn, user=DependAuth):
    table = await poker_manager.get_table(table_id)
    await table.ensure_member(user_id=user.id, username=user.username)
    await table.sit(user_id=user.id, seat_no=body.seat_no)
    result = Success(data=None)
    return json.loads(result.body)


@router.post(
    "/{table_id}/spectate",
    summary="切换观战",
    dependencies=[DependAuth],
    responses=_ok_response_example(None),
)
async def spectate(table_id: str, user=DependAuth):
    table = await poker_manager.get_table(table_id)
    await table.ensure_member(user_id=user.id, username=user.username)

    cashout = await table.spectate(user_id=user.id)
    if cashout > 0:
        wallet = await user_wallet_repository.get_or_create(user_id=user.id)
        tier_enum = await get_user_effective_tier(user_id=user.id)
        cap = int(TIER_POLICY[tier_enum].wallet_chip_cap)
        wallet.chips = min(int(wallet.chips) + int(cashout), cap)
        await wallet.save()
    result = Success(data=None)
    return json.loads(result.body)


@router.post(
    "/{table_id}/sitout",
    summary="坐出",
    dependencies=[DependAuth],
    responses=_ok_response_example(None),
)
async def sitout(table_id: str, user=DependAuth):
    table = await poker_manager.get_table(table_id)
    await table.ensure_member(user_id=user.id, username=user.username)
    await table.sitout(user_id=user.id)
    result = Success(data=None)
    return json.loads(result.body)
