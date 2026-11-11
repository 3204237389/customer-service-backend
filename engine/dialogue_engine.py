import time
from typing import List

from chitchat.handler import ChitChatHandler
from clarify.ClarifyResponder import ClarifyResponder
from domain.messages import UserMessage, ProcessResult, BotMessage, MessageType
from domain.state import DialogueState
from knowledge.handler import KnowledgeHandler
from plan.models import ClarifyReason
from plan.turn_planner import TurnPlanner
from plan.turn_validator import TurnPlanValidator
from task.command.models import Command, SetSlotsCommand
from task.flow.flows import FlowsList
from task.flow.steps import CollectFlowStep
from task.hander import TaskHandler



class DialogueEngine:

    def __init__(
            self,
            turn_planner: TurnPlanner,
            task_handler: TaskHandler,
            knowledge_handler: KnowledgeHandler,
            chitchat_handler: ChitChatHandler,
            clarify_responder: ClarifyResponder,
            turn_plan_validator: TurnPlanValidator
    ) -> None:
        self.turn_planner = turn_planner
        self.task_handler = task_handler
        self.knowledge_handler = knowledge_handler
        self.chitchat_handler = chitchat_handler
        self.clarify_responder = clarify_responder
        self.turn_plan_validator = turn_plan_validator
    async def process_message(self, dialogue_state: DialogueState,
                            user_message: UserMessage) -> ProcessResult:

        self._prepare_session(dialogue_state)

        self._begin_turn(dialogue_state, user_message)

        if user_message.type is MessageType.TEXT:
            messages = await self._handle_text_message(dialogue_state)
        else:
            dialogue_state.set_focused_object(user_message.object)
            messages = await self._handle_object_message(user_message, dialogue_state)

        dialogue_state.pending_turn.bot_messages.extend(messages)
        dialogue_state.commit_turn()


        return ProcessResult(
            sender_id=user_message.sender_id,
            message_id=user_message.message_id,
            messages=messages
        )

    @staticmethod
    def _prepare_session(dialogue_state:DialogueState):
        session = dialogue_state.current_session()

        if session is None:
            dialogue_state.start_session()
            return

        now = time.time()
        if now - session.last_activity_at > 60 * 60:
            dialogue_state.close_current_session()
            dialogue_state.reset_runtime_state_for_new_session()
            dialogue_state.start_session()
        else:
            session.last_activity_at = now

    def _begin_turn(self, dialogue_state:DialogueState, user_message:UserMessage):
        dialogue_state.begin_turn(user_message)

    async def _handle_text_message(self, dialogue_state:DialogueState)-> list[BotMessage] | None:
        turn_plan = await self.turn_planner.predict(dialogue_state, self.task_handler.flows,self.knowledge_handler.knowledge_intents)

        validated = self.turn_plan_validator.validate(dialogue_state, turn_plan, self.task_handler.flows,self.knowledge_handler.knowledge_intents)

        if not validated.valid:
            return await self.clarify_responder.respond(dialogue_state, validated.reason)

        if turn_plan.task is not None:
            return await self.task_handler.handle(commands=turn_plan.task.commands, state=dialogue_state)
        elif turn_plan.knowledge is not None:
            return await self.knowledge_handler.handle(intents=turn_plan.knowledge.intents,state=dialogue_state)
        elif turn_plan.chitchat is not None:
            return await self.chitchat_handler.handle(state = dialogue_state)


    async def _handle_object_message(
            self,
            message: UserMessage,
            state: DialogueState,
    ) -> list[BotMessage]:
        """
        处理对象消息
        :param message:
        :param state:
        :return:
        """

        commands = self._resolve_object_commands(
            message=message,
            state=state,
            flows=self.task_handler.flows,
        )

        if commands:
            return await self.task_handler.handle(commands=commands, state=state)

        if state.active_task is not None:
            return await self.task_handler.handle(commands=[], state=state)

        return await self.clarify_responder.respond(
            state=state,
            reason=ClarifyReason.OBJECT_REQUIRES_INTENT,
        )

    def _resolve_object_commands(
            self,
            message: UserMessage,
            state: DialogueState,
            flows: FlowsList
    ) -> list[Command]:
        """
        将对象消息转换成command
        :param message:
        :param state:
        :param flows:
        :return:
        """

        focused_object = message.object

        if focused_object is None:
            return []

        object_type = focused_object.type


        if object_type == "order":
            if self._flow_has_unfilled_collect_slot(state, flows, "order_number"):
                return [SetSlotsCommand(command="set_slots", slots={"order_number": focused_object.id})]
            return []

        if object_type == "product":
            if self._flow_has_unfilled_collect_slot(state, flows, "product_id"):
                return [
                    SetSlotsCommand(command="set_slots", slots={"product_id": focused_object.id})
                ]
            return []


        return []

    def _flow_has_unfilled_collect_slot(self, state: DialogueState, flows: FlowsList, slot_name: str):
        """
        当前流程是不是定义了某个槽位，并且这个槽位还没有被填充内容
        :param state:
        :param flows:
        :param slot_name:
        :return: 如果没有填充内容则返回 Ture
        """
        active_task = state.active_task

        if active_task is None:
            return False

        flow_id = active_task.flow_id
        flow = flows.get_flow_by_id(flow_id)
        if flow is None:
            return False

        if active_task.slots.get(slot_name):
            return False

        for step in flow.steps:
            if isinstance(step, CollectFlowStep) and step.slot_name == slot_name:
                return True

        return False