import os
from dataclasses import dataclass

from dotenv import load_dotenv
load_dotenv()

@dataclass
class Config:
    commerce_api_base_url: str


commerce_config = Config(
    commerce_api_base_url=os.getenv("COMMERCE_API_BASE_URL"),
)

if __name__ == "__main__":
    print(commerce_config.commerce_api_base_url)