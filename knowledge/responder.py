from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from domain.messages import UserMessage, BotMessage
from domain.state import Turn
from infrastructure.llm import llm
from knowledge.providers import KnowledgeChunk
from prompts.history_builder import HistoryBuilder
from prompts.loader import load_prompt


class KnowledgeResponder:

    @staticmethod
    async def respond(
            user_message: UserMessage,
            recent_turns: list[Turn],
            chunks: list[KnowledgeChunk]
    ) -> list[BotMessage]:

        user_message = HistoryBuilder.render_user_message(user_message)

        history = HistoryBuilder.build(recent_turns)

        knowledge_content = "\n\n".join([chunk.content for chunk in chunks])

        prompt_text = load_prompt("knowledge_respond")
        prompt = PromptTemplate.from_template(
            prompt_text,
            template_format="jinja2"
        )
        chain = prompt | llm | StrOutputParser()

        response = await chain.ainvoke({
            "user_message": user_message,
            "history": history,
            "knowledge_content": knowledge_content,
        })

        return [BotMessage(text=response)]
