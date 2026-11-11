from typing import Dict

from domain.state import DialogueState
from knowledge.intents import KnowledgeIntent
from plan.models import TurnPlan, TurnPlanValidationResult, ClarifyReason
from task.command.models import StartFlowCommand, ResumeFlowCommand, CancelFlowCommand, SetSlotsCommand
from task.flow.flows import FlowsList


class TurnPlanValidator:

    def validate(
            self,
            state: DialogueState,
            turn_plan: TurnPlan,
            flow_list: FlowsList,
            intents: Dict[str, KnowledgeIntent]
    ) -> TurnPlanValidationResult:
        """
        校验 turn_plan
        :param turn_plan:
        :return:
        """

        active_tracks = self._active_tracks(turn_plan)

        if not active_tracks:
            return self._reject(ClarifyReason.MISSING_TRACK)

        if len(active_tracks) > 1:
            return self._reject(ClarifyReason.MULTIPLE_TRACKS)

        active_track = active_tracks[0]

        if active_track == "task":
            return self._validate_task(turn_plan, flow_list)

        if active_track == "knowledge":
            return self._validate_knowledge(state, turn_plan, intents)

        return TurnPlanValidationResult(valid=True)

    def _active_tracks(self, turn_plan:TurnPlan)->list[str]:
        active_tracks: list[str] = []
        if turn_plan.task is not None:
            active_tracks.append("task")

        if turn_plan.knowledge is not None:
            active_tracks.append("knowledge")

        if turn_plan.chitchat is not None:
            active_tracks.append("chitchat")

        return active_tracks

    def _reject(self, reason: ClarifyReason)->TurnPlanValidationResult:
        return TurnPlanValidationResult(valid=False, reason=reason)

    def _validate_task(self, turn_plan:TurnPlan, flow_list:FlowsList):
        task_plan = turn_plan.task

        if task_plan is None or not task_plan.commands:
            return self._reject(ClarifyReason.MISSING_TASK_COMMANDS)

        allowed = (StartFlowCommand, ResumeFlowCommand, CancelFlowCommand, SetSlotsCommand)
        if not all(isinstance(cmd, allowed) for cmd in task_plan.commands):
            return self._reject(ClarifyReason.INVALID_TASK_COMMANDS)

        start_commands = [cmd for cmd in task_plan.commands if isinstance(cmd, StartFlowCommand)]
        if len(start_commands) > 1:
            return self._reject(ClarifyReason.MULTIPLE_TASK_FLOWS)

        if start_commands:
            flow = flow_list.get_flow_by_id(start_commands[0].flow)
            if flow is None:
                return self._reject(ClarifyReason.UNKNOWN_TASK_FLOW)

        return TurnPlanValidationResult(valid=True)

    def _validate_knowledge(
            self,
            state: DialogueState,
            turn_plan: TurnPlan,
            intents: Dict[str, KnowledgeIntent]
    ) -> TurnPlanValidationResult:

        knowledge_plan = turn_plan.knowledge
        if knowledge_plan is None or not knowledge_plan.intents:
            return self._reject(ClarifyReason.MISSING_KNOWLEDGE_INTENT)

        focused_object = state.focused_object
        for intent in knowledge_plan.intents:
            intent_meta = intents[intent]
            required_object = intent_meta.requires_object
            if required_object is not None:
                if focused_object is None or focused_object.type != required_object:
                    return self._reject(ClarifyReason.MISSING_FOCUSED_OBJECT)

        return TurnPlanValidationResult(valid=True)


