from contextlib import asynccontextmanager
from fastapi import FastAPI

from common.logging.getLogger import getContextualLogger
from common.routers import status_OK
from .core.service import Service
from .routers import service as service_router
from .dependencies import get_service_instance, get_service_session_instance


def app(*args, **kwargs):
    print(f"Starting app with args: {args} and kwargs: {kwargs}")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        getContextualLogger().info(f"Starting app with args: {args}, kwargs={kwargs}")
        with (
            Service("SERVICE_INSTANCE") as service_instance,
            service_instance.session() as persistent_session,
        ):

            async def get_service_instance_override():
                getContextualLogger().debug("get_service_instance_override Before yield")
                yield service_instance
                getContextualLogger().debug("get_service_instance_override After yield")

            async def get_service_session_instance_override():
                getContextualLogger().debug("get_service_session_instance_override Before yield")
                with (
                    persistent_session as session
                ):  # use service_instance.session() to get a new session instance
                    yield session
                getContextualLogger().debug("get_service_session_instance_override After yield")

            app.dependency_overrides[get_service_instance] = get_service_instance_override
            app.dependency_overrides[get_service_session_instance] = (
                get_service_session_instance_override
            )

            yield

        getContextualLogger().info("Ending Application Lifespan")

    app = FastAPI(lifespan=lifespan)
    app.include_router(status_OK.router, prefix="/health")
    app.include_router(service_router.create_router(), prefix="")

    @app.get("/shutdown")
    async def shutdown():
        # --reload doesn't restart the app after a SIGTERM
        import os
        import signal

        os.kill(os.getpid(), signal.SIGTERM)
        getContextualLogger().info("Shutting down Application")

    return app
