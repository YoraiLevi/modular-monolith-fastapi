import asyncio
import inspect
import logging
from pathlib import Path
from itertools import zip_longest
from typing import Any, Callable
import uvicorn
import click
from common.config_loader import load_config

from app.app_factory import app_factory as app_factory

import socket
from uvicorn.supervisors import ChangeReload, Multiprocess
from uvicorn._types import ASGIApplication


def create_config_from_config(app: ASGIApplication | Callable[..., Any] | str, config: dict):
    uvicorn_parameters = inspect.signature(uvicorn.Config).parameters
    uvicorn_arguments = dict(filter(lambda it: it[0] in uvicorn_parameters, config.items()))
    return uvicorn.Config(app, **uvicorn_arguments)


def create_server_from_configured_config(config: uvicorn.Config):
    return uvicorn.Server(config)


def create_server_and_config_from_config(app_name: str, app_config: dict):
    app = app_factory(app_name, app_config)
    server_config = create_config_from_config(app, app_config)
    server = create_server_from_configured_config(server_config)
    return server_config, server


class AppServerManager:
    def __init__(self, launch_config: dict):
        self.launch_config = launch_config

    @property
    def apps_config(self):
        return self.launch_config.get("apps", {})

    def prepare(self):
        configs = []
        servers = []
        for app_name, app_config in self.apps_config.items():
            config, server = create_server_and_config_from_config(app_name, app_config)
            configs.append(config)
            servers.append(server)
        return configs, servers

    def run(
        self, sockets: list[list[socket.socket] | socket.socket] | list[socket.socket] | None = None
    ):
        configs, servers = self.prepare()

        async def serve(servers):
            for server in servers:
                server.config.configure_logging()
            return await asyncio.gather(
                *[
                    server.serve(sockets=socket)
                    for socket, server in zip_longest(sockets or [], servers)
                ]
            )

        configs[0].setup_event_loop()
        # for config in configs:
        #     config.configure_logging()
        if self.launch_config.get("eager_task_factory", False):
            loop = asyncio.new_event_loop()
            loop.set_task_factory(asyncio.eager_task_factory)
            return loop.run_until_complete(serve(servers))
        return asyncio.run(serve(servers))


class SocketList(list):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def close(self):
        for sock in self:
            sock.close()


@click.command()
@click.option("--config", type=click.Path(exists=True))
@click.option(
    "--schema", type=click.Path(exists=True), default=Path(__file__).parent / "config_schema.yaml"
)
@click.option("--reload", is_flag=True, default=False, help="Enable auto-reload.")
@click.option(
    "--reload-dir",
    "reload_dirs",
    multiple=True,
    help="Set reload directories explicitly, instead of using the current working" " directory.",
    type=click.Path(exists=True),
)
@click.option(
    "--reload-include",
    "reload_includes",
    multiple=True,
    help="Set glob patterns to include while watching for files. Includes '*.py' "
    "by default; these defaults can be overridden with `--reload-exclude`. "
    "This option has no effect unless watchfiles is installed.",
)
@click.option(
    "--reload-exclude",
    "reload_excludes",
    multiple=True,
    help="Set glob patterns to exclude while watching for files. Includes "
    "'.*, .py[cod], .sw.*, ~*' by default; these defaults can be overridden "
    "with `--reload-include`. This option has no effect unless watchfiles is "
    "installed.",
)
def main(
    config: str,
    schema: str,
    reload: bool | None = None,
    reload_dirs: list[str] | str | None = None,
    reload_includes: list[str] | str | None = None,
    reload_excludes: list[str] | str | None = None,
):
    launch_config = load_config(config, schema)
    if reload:
        launch_config["reload"] = reload
    if reload_dirs:
        launch_config["reload_dirs"] = reload_dirs
    if reload_includes:
        launch_config["reload_includes"] = reload_includes
    if reload_excludes:
        launch_config["reload_excludes"] = reload_excludes
    uvicorn_config = create_config_from_config("", launch_config)
    # uvicorn_config.configure_logging()
    servers = AppServerManager(launch_config)
    configs, _ = servers.prepare()
    try:
        if uvicorn_config.should_reload:
            sockets = [SocketList([config.bind_socket()]) for config in configs]
            ChangeReload(uvicorn_config, target=servers.run, sockets=sockets).run()  # type: ignore
        elif uvicorn_config.workers > 1:
            raise NotImplementedError("Multiprocess not verified to be operational")
            logging.info("MULTIPROCESS")
            sockets = [[config.bind_socket()] for config in configs]
            Multiprocess(uvicorn_config, target=servers.run, sockets=sockets).run()
        else:
            servers.run()
    except KeyboardInterrupt:
        pass  # pragma: full coverage
    finally:
        pass


if __name__ == "__main__":
    main()
