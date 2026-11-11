from typing import Any

from pydantic import BaseModel

from domain.state import DialogueState
from task.action.base import ActionResult
from task.action.registry import ActionRegistry


class ActionCall(BaseModel):
    action_name: str
    action_kwargs: dict[str, Any] = {}

class ActionRunner:

    def __init__(self,registry:ActionRegistry) -> None:
        self.registry = registry

    async def run(self,action_call:ActionCall,state:DialogueState) -> ActionResult:
        action_name = action_call.action_name

        action = self.registry.get(action_name)

        return await action.run(state,action_call.action_kwargs)
