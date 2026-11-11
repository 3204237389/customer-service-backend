from langchain.chat_models import init_chat_model
from openai import base_url

from conf.llm_config import llm_config

llm = init_chat_model(
    model=llm_config.llm_model,
    base_url= llm_config.llm_base_url,
    api_key=llm_config.llm_api_key,
    model_provider="openai",
    temperature=0
)


if __name__ == '__main__':
    res = llm.invoke("你是谁").content
    print(res)