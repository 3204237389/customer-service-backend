from contextlib import asynccontextmanager



from fastapi import FastAPI



from api.routers.chat_router import router

from infrastructure.database import close_db_engine, init_db_engine

from infrastructure.http_client import init_http_client, close_http_client





@asynccontextmanager

async def lifespan():

    """

    应用生命周期管理：

        - 启动时：执行 yield 前的代码（初始化数据库引擎）

        - 运行中：yield 让出控制权，FastAPI 处理请求

        - 关闭时：执行 yield 后的代码（关闭数据库引擎）



    注意：

        - app 参数必须指定，类型为 FastAPI

        - 可通过 app.state 存储全局共享资源（当前未使用）

    """



    print("启动服务器...")

    init_db_engine()



    init_http_client()

    yield





    yield









    await close_db_engine()

    await close_http_client()

    print("服务器已关闭")





app = FastAPI(description="电商小二智能客服应用", lifespan=lifespan)



app.include_router(router)