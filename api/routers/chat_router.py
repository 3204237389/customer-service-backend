import uuid



from fastapi import Depends

from fastapi.routing import APIRouter



from api.dependencies import get_dialogue_service

from api.schemas import ChatRequest, ChatResponse, ChatBotMessage, ChatObject, HistoryResponse, HistoryMessage

from domain.messages import UserMessage, MessageType, FocusedObject, ProcessResult

from service.dialogue_service import DialogueService



router = APIRouter()





@router.post("/api/chat")

async def chat_endpoint(chat_request: ChatRequest,



                        dialogue_service: DialogueService = Depends(get_dialogue_service)

                        ) -> ChatResponse:



    user_message = _build_user_message(chat_request)





    process_result: ProcessResult = await dialogue_service.process_message(user_message)





    return _build_chat_response(process_result)





def _build_user_message(chat_request: ChatRequest) -> UserMessage:

    return UserMessage(

        sender_id=chat_request.sender_id,

        message_id=chat_request.message_id if chat_request.message_id else str(uuid.uuid4()),

        type=MessageType.TEXT if chat_request.text else MessageType.OBJECT,

        text=chat_request.text,

        object=FocusedObject(

            id=chat_request.object.id,

            type=chat_request.object.type,

            title=chat_request.object.title,

            attributes=chat_request.object.attributes,

        ) if chat_request.object else None

    )





def _build_chat_response(process_result: ProcessResult) -> ChatResponse:

    return ChatResponse(

        sender_id=process_result.sender_id,

        message_id=process_result.message_id,

        messages=[

            ChatBotMessage(

                text=bot_msg.text,

                object=ChatObject(

                    type=bot_msg.object.type,

                    id=bot_msg.object.id,

                    title=bot_msg.object.title,

                    attributes=bot_msg.object.attributes

                ) if bot_msg.object else None

            )

            for bot_msg in process_result.messages

        ]

    )





@router.get("/api/chat/history")

async def history(

        sender_id: str,

        service: DialogueService = Depends(get_dialogue_service)

) -> HistoryResponse:

    chat_message_response: list[HistoryMessage] = await service.load_chat_history(sender_id)

    return HistoryResponse(sender_id=sender_id, messages=chat_message_response)
