import asyncio
from typing import Annotated, List

from fastapi import Depends, HTTPException, Query
from sqlmodel import select, delete
import uvicorn

from .pet_service_client import DefaultApi  # type: ignore

from services.user_service import pet_service_client

from ._app import app
from . import database, models

from common.routers import status_OK

app.include_router(status_OK.router, prefix="/health")


async def get_pet_from_pet_service(
    pet_id: int,
    session: database.SessionDep,
    api_instance: DefaultApi = Depends(pet_service_client.getApiClient),
):
    pet_response = None
    try:
        pet_response = await api_instance.get_pet_pets_pet_id_get(pet_id)
    except Exception as e:
        print("Exception when calling DefaultApi->get_pet_pets_pet_id_get: %s\n" % e)
    if not pet_response:
        statement = delete(models.UserPetTableObject).where(
            models.UserPetTableObject.pet_id == pet_id  # type: ignore
        )
        session.exec(statement)  # type: ignore
        session.commit()
        raise HTTPException(status_code=404, detail="pet not found")
    return pet_response


async def get_user_pets_from_pet_service(
    user_id: int,
    session: database.SessionDep,
    api_instance: DefaultApi = Depends(pet_service_client.getApiClient),
):
    user = session.get(models.UserTableObject, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    pets = []
    for pet in user.pets_ids:
        try:
            pet_response = await get_pet_from_pet_service(pet.pet_id, session, api_instance)
            pets.append(pet_response)
        except HTTPException as e:
            if e.status_code == 404 and e.detail == "pet not found":
                print("pet not found", pet.pet_id)
    return pets


def format_user_response(user: models.UserTableObject, pets: List[models.UserPetResponseObject]):
    user.id  # TODO: figure out why user.model_dump() and user are "empty", is it related to commiting or changes?
    return {**user.model_dump(), "pets": pets}


async def cast_user_to_response(
    user: models.UserTableObject,
    session: database.SessionDep,
    api_instance: DefaultApi = Depends(pet_service_client.getApiClient),
):
    return format_user_response(
        user,
        await get_user_pets_from_pet_service(user.id, session, api_instance),  # type: ignore
    )


@app.post("/users/", response_model=models.UserResponseObject)
async def create_user(
    user: models.UserCreateObject,
    session: database.SessionDep,
    api_instance: DefaultApi = Depends(pet_service_client.getApiClient),
):
    try:
        db_user = models.UserTableObject.model_validate(user)
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return await cast_user_to_response(db_user, session, api_instance)  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {e}")


@app.get("/users/{user_id}", response_model=models.UserResponseObject)
async def get_user(
    user_id: int,
    session: database.SessionDep,
    api_instance: DefaultApi = Depends(pet_service_client.getApiClient),
):
    user = session.get(models.UserTableObject, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    return await cast_user_to_response(user, session, api_instance)


@app.get("/users/", response_model=List[models.UserResponseObject])
async def list_users(
    session: database.SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
    api_instance: DefaultApi = Depends(pet_service_client.getApiClient),
):
    users = session.exec(select(models.UserTableObject).offset(offset).limit(limit)).all()
    return await asyncio.gather(
        *[cast_user_to_response(user, session, api_instance) for user in users]
    )


@app.patch("/users/{user_id}", response_model=models.UserResponseObject)
async def update_user(
    user_id: int,
    user_update: models.UserUpdateObject,
    session: database.SessionDep,
    api_instance: DefaultApi = Depends(pet_service_client.getApiClient),
):
    db_user = session.get(models.UserTableObject, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="user not found")

    user_data = user_update.model_dump(exclude_unset=True)
    db_user.sqlmodel_update(user_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return await cast_user_to_response(db_user, session, api_instance)


@app.delete("/users/{user_id}")
async def delete_user(user_id: int, session: database.SessionDep) -> dict[str, bool]:
    user = session.get(models.UserTableObject, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    session.delete(user)
    session.commit()
    return {"ok": True}


@app.post("/users/{user_id}/pets/{pet_id}", response_model=models.UserResponseObject)
async def adopt_pet(
    user_id: int,
    pet_id: int,
    session: database.SessionDep,
    api_instance: DefaultApi = Depends(pet_service_client.getApiClient),
):
    user = session.get(models.UserTableObject, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    # Create an instance of the API class
    pet_response = await get_pet_from_pet_service(pet_id, session, api_instance)
    pet = session.get(models.UserPetTableObject, pet_response and pet_response.id)
    if not pet:
        pet = models.UserPetTableObject.model_validate(
            {"pet_id": pet_response.id, "user_id": user_id}
        )
        session.add(pet)
    user.pets_ids.append(pet)
    session.add(user)
    session.commit()
    return await cast_user_to_response(user, session, api_instance)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
