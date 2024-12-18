import atexit
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI

import common.routers.status_OK as status_OK
from common.config_loader import config_path, load_config
from common.importer import ImportFromStringError, import_from_string
from common.logging.middleware import LoggerContextMiddleware

# Set up logging

service_name = str(Path(__file__).parent.name)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load configuration
    yield
    # Clean up resources here if needed
    logger.info("Shutting down application")
    ...


app = FastAPI(lifespan=lifespan)
app.add_middleware(LoggerContextMiddleware, logger_name=service_name)

schema_path = Path(__file__).parent / "config_schema.yaml"
config = load_config(config_path, schema_path)
# if logger queue handler is found, start it, it creates a thread and shuts it down when the app is shut down
queue_handler = logging.getHandlerByName("queue_handler")  # type: ignore
if queue_handler is not None:
    queue_handler.listener.start()  # type: ignore
    atexit.register(queue_handler.listener.stop)  # type: ignore

logger = logging.getLogger(service_name)

# Create the main application
# Dynamically import and mount sub-applications based on the configuration
for sub_app_name, sub_app_info in config["sub_routes"].items():
    route_path = sub_app_info["path"]
    app_path = sub_app_info["app"]
    try:
        # Use the import_from_string function to import the sub-application
        sub_app_instance = import_from_string(app_path)

        # Mount the sub-application
        app.mount(route_path, sub_app_instance)
        logger.info(f"Mounted {sub_app_name} at {route_path}")
    except ImportFromStringError as e:
        logger.error(f"Import error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

app.include_router(status_OK.router, prefix="/health")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
