from pydantic import BaseModel


class ChatObject(BaseModel):
    """
    聚焦对象：
    对应前端点击订单/商品卡片时带的数据
    """
    type: str
    id: str
    title: str | None = None
    attributes: dict = {}


class ChatRequest(BaseModel):
    """
    请求对象（用户问题）
    `POST /api/chat` 的请求体
    注意：
    text 和 object 都是可选的，但实际使用中至少要传一个
    文本消息传 text，对象消息传 object
    """
    sender_id: str
    message_id: str | None = None
    text: str | None = None
    object: ChatObject | None = None


class ChatBotMessage(BaseModel):
    """
    机器人消息
    """
    text: str | None = None
    object: ChatObject | None = None


class ChatResponse(BaseModel):
    """
    响应对象（机器人回复）
    """
    sender_id: str
    message_id: str
    messages: list[ChatBotMessage]


class HistoryMessage(BaseModel):
    """
    历史消息
    """
    role: str
    text: str | None = None
    object: ChatObject | None = None

class HistoryResponse(BaseModel):
    """
    历史消息列表
    `GET /api/chat/history` 的返回体。
    """
    sender_id: str
    messages: list[HistoryMessage]