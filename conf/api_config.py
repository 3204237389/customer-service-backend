import os
from dataclasses import dataclass

from dotenv import load_dotenv
load_dotenv()

@dataclass
class Config:
    app_host: str
    app_port: int


api_config = Config(
    app_host=os.getenv("APP_HOST"),
    app_port=int(os.getenv("APP_PORT")),
)

if __name__ == "__main__":
    print(api_config.app_host)