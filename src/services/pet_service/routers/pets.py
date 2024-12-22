from typing import Annotated, List
from fastapi import APIRouter, Query

from ..dependencies.service import PetServiceDep
from ..dependencies.database import SessionDep
from ..models import PetResponseObject, PetCreateObject, PetUpdateObject


def create_router():
    router = APIRouter()

    @router.post("/", response_model=PetResponseObject)
    async def create_pet(pet: PetCreateObject, service: PetServiceDep, session: SessionDep):
        try:
            db_pet = await service.create_pet(session, pet)
            return db_pet
        except Exception:
            raise

    @router.get("/{pet_id}", response_model=PetResponseObject)
    async def get_pet(pet_id: int, service: PetServiceDep, session: SessionDep):
        return await service.get_pet(session, pet_id)

    @router.get("/", response_model=List[PetResponseObject])
    async def list_pets(
        service: PetServiceDep,
        session: SessionDep,
        offset: int = 0,
        limit: Annotated[int, Query(le=100)] = 100,
    ):
        pets = await service.list_pets(session, offset, limit)
        return pets

    @router.patch("/{pet_id}", response_model=PetResponseObject)
    async def update_pet(
        pet_id: int, pet_update: PetUpdateObject, service: PetServiceDep, session: SessionDep
    ):
        db_pet = await service.update_pet(session, pet_id, pet_update)
        return db_pet

    @router.delete("/{pet_id}")
    async def delete_pet(
        pet_id: int, service: PetServiceDep, session: SessionDep
    ) -> dict[str, bool]:
        await service.delete_pet(session, pet_id)
        return {"ok": True}

    @router.post("/{pet_id}/hydrate", response_model=PetResponseObject)
    async def hydrate_pet(pet_id: int, service: PetServiceDep, session: SessionDep):
        pet = await service.hydrate_pet(session, pet_id)
        return pet

    @router.post("/{pet_id}/feed", response_model=PetResponseObject)
    async def feed_pet(pet_id: int, service: PetServiceDep, session: SessionDep):
        pet = await service.feed_pet(session, pet_id)
        return pet

    @router.post("/{pet_id}/treat", response_model=PetResponseObject)
    async def give_treat(pet_id: int, service: PetServiceDep, session: SessionDep):
        pet = await service.give_treat(session, pet_id)
        return pet

    return router
