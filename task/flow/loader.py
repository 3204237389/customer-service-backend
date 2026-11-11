
"""
流程加载器 —— 负责将 YAML 配置文件加载为 Python 数据模型。

核心转换链路：
    YAML 文件  →  yaml.safe_load()  →  dict  →  FlowSlot / FlowStep / Flow  →  FlowsList

整个加载过程：
1. 读取 yml 文件，解析为 Python 字典
2. 解析 slots 部分 → Dict[str, FlowSlot]（全局槽位定义）
3. 解析 flows 部分 → List[Flow]（每个 flow 包含 steps 列表和自动收集的 slots 列表）
4. 组装为 FlowsList 对象，供对话引擎使用

使用方式：
    loader = FlowLoader()
    flows_list = loader.load_many([
        Path('flow_config/user_flows.yml'),     # 用户业务流程（含 slots 定义）
        Path('flow_config/system_flows.yml')     # 系统流程（无 slots 定义）
    ])
"""

from pathlib import Path
from typing import List, Dict, Any

import yaml

from task.flow.flows import FlowsList, Flow, FlowSlot
from task.flow.steps import FlowStep, CollectFlowStep


class FlowLoader:
    """
    流程加载器 —— 读取 YAML 配置文件并转换为 FlowsList 数据模型。

    支持加载单个或多个 yml 文件：
    - load(path)：加载单个 yml 文件，返回 FlowsList
    - load_many(paths)：加载多个 yml 文件，合并为一个 FlowsList（会检测槽位名冲突）

    典型用法是加载 user_flows.yml（业务流程）和 system_flows.yml（系统流程），
    合并后得到包含所有流程和全局槽位的 FlowsList 对象。
    """

    def load_many(self, paths: List[Path]) -> FlowsList:
        """
        加载多个 yml 文件，合并为一个 FlowsList。

        处理流程：
        1. 依次加载每个 yml 文件，得到各自的 FlowsList
        2. 将所有文件的 flows 合并到一个列表中
        3. 将所有文件的 slots 合并到一个字典中（检测重复槽位名，有重复则报错）
        4. 返回合并后的 FlowsList

        为什么要检测重复：
        - user_flows.yml 中定义了 slots（如 order_number）
        - system_flows.yml 中没有 slots
        - 如果两个文件都定义了同名槽位，说明配置有冲突，应该报错

        :param paths: yml 文件路径列表（如 [user_flows.yml, system_flows.yml]）
        :return: 合并后的 FlowsList（包含所有流程和所有槽位）
        """
        flows: List[Flow] = []
        slots: Dict[str, FlowSlot] = {}
        for path in paths:
            single_flows_list = self.load(path)
            flows.extend(single_flows_list.flows)
            duplicate_slot_name = set(slots).intersection(single_flows_list.slots)
            if duplicate_slot_name:
                duplicates = ", ".join(sorted(duplicate_slot_name))
                raise ValueError(
                    f"flow定义中存在重复的槽位名称: {duplicates}."
                )
            slots.update(single_flows_list.slots)
        return FlowsList(flows=flows, slots=slots)

    def load(self, path: Path) -> FlowsList:
        """
        加载单个 yml 文件，解析为 FlowsList 数据模型。

        处理流程：
        1. 用 yaml.safe_load() 将文件内容解析为 Python 字典
        2. 调用 _load_slots() 解析 slots 部分 → Dict[str, FlowSlot]
        3. 调用 _load_flows() 解析 flows 部分 → List[Flow]
        4. 组装为 FlowsList 返回

        :param path: yml 文件路径
        :return: 该文件解析后的 FlowsList
        """
        with open(path, 'r', encoding="utf-8") as f:
            data: Dict[str, Any] = yaml.safe_load(f)

        slots: Dict[str, FlowSlot] = self._load_slots(data.get('slots', {}))

        flows = self._load_flows(data.get('flows', {}), slots)

        return FlowsList(slots=slots, flows=flows)

    def _load_slots(self, yaml_slots_data: Dict[str, Any]) -> Dict[str, FlowSlot]:
        """
        解析 yml 中的 slots 部分，将每个槽位定义转为 FlowSlot 对象。

        yml 中的 slots 结构：
            slots:
              order_number:          ← slot_name（作为字典的 key）
                type: text           ← FlowSlot.type
                label: 订单号         ← FlowSlot.label
                description: ...     ← FlowSlot.description

        解析后：
            {
                "order_number": FlowSlot(name="order_number", type="text", label="订单号", description="用户的订单号"),
                ...
            }

        :param yaml_slots_data: yml 中 slots 部分解析后的字典
        :return: 槽位名字 → FlowSlot 对象的字典
        """
        slots = {}
        for slot_name, slot_dict in yaml_slots_data.items():
            slots[slot_name] = FlowSlot(
                name=slot_name,
                **slot_dict
            )

        return slots

    def _load_flows(self, yaml_flows_data: Dict[str, Any], slots_definition: Dict[str, FlowSlot]) -> List[Flow]:
        """
        解析 yml 中的 flows 部分，将每个流程定义转为 Flow 对象。

        对每个流程：
        1. 将 steps 列表中的每个 step 字典通过 FlowStep.from_dict() 转为步骤子类实例
        2. 通过 _collect_flow_slots() 从 collect 步骤中自动提取该流程需要的槽位
        3. 组装为 Flow 对象

        :param yaml_flows_data: yml 中 flows 部分解析后的字典
        :param slots_definition: 全局槽位定义（来自 yml 的 slots 部分），用于给每个 flow 关联它用到的槽位
        :return: Flow 对象列表
        """
        flows: List[Flow] = []
        for flow_id, flow_dict in yaml_flows_data.items():
            steps = [FlowStep.from_dict(step) for step in flow_dict.get('steps', [])]

            flows.append(
                Flow(
                    id=flow_id,
                    description=flow_dict.get('description', ''),
                    name=flow_dict.get('name'),
                    steps=steps,
                    slots=self._collect_flow_slots(slots_definition, steps)
                )
            )

        return flows

    def _collect_flow_slots(self, slots_definition: Dict[str, FlowSlot],
                            steps: List[FlowStep]) -> List[FlowSlot]:
        """
        从流程的步骤列表中收集该流程需要用到的槽位。

        工作原理：
        1. 遍历流程的所有步骤，只关注 CollectFlowStep（收集步骤）
        2. 取出每个 CollectFlowStep 的 slot_name（如 "order_number"）
        3. 从全局槽位定义中查找对应的 FlowSlot 对象
        4. 去重后返回（同一个流程中不同步骤可能收集同一个槽位，不需要重复给 LLM 看）

        为什么要做这一步：
        - yml 中 flow 没有显式声明自己需要哪些 slots
        - 但 LLM 在做意图识别时需要知道每个 flow 收集哪些信息
        - 所以 loader 自动扫描 flow 的 collect 步骤，提取出该 flow 涉及的槽位

        例如 order_status_query 流程：
        - 有一个 collect 步骤，slot_name="order_number"
        - 从全局 slots 中找到 FlowSlot(name="order_number", type="text", label="订单号", ...)
        - 该 flow 的 slots 列表就包含这一个 FlowSlot

        :param slots_definition: 全局槽位定义字典（key 是槽位名，value 是 FlowSlot）
        :param steps: 当前流程的所有步骤列表
        :return: 当前流程需要用到的 FlowSlot 列表（已去重）
        """
        seen = set()
        flow_slots = []
        for step in steps:

            if not isinstance(step, CollectFlowStep):
                continue

            step_slot_name = step.slot_name
            if step_slot_name in seen:
                continue
            seen.add(step_slot_name)

            slot_definition = slots_definition.get(step_slot_name)
            if slot_definition is not None:
                flow_slots.append(slot_definition)

        return flow_slots


if __name__ == '__main__':
    base_path = Path(__file__).parents[2]
    user_flow_path = base_path / 'flow_config' / 'user_flows.yml'
    system_flow_path = base_path / 'flow_config' / 'system_flows.yml'
    loader = FlowLoader()
    flows_list = loader.load_many([user_flow_path, system_flow_path])
    print(flows_list)
