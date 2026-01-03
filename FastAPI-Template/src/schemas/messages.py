from datetime import datetime

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    """创建消息入参"""

    title: str = Field(description="消息标题", max_length=200)
    content: str = Field(description="消息内容")
    type: str = Field(default="info", description="消息类型", max_length=20)
    time: datetime | None = Field(
        default=None, description="消息时间，不传则为当前时间"
    )


class MessageFeedItem(BaseModel):
    """面向App用户的消息项（带已读状态）"""

    id: int = Field(description="消息ID")
    title: str = Field(description="消息标题")
    content: str = Field(description="消息内容")
    time: datetime = Field(description="消息时间")
    type: str = Field(description="消息类型")
    is_read: bool = Field(default=False, description="是否已读")


class UnreadCountOut(BaseModel):
    unread_count: int = Field(description="未读数量")


class MarkReadOut(BaseModel):
    message_id: int = Field(description="消息ID")
    is_read: bool = Field(default=True, description="是否已读")


class MarkAllReadOut(BaseModel):
    marked: int = Field(description="本次标记已读的条数")
