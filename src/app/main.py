import asyncio
import atexit
import inspect
import logging
from pathlib import Path

import uvicorn

from common.config_loader import config_path, load_config
from common.logging.getLogger import getContextualLogger

from .app_factory import app_factory as app_factory


async def init_app_server(app_name: str, app_config: dict):
    app = app_factory(app_name, app_config)
    uvicorn_parameters = inspect.signature(uvicorn.Config).parameters
    uvicorn_arguments = dict(filter(lambda it: it[0] in uvicorn_parameters, app_config.items()))
    getContextualLogger().debug(f"configuring server with uvicorn_arguments: {uvicorn_arguments}")
    server_config = uvicorn.Config(app, **uvicorn_arguments)
    server = uvicorn.Server(server_config)
    return await server.serve()


async def serve(apps_config: dict):
    servers = [
        asyncio.create_task(init_app_server(app_name, app_config))
        for app_name, app_config in apps_config.items()
    ]
    _, pending = await asyncio.wait(servers, return_when=asyncio.FIRST_COMPLETED)

    for server in pending:
        # todo better cancel handling
        server.cancel()


def main():  # TODO: make this configurable from the command line
    try:
        schema_path = Path(__file__).parent / "config_schema.yaml"
        config = load_config(config_path, schema_path)
        # if logger queue handler is found, start it, it creates a thread and shuts it down when the app is shut down
        queue_handler = logging.getHandlerByName("queue_handler")  # type: ignore
        if queue_handler is not None:
            queue_handler.listener.start()  # type: ignore
            atexit.register(queue_handler.listener.stop)  # type: ignore
        apps_config = config.get("apps", {})

        loop = asyncio.new_event_loop()
        if config.get("eager_task_factory", False):
            getContextualLogger().debug("AsyncIO eager task factory enabled")
            loop.set_task_factory(asyncio.eager_task_factory)
        loop.run_until_complete(serve(apps_config))
    except KeyboardInterrupt:
        getContextualLogger().info("Keyboard interrupt detected, shutting down...")


if __name__ == "__main__":
    main()
