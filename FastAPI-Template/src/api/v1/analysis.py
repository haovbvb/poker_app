from fastapi import APIRouter, Depends
from core.dependency import DependAuth
from models.admin import User
from schemas.response import ResponseBase, PageResponse
from schemas.analysis import HandUploadIn, HandHistoryOut
from schemas.growth import GrowthStatsOut
from services import analysis_service
from models.analysis import HandHistory

router = APIRouter()


@router.post(
    "/hands/upload", response_model=ResponseBase[HandHistoryOut], summary="上传牌谱"
)
async def upload_hand(data: HandUploadIn, current_user: User = DependAuth):
    hand = await analysis_service.upload_hand_history(current_user.id, data)
    return ResponseBase(data=hand)


@router.get(
    "/hands",
    response_model=PageResponse[list[HandHistoryOut]],
    summary="获取我的牌谱列表",
)
async def list_hands(
    page: int = 1, page_size: int = 20, current_user: User = DependAuth
):
    offset = (page - 1) * page_size
    hands = await analysis_service.get_user_hands(
        current_user.id, limit=page_size, offset=offset
    )

    total = await HandHistory.filter(user_id=current_user.id).count()

    return PageResponse(data=hands, total=total, page=page, page_size=page_size)


@router.get(
    "/growth/stats",
    response_model=ResponseBase[GrowthStatsOut],
    summary="成长数据统计（全量 + 近30日）",
)
async def growth_stats(current_user: User = DependAuth):
    stats = await analysis_service.get_growth_stats(user_id=current_user.id)
    return ResponseBase(data=stats)
