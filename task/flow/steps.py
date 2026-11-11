"""
步骤（节点）设计 —— 定义流程中的 4 种步骤类型。

每个步骤（Step）是流程图中的一个节点，通过 Link（边）相互连接。
步骤类型由 yml 中的 type 字段决定：

    yml 中 type 的值    →  对应的 Python 类       →  用途
    ─────────────────────────────────────────────────────────
    start               →  StartFlowStep          →  流程入口，标记流程开始
    end                 →  EndFlowStep            →  流程出口，标记流程结束
    action              →  ActionFlowStep         →  执行动作（回复用户/等待输入/调接口等）
    collect             →  CollectFlowStep        →  收集用户信息（槽位填充）

对应 yml 中的 step 定义，例如：
    - id: ask_order_number          ← 步骤唯一标识
      type: collect                 ← 步骤类型 → 决定实例化哪个类
      slot_name: order_number       ← CollectFlowStep 特有字段
      response:                     ← CollectFlowStep 特有字段
        text: "请告诉我你的订单号。"
      next: lookup_order_status     ← 下一步 → 解析为 FlowStepLink
"""
from enum import Enum
from typing import List, Dict, Any, Literal, Annotated
from pydantic import BaseModel, Field, TypeAdapter, field_validator
from task.flow.links import FlowStepLink, StaticLink, ConditionalLink, FallbackLink


class ResponseDefinition(BaseModel):
    """
    响应定义 —— 定义 action_response 动作如何向用户展示回复。

    对应 yml 中 action 步骤的 args 部分（当 action 为 action_response 时）：
        args:
          mode: static              ← model 字段（注意 yml 写 mode，代码字段名是 model）
          text: "订单状态是..."      ← text 字段：要展示的文本
          prompt: |                 ← prompt 字段（可选）：rephrase 模式下的 LLM 改写提示词

    两种响应模式：
    - static：原样输出 text，不经过 LLM 改写
    - rephrase：把 text 作为"建议回复"，连同 prompt 一起发给 LLM，让 LLM 改写出更自然的回复
    """
    model: str = "static"
    text: str
    prompt: str | None = None


class FlowStepType(Enum):
    """
    流程步骤类型枚举 —— 对应 yml 中 step 的 type 字段的 4 种取值。
    """
    START = "start"
    END = "end"
    ACTION = "action"
    COLLECT = "collect"


