from abc import abstractmethod, ABC
from typing import Any

from openai import BaseModel

from domain.messages import BotMessage
from domain.state import DialogueState


class ActionResult(BaseModel):
    message:list[BotMessage] = []
    slot_updates: dict[str,Any] = {}

@abstractmethod
class Action(ABC):
    name: str = ""

    async def run(self,state:DialogueState,action_kwargs:dict[str,Any])-> ActionResult:
        """
        执行action
        :param state:
        :param action_kwargs: action的args参数
        :return:
        """
        pass

