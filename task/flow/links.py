"""
模板边（Link）定义 —— 描述流程中步骤与步骤之间的跳转关系。

在流程图中，步骤（Step）是"节点"，而 Link 是连接节点之间的"边"。
每条边都有一个 target 字段，表示这条边指向的下一个步骤的 ID。

对应 yml 中 step 的 next 字段：
    next: step_id                          → StaticLink（静态边，无条件跳转）
    next: [{if: "条件", then: step_id}]    → ConditionalLink（条件边，满足条件才跳）
    next: [{else: step_id}]                → FallbackLink（兜底边，所有条件都不满足时走这里）
"""

from pydantic import BaseModel


class FlowStepLink(BaseModel):
    """
    模板边（基类）—— 所有边类型的父类。

    对应 yml 中 next 字段解析后的结果。
    无论哪种边，都必须有 target（目标步骤 ID）。

    例如 yml 中：
        next: lookup_order_status
    解析后生成：
        StaticLink(target="lookup_order_status")
    """
    target: str


class StaticLink(FlowStepLink):
    """
    静态边 —— 无条件跳转，直接指向下一个步骤。

    对应 yml 中 next 的值是字符串的情况：
        next: respond        ← 无条件跳到 id="respond" 的步骤

    这是最简单的边类型，没有额外字段，只需要继承自基类的 target 即可。
    例如：next: respond  →  StaticLink(target="respond")
    """
    pass


class ConditionalLink(FlowStepLink):
    """
    条件边 —— 只有满足条件时才跳转。

    对应 yml 中 next 是列表且包含 if/then 的情况：
        next:
          - if: "slots.get('product_id')"    ← condition 字段接收这个条件表达式字符串
            then: respond                     ← target 字段接收这个目标步骤 ID

    例如：
        - if: "context.get('reason') == 'not_supported'"
          then: not_supported
    解析后生成：
        ConditionalLink(condition="context.get('reason') == 'not_supported'", target="not_supported")

    运行时引擎会 eval(condition) 判断是否满足条件，满足则跳到 target。
    """
    condition: str


class FallbackLink(FlowStepLink):
    """
    兜底边 —— 当所有条件边都不满足时，走这条边（相当于 if/else 中的 else）。

    对应 yml 中 next 是列表且包含 else 的情况：
        next:
          - if: "条件1"
            then: step_a
          - if: "条件2"
            then: step_b
          - else: step_c        ← FallbackLink(target="step_c")

    FallbackLink 必须放在条件列表的最后，作为兜底选项。
    没有额外字段，只需要继承自基类的 target 即可。
    """
    pass
