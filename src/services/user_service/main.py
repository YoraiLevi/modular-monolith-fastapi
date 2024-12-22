from contextlib import asynccontextmanager
from fastapi import FastAPI
from common.logging.getLogger import getContextualLogger
from common.routers import status_OK
from services.user_service.core.service import UserService
from services.user_service.dependencies.pet_service import get_pet_service_api_client
from services.user_service.dependencies.service import get_user_service_instance
from services.user_service.pet_service_client import create_pet_service_api_client
from .routers import users
from .core.database import create_tables
from .dependencies.database import get_engine_instance, init_engine
from .defaults import DATABASE_URL, PET_SERVICE_URL


def app(database_url: str = DATABASE_URL, pet_service_url: str = PET_SERVICE_URL, *args, **kwargs):
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

        user_service = UserService()

        async def get_user_service_instance_override():
            return user_service

        app.dependency_overrides[get_user_service_instance] = get_user_service_instance_override

        pet_service_api_client = create_pet_service_api_client(pet_service_url)

        async def get_pet_service_api_client_override():
            return pet_service_api_client

        app.dependency_overrides[get_pet_service_api_client] = get_pet_service_api_client_override
        yield

    app = FastAPI(lifespan=lifespan)
    app.include_router(status_OK.router, prefix="/health")
    app.include_router(users.create_router(), prefix="")

    return app
