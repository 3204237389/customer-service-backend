import os
from dataclasses import dataclass

from dotenv import load_dotenv
load_dotenv()

@dataclass
class Config:
    database_url:str


db_config = Config(
    database_url=os.getenv("DATABASE_URL"),
)

if __name__ == "__main__":
    print(db_config.database_url)