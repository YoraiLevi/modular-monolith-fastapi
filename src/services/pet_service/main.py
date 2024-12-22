from contextlib import asynccontextmanager
from fastapi import FastAPI
from common.logging.getLogger import getContextualLogger
from services.pet_service.dependencies.service import get_pet_service_instance
from .dependencies.database import get_engine_instance, init_engine
from common.routers import status_OK
from .routers import pets
from .core.database import create_tables
from .core.service import PetService
from .defaults import DATABASE_URL


def app(database_url: str = DATABASE_URL, *args, **kwargs):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        getContextualLogger().info(
            f"Starting app with args: database_url={database_url}, args={args}, kwargs={kwargs}"
        )
        engine = init_engine(database_url)

        async def get_engine_instance_override():
            return engine

        app.dependency_overrides[get_engine_instance] = get_engine_instance_override
        create_tables(engine)

        pet_service = PetService()

        async def get_pet_service_instance_override():
            return pet_service

        app.dependency_overrides[get_pet_service_instance] = get_pet_service_instance_override
        yield

    app = FastAPI(lifespan=lifespan)
    app.include_router(status_OK.router, prefix="/health")
    app.include_router(pets.create_router(), prefix="")

    return app
