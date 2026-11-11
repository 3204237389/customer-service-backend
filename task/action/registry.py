from typing import Dict

from task.action.base import Action


class ActionRegistry:
    def __init__(self) -> None:
        self._actions:Dict[str,Action] = {}

    def register(self,action:Action):
        """
        注册一个action
        :param action:
        :return:
        """
        self._actions[action.name] = action

    def get(self,name:str)-> Action:
        """
        根据action的name获取action对象
        :param name:
        :return:
        """
        if name not in self._actions:
            raise KeyError(f"Action {name} 不存在")

        return self._actions[name]