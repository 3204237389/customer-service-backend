from typing import Any

from jinja2 import Template
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from domain.messages import BotMessage
from domain.state import DialogueState
from infrastructure.llm import llm
from prompts.history_builder import HistoryBuilder
from task.action.base import Action, ActionResult


class ActionResponse(Action):
    """
    给用户返回一句话：搜集槽位信息，例如：请告诉我你的订单号
    """
    name = "action_response"

    async def run(self,state:DialogueState,action_kwargs:dict[str,Any]) -> ActionResult:
        mode = action_kwargs.get("mode","static")
        if mode == "static":
            text = action_kwargs["text"]
            rendered_text = self._render_text(text,state)
            return ActionResult(message=[BotMessage(text=rendered_text)])

        elif mode == "rephrase":
            text = action_kwargs["text"]
            rendered_text = self._render_text(text,state)
            prompt_text = action_kwargs["prompt_text"]
            llm_text = await self._call_llm(prompt_text,state,rendered_text)
            return ActionResult(message=[BotMessage(text=llm_text)])
        else:
            prompt_text = action_kwargs["prompt_text"]
            llm_text = await self._call_llm(prompt_text,state)
            return ActionResult(message=[BotMessage(text=llm_text)])

    @staticmethod
    def _render_text(text:str, state:DialogueState):
        """
        将模板中占位符替换成真实的值
        :param text:
        :param state:
        :return:
        """
        template = Template(text)
        result = template.render(
            slots = state.active_task.slots if state.active_task else {},
            context = state.active_system_task or state.active_task
        )
        return result

    @staticmethod
    async def _call_llm(prompt_text: str, state: DialogueState, rendered_text: str = "") -> str:
        prompt = PromptTemplate.from_template(prompt_text)
        chain = prompt | llm | StrOutputParser()

        bot_message = await chain.ainvoke({
            "history": HistoryBuilder.build(state.current_session().turns),
            "user_message": HistoryBuilder.render_user_message(state.pending_turn.user_message),
            "current_response": rendered_text
        })
        return bot_message  
