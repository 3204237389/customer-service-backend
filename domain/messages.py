from enum import Enum

from pydantic import BaseModel


class FocusedObject(BaseModel):
    id: str
    type: str
    title: str | None = None
    attributes: dict = {}

class MessageType(Enum):
    TEXT = "text"
    OBJECT = "object"

class UserMessage(BaseModel):
    sender_id: str
    message_id: str
    type: MessageType
    text: str | None = None
    object: FocusedObject | None = None

class BotMessage(BaseModel):
    text: str | None = None
    object: FocusedObject | None = None

class ProcessResult(BaseModel):
    sender_id: str
    message_id: str
    messages: list[BotMessage]

if __name__ == "__main__":
    attributes = {"price":"200"}
    fo = FocusedObject(id="1", type="order",title="订单1",attributes=attributes)
    data = fo.model_dump(mode="json")
    print(fo)
    print(type(fo))
    print(data)
    print(type(data))

    fo_obj = FocusedObject.model_validate(data)
    print(fo_obj)
    print(type(fo_obj))