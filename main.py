import uvicorn

from conf.api_config import api_config

if __name__ == "__main__":
    uvicorn.run("api.app:app", host=api_config.app_host, port=api_config.app_port)

