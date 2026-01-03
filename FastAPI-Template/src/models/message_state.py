from tortoise import fields

from .base import BaseModel, TimestampMixin


class MessageUserState(BaseModel, TimestampMixin):
    """用户消息状态（已读/删除）

    用于在不为每条广播消息预生成记录的情况下，仍支持：未读数、已读时间、用户删除隐藏等能力。
    """

    user_id = fields.IntField(index=True, description="用户ID")
    message = fields.ForeignKeyField(
        "models.Message",
        related_name="user_states",
        on_delete=fields.CASCADE,
        description="消息",
    )

    is_read = fields.BooleanField(default=False, description="是否已读", index=True)
    read_at = fields.DatetimeField(null=True, description="已读时间")

    is_deleted = fields.BooleanField(default=False, description="是否删除/隐藏", index=True)
    deleted_at = fields.DatetimeField(null=True, description="删除/隐藏时间")

    class Meta:
        table = "message_user_state"
        unique_together = ("user_id", "message_id")
