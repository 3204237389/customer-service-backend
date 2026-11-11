import asyncio

import httpx
from httpx import AsyncClient



http_client: AsyncClient | None = None

def init_http_client():
    global http_client
    http_client = httpx.AsyncClient()

async def close_http_client():
    if http_client is not None:
        await http_client.aclose()

if __name__ == "__main__":
    async def run():
        init_http_client()
        result = await http_client.get("http://localhost:18081/users/u1001/orders")
        print(result.json())

        await close_http_client()

    asyncio.run(run())