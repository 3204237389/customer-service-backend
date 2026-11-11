from domain.messages import BotMessage
from domain.state import DialogueState
from task.command.models import Command
from task.flow.executor import FlowExecutor
from task.flow.flows import FlowsList
from task.command.processor import CommandProcessor
from task.action.runner import ActionRunner


class TaskHandler:

    def __init__(
            self,
            flows:FlowsList,
            command_processor:CommandProcessor,
            action_runner:ActionRunner,
            flow_executor:FlowExecutor,
    ):
        self.flows = flows
        self.command_processor = command_processor
        self.action_runner = action_runner
        self.flow_executor = flow_executor

    async def handle(self, commands: list[Command], state: DialogueState) -> list[BotMessage]:
        self.command_processor.run(commands, state,self.flows)

        messages = await self.flow_executor.run_task(state, self.flows, self.action_runner)

        return messages

