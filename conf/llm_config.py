import os
from dataclasses import dataclass

from dotenv import load_dotenv
load_dotenv()

@dataclass
class Config:
    llm_base_url: str
    llm_api_key: str
    llm_model: str



llm_config = Config(
    llm_base_url=os.getenv("LLM_BASE_URL"),
    llm_api_key=os.getenv("LLM_API_KEY"),
    llm_model=os.getenv("LLM_MODEL"),

)

if __name__ == "__main__":
    print(llm_config.llm_model)