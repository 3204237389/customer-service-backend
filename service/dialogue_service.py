
from domain.messages import UserMessage, ProcessResult
from domain.state import DialogueState
from repository.dialogue_state_repository import DialogueStateRepository
from engine.dialogue_engine import DialogueEngine


class DialogueService:
    """
    处理对话的业务类
    """

    def __init__(self, dialogue_state_repository: DialogueStateRepository,
                 dialogue_engine: DialogueEngine):
        self.dialogue_state_repository = dialogue_state_repository
        self.dialogue_engine = dialogue_engine

    async def process_message(self, user_message: UserMessage) -> ProcessResult:
        """
        核心处理逻辑(IO：很慢/计算:调用LLM以及执行引擎、比较慢)
        :param user_message:
        :return:
        """
        dialogue_state: DialogueState = await self.dialogue_state_repository.load_state(user_message.sender_id)
        process_result: ProcessResult = await self.dialogue_engine.process_message(dialogue_state, user_message)
        await self.dialogue_state_repository.save_state(dialogue_state)
        return process_result
