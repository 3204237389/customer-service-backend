from typing import List, Dict
from pydantic import BaseModel
from task.flow.steps import FlowStep, StartFlowStep

class FlowSlot(BaseModel):
    """
    槽位
    """
    name: str
    type: str = "any"
    label: str = ""
    description: str = ""


class Flow(BaseModel):
    """
    流程
    """
    id: str
    description: str = ""
    steps: List[FlowStep] = []
    slots: List[FlowSlot] = []
    name: str | None = None

    def start_step(self) -> StartFlowStep | None:
        """
        返回流程的开始步骤
        :return:
        """
        for step in self.steps:
            if isinstance(step, StartFlowStep):
                return step
        return None

    def get_step_by_id(self, step_id: str) -> FlowStep | None:
        """
        根据步骤ID获取步骤
        :param step_id:
        :return:
        """
        for step in self.steps:
            if step.id == step_id:
                return step
        return None


class FlowsList(BaseModel):
    """
    流程列表
    """
    flows: List[Flow] = []
    slots: Dict[str, FlowSlot] = {}

    def get_flow_by_id(self, flow_id: str) -> Flow | None:
        """
        根据流程ID获取流程
        :param flow_id:
        :return:
        """
        for flow in self.flows:
            if flow.id == flow_id:
                return flow
        return None
