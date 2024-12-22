import logging
from fastapi import APIRouter
from ..dependencies.service import ServiceDep, ServiceSessionDep


def create_router():
    router = APIRouter()

    @router.get("/session")
    def call_session(session: ServiceSessionDep):
        logging.debug(f"call_session: {id(session)}")
        return session()

    @router.get("/")
    def call_service(service: ServiceDep):
        logging.debug(f"call_service: {id(service)}")
        return service()

    return router
