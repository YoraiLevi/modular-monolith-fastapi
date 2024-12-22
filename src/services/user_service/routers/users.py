from typing import List, Annotated
from fastapi import APIRouter, Query
from ..models import UserResponseObject, UserCreateObject, UserUpdateObject
from ..dependencies.database import SessionDep
from ..dependencies.service import UserServiceDep
from ..dependencies.pet_service import petServiceDefaultApiClientDep


def create_router():
    router = APIRouter()

    @router.post("/", response_model=UserResponseObject)
    async def create_user(
        user: UserCreateObject,
        user_service: UserServiceDep,
        session: SessionDep,
        api_instance: petServiceDefaultApiClientDep,
    ):
        return await user_service.create_user(user, session, api_instance)

    @router.get("/{user_id}", response_model=UserResponseObject)
    async def get_user(
        user_id: int,
        user_service: UserServiceDep,
        session: SessionDep,
        api_instance: petServiceDefaultApiClientDep,
    ):
        return await user_service.get_user(user_id, session, api_instance)

    @router.get("/", response_model=List[UserResponseObject])
    async def list_users(
        user_service: UserServiceDep,
        session: SessionDep,
        api_instance: petServiceDefaultApiClientDep,
        offset: int = 0,
        limit: Annotated[int, Query(le=100)] = 100,
    ):
        return await user_service.list_users(session, offset, limit, api_instance)

    @router.patch("/{user_id}", response_model=UserResponseObject)
    async def update_user(
        user_id: int,
        user_update: UserUpdateObject,
        user_service: UserServiceDep,
        session: SessionDep,
        api_instance: petServiceDefaultApiClientDep,
    ):
        return await user_service.update_user(user_id, user_update, session, api_instance)

    @router.delete("/{user_id}")
    async def delete_user(
        user_id: int,
        user_service: UserServiceDep,
        session: SessionDep,
    ) -> dict[str, bool]:
        return await user_service.delete_user(user_id, session)

    @router.post("/{user_id}/pets/{pet_id}", response_model=UserResponseObject)
    async def adopt_pet(
        user_id: int,
        pet_id: int,
        user_service: UserServiceDep,
        session: SessionDep,
        api_instance: petServiceDefaultApiClientDep,
    ):
        return await user_service.adopt_pet(user_id, pet_id, session, api_instance)

    return router
