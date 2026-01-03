from core.crud import CRUDBase
from models.admin import Message
from schemas.messages import MessageCreate


class MessageRepository(CRUDBase[Message, MessageCreate, MessageCreate]):
    def __init__(self):
        super().__init__(model=Message)


message_repository = MessageRepository()
