from domain.contexts import CollectedSystemContext
from domain.messages import BotMessage
from domain.state import DialogueState
from task.action.base import ActionResult
from task.action.runner import ActionRunner, ActionCall
from task.flow.flows import FlowsList
from task.flow.links import StaticLink, ConditionalLink, FallbackLink
from task.flow.steps import FlowStep, StartFlowStep, EndFlowStep, CollectFlowStep, ActionFlowStep


class FlowExecutor:
    """
    推进yml文件中定义的业务流程以及系统流程
    内层循环：负责流程的不断推进
    外层循环：负责执行action，如果action的返回结果是action_listen，则退出外层循环 等待用户输入
    """

    async def run_task(self, state: DialogueState, flows: FlowsList, action_runner: ActionRunner) -> list[BotMessage]:

        messages: list[BotMessage] = []
        while True:
            action_call: ActionCall = self.advance_until_action(state, flows)

            if action_call.action_name == "action_listen":
                break

            else:
                action_result: ActionResult = await action_runner.run(action_call, state)
                state.set_slots(action_result.slot_updates)
                messages.extend(action_result.message)

        return messages

    def advance_until_action(self, state: DialogueState, flows: FlowsList) -> ActionCall:
        while True:
            current_active_task = state.current_active_task()

            if current_active_task is None:
                return ActionCall(action_name="action_listen")

            flow = flows.get_flow_by_id(current_active_task.flow_id)

            step = flow.get_step_by_id(current_active_task.step_id)

            action_call:ActionCall = self._run_step(state, step, flows)

            if action_call is not None:
                return action_call

    def _run_step(self, state: DialogueState, step: FlowStep, flows: FlowsList) -> ActionCall|None:
        if isinstance(step, StartFlowStep):
            return self._run_start_step(step, state)
        if isinstance(step, EndFlowStep):
            return self._run_end_step(state)
        if isinstance(step, CollectFlowStep):
            return self._run_collect_step(step, state, flows)
        if isinstance(step, ActionFlowStep):
            return self._run_action_step(step, state)

    def _run_start_step(self, step: StartFlowStep, state: DialogueState) -> None:
        self._advance_next_step(state, step)
        return None

    def _advance_next_step(self, state: DialogueState, step: FlowStep):
        next_step_id = self._select_next_step(step, state)
        state.current_active_task().step_id = next_step_id

    def _select_next_step(self, step: FlowStep, state: DialogueState) -> str:

        for link in step.next:
            if isinstance(link, StaticLink):
                return link.target
            if isinstance(link, ConditionalLink):
                if self._eval_condition(state, link.condition):
                    return link.target
            if isinstance(link, FallbackLink):
                return link.target
        return "没有下一步"

    @staticmethod
    def _eval_condition(state: DialogueState, condition: str) -> bool:
        data = {
            "slots": state.active_task.slots,
            "context": state.current_active_task().model_dump(mode="json")
        }
        return bool(eval(condition, {'__builtins__': None}, data))

    @staticmethod
    def _run_end_step(state: DialogueState) -> None:
        if state.active_system_task:
            state.end_active_system_task()
        else:
            state.end_active_task()
        return None

    def _run_action_step(self, step: ActionFlowStep, state: DialogueState) -> ActionCall:
        self._advance_next_step(state, step)
        action_call = self._build_action_call(state, step)
        return action_call

    @staticmethod
    def _build_action_call(state: DialogueState, step: ActionFlowStep) -> ActionCall:
        action_name = step.action
        action_kwargs = step.args
        if isinstance(action_kwargs, str):
            action_kwargs = state.active_system_task.model_dump(mode="json")[action_kwargs.split(".")[1]]
        return ActionCall(action_name=action_name, action_kwargs=action_kwargs)

    def _run_collect_step(self, step: CollectFlowStep, state: DialogueState, flows: FlowsList):

        self._try_to_fill_collect_slot_focused_object(state, step)

        if state.active_task.slots.get(step.slot_name):

            self._advance_next_step(state, step)
            return None
        else:
            state.start_active_system_task(CollectedSystemContext(
                step_id=flows.get_flow_by_id('system_collect_information').start_step().id,
                slot_name=step.slot_name,
                response=step.response.model_dump(mode="json")
            ))
            return None

    @staticmethod
    def _try_to_fill_collect_slot_focused_object(state: DialogueState, step: CollectFlowStep):

        if state.focused_object is None:
            return None

        if step.slot_name == 'order_number' and state.focused_object.type == "order":
            state.set_slots({step.slot_name: state.focused_object.id})

        if step.slot_name == "product_id" and state.focused_object.type == "product":
            state.set_slots({step.slot_name: state.focused_object.id})
        return None
