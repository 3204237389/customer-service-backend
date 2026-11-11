from typing import Any

from domain.state import DialogueState
from task.action.base import ActionResult


class ActionListen:
    """
    等待用户输入槽位信息：什么都不做
    """

    name = "action_listen"

    async def run(self,state:DialogueState,action_kwargs:dict[str,Any])->ActionResult:
        return ActionResult()