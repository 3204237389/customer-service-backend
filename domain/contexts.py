from typing import Literal, Annotated

from pydantic import BaseModel, Field, TypeAdapter


class TaskContext(BaseModel):
    """
    业务任务上下文
    """
    flow_id: str
    step_id: str | None = None
    slots: dict = {}


class SystemContext(BaseModel):
    """
    系统流程上下文
    定义具体流程的通用属性
    """
    flow_id: str
    step_id: str | None = None

class StartedSystemContext(SystemContext):
    """
    流程开始
    """
    started_flow_id: str = ""
    started_flow_name: str = ""

    flow_id: Literal["system_task_started"] = "system_task_started"

class InterruptedSystemContext(SystemContext):
    """
    流程中断
    """
    interrupted_flow_id: str = ""
    interrupted_flow_name: str = ""
    started_flow_id: str = ""
    started_flow_name: str = ""
    flow_id: Literal["system_task_interrupted"] = "system_task_interrupted"

class CanceledSystemContext(SystemContext):
    """
    流程取消
    """
    canceled_flow_id: str = ""
    canceled_flow_name: str = ""
    flow_id: Literal["system_task_canceled"] = "system_task_canceled"

class ResumedSystemContext(SystemContext):
    """
    流程恢复
    """
    resumed_flow_id: str = ""
    resumed_flow_name: str = ""
    flow_id: Literal["system_task_resumed"] = "system_task_resumed"

class CollectedSystemContext(SystemContext):
    """
    系统流程收集槽位信息
    """
    slot_name: str = ""
    response: dict = {}
    flow_id: Literal["system_collect_information"] = "system_collect_information"

SystemContextUnion = Annotated[
    StartedSystemContext |
    InterruptedSystemContext |
    CanceledSystemContext |
    ResumedSystemContext |
    CollectedSystemContext,
    Field(discriminator="flow_id")
]
system_context_adapter = TypeAdapter(SystemContextUnion)

if __name__ == '__main__':

    data = {
        "flow_id": "system_task_started",
        "step_id": "start",
        "started_flow_id": "order_status_query",
        "started_flow_name": "订单状态查询"
    }

    obj1 = SystemContext.model_validate(data)
    print(type(obj1))
    print(obj1)

    obj2 = StartedSystemContext.model_validate(data)
    print(type(obj2))
    print(obj2)

    obj = system_context_adapter.validate_python(data)

    print(type(obj))
    print(obj)