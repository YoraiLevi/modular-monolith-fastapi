from typing import Annotated
from fastapi import Depends

from ..core.service import Service


async def get_service_instance() -> Service:
    raise NotImplementedError("get_service_instance")


ServiceDep = Annotated[Service, Depends(get_service_instance)]


async def get_service_session_instance() -> Service.Session:
    raise NotImplementedError("get_service_session_instance")


ServiceSessionDep = Annotated[Service.Session, Depends(get_service_session_instance)]
