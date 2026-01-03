from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Query
from fastapi.encoders import jsonable_encoder

from core.dependency import DependAuth, DependPermisson
from models.admin import Message, User
from models.message_state import MessageUserState
from repositories.message import message_repository
from schemas import Fail, Success, SuccessExtra
from schemas.messages import (
    MarkAllReadOut,
    MarkReadOut,
    MessageCreate,
    MessageFeedItem,
    UnreadCountOut,
)
from schemas.response import PageResponse, ResponseBase
from settings.config import settings

example_response = {
    "code": 200,
    "msg": "OK",
    "data": [
        {
            "title": "系统公告",
            "content": "欢迎使用 FastAPI 模板，祝你开发顺利！",
            "time": "2025-12-09T08:00:00Z",
            "type": "info",
        }
    ],
    "total": 1,
    "page": 1,
    "page_size": 10,
}

router = APIRouter()


def _server_tz() -> ZoneInfo:
    tzname = "Asia/Shanghai"
    try:
        tzname = (settings.TORTOISE_ORM or {}).get("timezone") or tzname
    except Exception:
        tzname = "Asia/Shanghai"
    return ZoneInfo(tzname)


def _now() -> datetime:
    return datetime.now(_server_tz())


@router.get(
    "/list",
    summary="消息列表",
    response_model=PageResponse[list[MessageFeedItem]],
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json": {"example": example_response}},
        }
    },
)
async def list_messages(
    page: int = Query(1, ge=1, description="当前页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页数量"),
    unread_only: bool = Query(False, description="仅返回未读"),
    type: str | None = Query(None, description="消息类型过滤"),
    current_user: User = DependAuth,
):
    now = _now()
    deleted_ids = await MessageUserState.filter(
        user_id=current_user.id, is_deleted=True
    ).values_list("message_id", flat=True)

    query = Message.filter(send_time__lte=now)
    if deleted_ids:
        query = query.exclude(id__in=list(deleted_ids))
    if type:
        query = query.filter(type=type)

    total = await query.count()
    items = await query.offset((page - 1) * page_size).limit(page_size).order_by(
        "-send_time"
    )

    message_ids = [item.id for item in items]
    read_ids: set[int] = set()
    if message_ids:
        read_rows = await MessageUserState.filter(
            user_id=current_user.id,
            is_read=True,
            is_deleted=False,
            message_id__in=message_ids,
        ).values_list("message_id", flat=True)
        read_ids = set(read_rows)

    payload = jsonable_encoder(
        [
            {
                "id": item.id,
                "title": item.title,
                "content": item.content,
                "time": item.send_time,
                "type": item.type,
                "is_read": item.id in read_ids,
            }
            for item in items
        ]
    )

    if unread_only:
        payload = [row for row in payload if not row.get("is_read")]
        total = len(payload)

    return SuccessExtra(data=payload, total=total, page=page, page_size=page_size)


@router.get(
    "/unread_count",
    summary="未读消息数量",
    response_model=ResponseBase[UnreadCountOut],
)
async def unread_count(
    current_user: User = DependAuth,
    type: str | None = Query(None, description="消息类型过滤"),
):
    now = _now()
    deleted_ids = await MessageUserState.filter(
        user_id=current_user.id, is_deleted=True
    ).values_list("message_id", flat=True)

    query = Message.filter(send_time__lte=now)
    if deleted_ids:
        query = query.exclude(id__in=list(deleted_ids))
    if type:
        query = query.filter(type=type)

    visible_ids = await query.values_list("id", flat=True)
    if not visible_ids:
        return Success(data=UnreadCountOut(unread_count=0).model_dump())

    read_ids = await MessageUserState.filter(
        user_id=current_user.id,
        is_read=True,
        is_deleted=False,
        message_id__in=list(visible_ids),
    ).values_list("message_id", flat=True)

    unread = len(set(visible_ids) - set(read_ids))
    return Success(data=UnreadCountOut(unread_count=unread).model_dump())


@router.post(
    "/{message_id}/read",
    summary="标记消息已读",
    response_model=ResponseBase[MarkReadOut],
)
async def mark_read(message_id: int, current_user: User = DependAuth):
    msg = await Message.filter(id=message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="i18n:common.not_found")
    now = _now()
    if msg.send_time and msg.send_time > now:
        raise HTTPException(status_code=404, detail="i18n:common.not_found")

    state, _ = await MessageUserState.get_or_create(
        user_id=current_user.id, message_id=message_id
    )
    if not state.is_deleted:
        state.is_read = True
        state.read_at = now
        await state.save()

    return Success(data=MarkReadOut(message_id=message_id, is_read=True).model_dump())


@router.post(
    "/read_all",
    summary="全部标记已读",
    response_model=ResponseBase[MarkAllReadOut],
)
async def mark_all_read(current_user: User = DependAuth):
    now = _now()
    deleted_ids = await MessageUserState.filter(
        user_id=current_user.id, is_deleted=True
    ).values_list("message_id", flat=True)

    visible_query = Message.filter(send_time__lte=now)
    if deleted_ids:
        visible_query = visible_query.exclude(id__in=list(deleted_ids))

    visible_ids = await visible_query.values_list("id", flat=True)
    if not visible_ids:
        return Success(data=MarkAllReadOut(marked=0).model_dump())

    # 先更新已有状态
    updated = await MessageUserState.filter(
        user_id=current_user.id,
        is_deleted=False,
        is_read=False,
        message_id__in=list(visible_ids),
    ).update(is_read=True, read_at=now)

    # 再为缺失状态的消息补齐记录（稀疏写入）
    existing_ids = await MessageUserState.filter(
        user_id=current_user.id,
        message_id__in=list(visible_ids),
    ).values_list("message_id", flat=True)

    missing_ids = list(set(visible_ids) - set(existing_ids))
    if missing_ids:
        await MessageUserState.bulk_create(
            [
                MessageUserState(
                    user_id=current_user.id,
                    message_id=mid,
                    is_read=True,
                    read_at=now,
                )
                for mid in missing_ids
            ]
        )

    return Success(
        data=MarkAllReadOut(marked=int(updated) + len(missing_ids)).model_dump()
    )


@router.delete(
    "/{message_id}",
    summary="删除/隐藏消息",
    response_model=ResponseBase[None],
)
async def delete_message(message_id: int, current_user: User = DependAuth):
    msg = await Message.filter(id=message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="i18n:common.not_found")

    now = _now()
    state, _ = await MessageUserState.get_or_create(
        user_id=current_user.id, message_id=message_id
    )
    state.is_deleted = True
    state.deleted_at = now
    await state.save()

    return Success(data=None)


@router.post(
    "/create",
    summary="新增消息（后台）",
    dependencies=[DependPermisson],
)
async def create_message(body: MessageCreate):
    try:
        send_time = body.time or _now()
        await message_repository.create(
            {
                "title": body.title,
                "content": body.content,
                "type": body.type,
                "send_time": send_time,
            }       
        )
        return Success(msg="Created Successfully")
    
    except Exception as exc:  # pragma: no cover - defensive guard
        return Fail(msg=str(exc))
