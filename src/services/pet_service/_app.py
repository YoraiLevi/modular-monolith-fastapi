from contextlib import asynccontextmanager
from fastapi import FastAPI

from common.logging.middleware import LoggerContextMiddleware

from .create_tables import create_tables

create_tables()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Shutdown


app = FastAPI(lifespan=lifespan)
app.add_middleware(LoggerContextMiddleware, logger_name="pet_service")
