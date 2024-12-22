from typing import Annotated
from fastapi import Depends

from ..core.service import PetService


async def get_pet_service_instance() -> PetService:
    raise NotImplementedError("PetService is not implemented")


PetServiceDep = Annotated[PetService, Depends(get_pet_service_instance)]
