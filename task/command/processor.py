import dataclasses
from typing import List

from domain.contexts import StartedSystemContext, InterruptedSystemContext, ResumedSystemContext, CanceledSystemContext, \
    TaskContext
from domain.state import DialogueState
from task.command.models import Command, StartFlowCommand, SetSlotsCommand, CancelFlowCommand, ResumeFlowCommand
from task.flow.flows import FlowsList
from task.flow.steps import StartFlowStep


class CommandProcessor:
    """
    命令处理器
    """

    def run(self, commands: List[Command], state: DialogueState, flows: FlowsList):
        """
        处理命令列表
        :param commands:
        :param state:
        :param flows:
        :return:
        """
        for command in commands:
            self._apply(command, state, flows)

    def _apply(self, command, state, flows):
        """
        处理一个命令
        :param command:
        :param state:
        :param flows:
        :return:
        """
        if isinstance(command, StartFlowCommand):
            self._handle_start_flow(command, state, flows)
        elif isinstance(command, SetSlotsCommand):
            self._handle_set_slots(command, state)
        elif isinstance(command, CancelFlowCommand):
            self._handle_cancel_flow(state, flows)
        elif isinstance(command, ResumeFlowCommand):
            self._handle_resume_flow(command, state, flows)

    def _handle_start_flow(self, command: StartFlowCommand, state: DialogueState, flows: FlowsList):
        """
        开启一个业务
        :param command:
        :param state:
        :param flows:
        :return:
        """
        state.end_active_system_task()

        if command.flow.startswith("system_"):
            raise ValueError(f"不能直接启动系统流程：'{command.flow}'")

        target_flow = flows.get_flow_by_id(command.flow)
        if target_flow is None:
            raise ValueError(f"未知流程：'{command.flow}'.")

        start_step = target_flow.start_step()
        if start_step is None:
            raise ValueError(f"流程 '{command.flow}' 没有开始步骤")

        active_task = state.active_task

        if active_task is not None:

            if active_task.flow_id == command.flow:
                return

            state.interrupted_active_task()

            resumed = state.resumed_active_task(command.flow)
            if not resumed:
                state.start_active_task(TaskContext(flow_id=command.flow, step_id=start_step.id))

            interrupted_flow_id = active_task.flow_id
            interrupted_flow_name = self._readable_flow_name(active_task.flow_id, flows)
            started_flow_id = command.flow
            started_flow_name = self._readable_flow_name(command.flow, flows)
            self._activate_interrupted_system_flow(
                state, flows, interrupted_flow_id, interrupted_flow_name,
                started_flow_id, started_flow_name)

            return

        resumed = state.resumed_active_task(command.flow)
        if resumed:
            self._activate_resumed_system_flow(
                state, flows, command.flow, self._readable_flow_name(command.flow, flows)
            )
            return

        state.start_active_task(TaskContext(flow_id=command.flow, step_id=start_step.id))
        self._activate_started_system_flow(
            state, flows, command.flow, self._readable_flow_name(command.flow, flows)
        )

    def _handle_set_slots(self, command: SetSlotsCommand, state: DialogueState):
        """
        设置槽值
        :param command:
        :param state:
        :return:
        """
        if state.active_task:
            state.set_slots(command.slots)

    def _handle_cancel_flow(self, state: DialogueState, flows: FlowsList):
        """
        取消一个业务
        :param state:
        :param flows:
        :return:
        """
        active_task = state.active_task

        state.cancel_active_task()

        canceled_flow_id = active_task.flow_id
        canceled_flow_name = self._readable_flow_name(canceled_flow_id, flows)
        self._activate_canceled_system_flow(
            state, flows, canceled_flow_id, canceled_flow_name
        )

    def _handle_resume_flow(self, command: ResumeFlowCommand, state: DialogueState, flows: FlowsList):
        """
        恢复一个业务
        :param command:
        :param state:
        :param flows:
        :return:
        """
        if command.flow is not None:
            target_flow = flows.get_flow_by_id(command.flow)
            if target_flow is None:
                raise ValueError(f"未知流程 '{command.flow}'.")
            target_flow_id = target_flow.id
            target_flow_name = target_flow.name
        else:
            if not state.paused_tasks:
                return
            top_paused = state.paused_tasks[-1]
            target_flow_id = top_paused.flow_id
            target_flow_name = self._readable_flow_name(target_flow_id, flows)

        active_task = state.active_task
        if active_task is not None:
            if active_task.flow_id == target_flow_id:
                return
            interrupted_flow_id = active_task.flow_id
            interrupted_flow_name = self._readable_flow_name(active_task.flow_id, flows)
            state.interrupted_active_task()
            if not state.resumed_active_task(target_flow_id):
                state.resumed_active_task()
                return
            self._activate_interrupted_system_flow(
                state, flows, interrupted_flow_id, interrupted_flow_name,
                target_flow_id, target_flow_name)
        else:
            if not state.resumed_active_task(command.flow):
                return

            resumed = state.active_task
            self._activate_resumed_system_flow(
                state, flows, resumed.flow_id, self._readable_flow_name(resumed.flow_id, flows))

    @staticmethod
    def _readable_flow_name(flow_id: str, flows: FlowsList) -> str:
        """
        根据流程id获取流程名称
        :param flow_id:
        :param flows:
        :return:
        """
        flow = flows.get_flow_by_id(flow_id)
        return flow.name if flow else flow_id


    @staticmethod
    def _activate_started_system_flow(
            state: DialogueState,
            flows: FlowsList,
            started_flow_id: str,
            started_flow_name: str
    ):
        """
        激活开始流程的过场白
        """
        flow = flows.get_flow_by_id("system_task_started")
        state.start_active_system_task(StartedSystemContext(
            step_id=flow.start_step().id,
            started_flow_id=started_flow_id,
            started_flow_name=started_flow_name,
        ))


    @staticmethod
    def _activate_interrupted_system_flow(
            state: DialogueState,
            flows: FlowsList,
            interrupted_flow_id: str,
            interrupted_flow_name: str,
            started_flow_id: str,
            started_flow_name: str
    ):
        """
        激活中断流程的过场白
        """
        flow = flows.get_flow_by_id("system_task_interrupted")
        state.start_active_system_task(InterruptedSystemContext(
            step_id=flow.start_step().id,
            interrupted_flow_id=interrupted_flow_id,
            interrupted_flow_name=interrupted_flow_name,
            started_flow_id=started_flow_id,
            started_flow_name=started_flow_name
        ))


    @staticmethod
    def _activate_resumed_system_flow(
            state: DialogueState, flows: FlowsList,
            resumed_flow_id: str, resumed_flow_name: str):
        """
        激活恢复流程的过场白
        """
        flow = flows.get_flow_by_id("system_task_resumed")
        state.start_active_system_task(ResumedSystemContext(
            step_id=flow.start_step().id,
            resumed_flow_id=resumed_flow_id,
            resumed_flow_name=resumed_flow_name
        ))

    @staticmethod
    def _activate_canceled_system_flow(
            state: DialogueState,
            flows: FlowsList,
            canceled_flow_id: str,
            canceled_flow_name: str
    ):
        """"
        激活取消流程的过场白
        """
        flow = flows.get_flow_by_id("system_task_canceled")
        state.start_active_system_task(CanceledSystemContext(
            step_id=flow.start_step().id,
            canceled_flow_id=canceled_flow_id,
            canceled_flow_name=canceled_flow_name
        ))
