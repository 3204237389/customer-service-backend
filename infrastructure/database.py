import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine, AsyncEngine

from conf.db_config import db_config

engine: AsyncEngine | None = None
async_session: async_sessionmaker[AsyncSession] | None = None

def init_db_engine() -> None:
    global engine, async_session

    engine = create_async_engine(db_config.database_url, echo=True, pool_pre_ping=True)

    async_session = async_sessionmaker(engine, expire_on_commit=False)

async def close_db_engine():
    if engine is not None:
        await engine.dispose()


if __name__ == '__main__':
    init_db_engine()


    async def test():
        async with async_session() as session:

            result = await session.execute(text("SELECT * FROM dialogue_states WHERE sender_id = :sender_id"), {"sender_id": 1})

            data = result.fetchone()
            print(data)
            print(type(data))

        await close_db_engine()


    asyncio.run(test())
