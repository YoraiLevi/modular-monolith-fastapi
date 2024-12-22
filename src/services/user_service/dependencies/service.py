from typing import Annotated
from fastapi import Depends

from ..core.service import UserService


def get_user_service_instance():
    raise NotImplementedError("UserService is not implemented")


UserServiceDep = Annotated[UserService, Depends(get_user_service_instance)]