class FlowStep(BaseModel):
    """
    流程步骤（基类）—— 所有步骤类型的父类。

    对应 yml 中 steps 列表里的每一个 step 定义。
    这是一个基类，实际使用时会根据 type 实例化对应的子类：
    - StartFlowStep（type=start）
    - EndFlowStep（type=end）
    - ActionFlowStep（type=action）
    - CollectFlowStep（type=collect）
    """
    id: str
    type: FlowStepType
    next: List[FlowStepLink] = []
    description: str = ""

    @classmethod
    def from_dict(cls, step_data: dict[str, Any]) -> "FlowStep":
        """
        工厂方法 —— 根据 yml 中 step 的字典数据，自动创建对应类型的步骤实例。

        这是反序列化的入口：loader 读取 yml 得到 step_data 字典后，调用此方法。
        它根据 step_data['type'] 查 STEP_TYPE_TO_CLASS 映射表，找到对应的子类，
        再调用子类的 from_dict 完成具体实例化。

        例如：
            step_data = {"id": "ask_order_number", "type": "collect", ...}
            → 查到 CollectFlowStep
            → 调用 CollectFlowStep.from_dict(step_data)
            → 返回 CollectFlowStep 实例

        :param step_data: yml 中一个 step 解析后的字典
        :return: 对应类型的 FlowStep 子类实例
        """
        step_type = step_data['type']
        clz = STEP_TYPE_TO_CLASS[step_type]
        return clz.from_dict(step_data)

    @staticmethod
    def base_fields(base_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取所有步骤类型共有的基础字段。

        每个 step 不管是什么类型，都有 id、type、description、next 这 4 个基础字段。
        各子类的 from_dict 会先调用此方法获取基础字段，再补充自己的特有字段。

        :param base_data: yml 中一个 step 的字典数据
        :return: 包含 id、type、description、next 的字典，可直接传给子类构造函数
        """
        return {
            "id": base_data['id'],
            "type": FlowStepType(base_data['type']),
            "description": base_data.get('description', ''),
            "next": FlowStep.build_links(base_data['next'])
        }

    @staticmethod
    def build_links(link_data: str | list[Dict[str, Any]]) -> List[FlowStepLink]:
        """
        解析 yml 中的 next 字段，转换为 FlowStepLink 对象列表。

        yml 中 next 有两种写法，对应不同的 Link 类型：

        写法1：next 是字符串（静态跳转）
            next: respond
            → 解析为 [StaticLink(target="respond")]

        写法2：next 是列表（条件分支跳转）
            next:
              - if: "slots.get('product_id')"
                then: respond
              - else: ask_product_id
            → 解析为 [ConditionalLink(condition="slots.get('product_id')", target="respond"),
                       FallbackLink(target="ask_product_id")]

        :param link_data: yml 中 next 字段的值（字符串或字典列表）
        :return: FlowStepLink 子类对象列表
        """
        if isinstance(link_data, str):
            return [StaticLink(target=link_data)]

        else:
            links = []
            for link_dict in link_data:
                if "if" in link_dict:
                    links.append(ConditionalLink(condition=link_dict['if'], target=link_dict['then']))
                else:
                    links.append(FallbackLink(target=link_dict['else']))
            return links


class StartFlowStep(FlowStep):
    """
    流程开始步骤 —— 标记流程的入口。

    对应 yml 中：
        - id: start
          type: start
          next: respond        ← 跳到第一个业务步骤

    每个流程有且只有一个 start 步骤。
    没有额外字段，只需要基类的 id、type、next 即可。
    流程执行时，引擎通过 Flow.start_step() 找到这个步骤作为起点。
    """
    type: FlowStepType = FlowStepType.START

    @classmethod
    def from_dict(cls, step_data: dict[str, Any]) -> "StartFlowStep":
        """
        从字典创建 StartFlowStep。
        只需要基类的基础字段（id、type、next），没有额外字段。
        """
        return cls(**FlowStep.base_fields(step_data))


class EndFlowStep(FlowStep):
    """
    流程结束步骤 —— 标记流程的出口。

    对应 yml 中：
        - id: end
          type: end
          next: []             ← 结束步骤没有下一步，next 始终为空列表

    每个流程有且只有一个 end 步骤。
    流程执行到 end 步骤时，该流程就结束了。
    """
    type: FlowStepType = FlowStepType.END

    @classmethod
    def from_dict(cls, step_data: dict[str, Any]) -> "EndFlowStep":
        """
        从字典创建 EndFlowStep。
        只需要基类的基础字段（id、type、next），没有额外字段。
        """
        return cls(**FlowStep.base_fields(step_data))


class ActionFlowStep(FlowStep):
    """
    动作步骤 —— 执行某个具体动作。

    对应 yml 中：
        - id: respond
          type: action
          action: action_response       ← 要执行的动作名称
          args:                          ← 动作参数
            mode: static
            text: "订单状态是..."
          next: end

    常见的 action 值：
    - action_response：回复用户（向用户展示文本，可配合 LLM 改写）
    - action_listen：等待用户输入（哨兵模式，监听用户下一条消息）
    - action_lookup_order_status：查询订单状态（调用后端接口）
    - action_lookup_logistics：查询物流信息（调用后端接口）
    - action_recommend_similar_products：推荐相似商品（调用后端接口）

    动作的具体执行逻辑不在这里定义，由引擎中的 action handler 根据 action 名称分发执行。
    """
    type: FlowStepType = FlowStepType.ACTION

    action: str = ""
    args: dict | str = {}

    @classmethod
    def from_dict(cls, step_data: dict[str, Any]) -> "ActionFlowStep":
        """
        从字典创建 ActionFlowStep。
        基础字段 + 特有字段 action（动作名称）和 args（动作参数）。
        """
        return cls(**FlowStep.base_fields(step_data),
                   action=step_data['action'],
                   args=step_data.get('args', {}))


class CollectFlowStep(FlowStep):
    """
    收集步骤 —— 向用户收集某个槽位（信息字段）的值。

    对应 yml 中：
        - id: ask_order_number
          type: collect
          slot_name: order_number       ← 要收集的槽位名（对应 slots 中定义的 key）
          response:                      ← 向用户提问的话术定义
            text: "请告诉我你的订单号。"
          next: lookup_order_status

    执行流程：
    1. 引擎遇到 CollectFlowStep 时，会调用 system_collect_information 系统流程
    2. 系统流程用 response.text 向用户提问
    3. 等待用户回答（action_listen）
    4. 将用户回答填入 slot_name 指定的槽位

    loader 在加载时会扫描流程中所有 CollectFlowStep，收集其 slot_name 对应的 FlowSlot，
    去重后存入 Flow.slots 列表，供 LLM 了解该流程需要收集哪些信息。
    """
    type: FlowStepType = FlowStepType.COLLECT

    slot_name: str
    response: ResponseDefinition

    @classmethod
    def from_dict(cls, step_data: dict[str, Any]) -> "CollectFlowStep":
        """
        从字典创建 CollectFlowStep。
        基础字段 + 特有字段 slot_name（槽位名）和 response（响应定义）。
        """
        return cls(
            **FlowStep.base_fields(step_data),
            slot_name=step_data['slot_name'],
            response=ResponseDefinition(**step_data['response'])
        )


STEP_TYPE_TO_CLASS = {
    "start": StartFlowStep,
    "action": ActionFlowStep,
    "collect": CollectFlowStep,
    "end": EndFlowStep
}