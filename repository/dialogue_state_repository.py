import json
from sqlalchemy.dialects.mysql import insert
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.state import DialogueState
from modles.dialogue_state import DialogueStateRecord


class DialogueStateRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def load_state(self, sender_id: str) -> DialogueState:
        """
        读操作
        :return:
        """
        sql = select(DialogueStateRecord).where(DialogueStateRecord.sender_id == sender_id)

        result = await self.session.execute(sql)

        sate = result.scalar_one_or_none()

        if sate:
            state_dict = json.loads(sate.state_json)
            return DialogueState.model_validate(state_dict)

        return DialogueState(sender_id=sender_id)

    async def save_state(self,dialogue_state:DialogueState ):
        state_json: str = json.dumps(dialogue_state.model_dump(mode="json"))

        insert_stmt = insert(DialogueStateRecord).values(
            sender_id=dialogue_state.sender_id,
            state_json=state_json
        )

        update_stmt = insert_stmt.on_duplicate_key_update(
            state_json=insert_stmt.inserted.state_json
        )

        await  self.session.execute(update_stmt)

        await self.session.commit()
