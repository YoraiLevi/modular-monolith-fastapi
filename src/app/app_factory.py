import types
from contextlib import asynccontextmanager

from fastapi import FastAPI

import common.routers.status_OK as status_OK
from common.importer import ImportFromStringError, import_from_string
from common.logging.getLogger import getContextualLogger
from common.logging.middleware import LoggerContextMiddleware

from .MountedLifespanMiddleware import MountedLifespanMiddleware


def app_factory(app_name: str = "app", config: dict | None = None):
    config = {} if config is None else config
    # Set up logging
    logger = getContextualLogger()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield

    app = FastAPI(lifespan=lifespan)
    app.add_middleware(MountedLifespanMiddleware)
    app.add_middleware(LoggerContextMiddleware, logger_name=app_name)

    # Create the main application
    for sub_app_name, sub_app_info in config.get("sub_apps", {}).items():
        # Dynamically import and mount sub-applications based on the configuration
        route_path = sub_app_info.get("path", "")
        subapp_factory = sub_app_info.get("app", FastAPI)
        try:
            # Use the import_from_string function to import the sub-application
            subapp_factory = import_from_string(subapp_factory)
            if isinstance(subapp_factory, types.FunctionType):
                args = sub_app_info.get("args", [])
                assert isinstance(args, list), "args must be a list"
                kwargs = sub_app_info.get("kwargs", {})
                assert isinstance(kwargs, dict), "kwargs must be a dict"
                subapp = subapp_factory(*args, **kwargs)
            else:
                subapp = subapp_factory()
            assert isinstance(subapp, FastAPI)
            subapp.add_middleware(LoggerContextMiddleware, logger_name=f"{app_name}.{sub_app_name}")
            # Mount the sub-application
            app.mount(route_path, subapp)
            logger.info(f"Mounted {sub_app_name} at {route_path}")
        except ImportFromStringError as e:
            logger.error(f"Import error: {e}")
            raise e

    app.include_router(status_OK.router, prefix="/health")
    return app
