import asyncio
from typing import Annotated, List

from fastapi import Depends, HTTPException, Query
from sqlmodel import select, delete

from .pet_service_client import DefaultApi

from services.user_service import pet_service_client

from ._app import app
from . import database, models
from common.routers import status_OK
from common.logging import getContextualLogger

app.include_router(status_OK.router, prefix="/health")


async def get_pet_from_pet_service(
    pet_id: int, session: database.SessionDep, api_instance: DefaultApi
):
    logger = getContextualLogger()
    logger.debug("Fetching pet from pet service", extra={"pet_id": pet_id})
    pet_response = None
    try:
        pet_response = await api_instance.get_pet_pets_pet_id_get(pet_id)
    except Exception as e:
        logger.error(
            "Failed to fetch pet from pet service", extra={"pet_id": pet_id, "error": str(e)}
        )
        print("Exception when calling DefaultApi->get_pet_pets_pet_id_get: %s\n" % e)
    if not pet_response:
        logger.warning(
            "Pet not found in pet service, cleaning up references", extra={"pet_id": pet_id}
        )
        statement = delete(models.UserPetTableObject).where(
            models.UserPetTableObject.pet_id == pet_id  # type: ignore
        )
        logger.debug(
            "Executing SQL",
            extra={"sql": str(statement.compile(compile_kwargs={"literal_binds": True}))},
        )
        session.exec(statement)  # type: ignore
        session.commit()
        raise HTTPException(status_code=404, detail="pet not found")
    return pet_response


async def get_user_pets_from_pet_service(
    user_id: int, session: database.SessionDep, api_instance: DefaultApi
):
    logger = getContextualLogger()
    logger.debug("Fetching user's pets", extra={"user_id": user_id})
    user = session.get(models.UserTableObject, user_id)
    if not user:
        logger.warning("User not found", extra={"user_id": user_id})
        raise HTTPException(status_code=404, detail="user not found")
    pets = []
    for pet in user.pets_ids:
        try:
            pet_response = await get_pet_from_pet_service(pet.pet_id, session, api_instance)
            pets.append(pet_response)
        except HTTPException as e:
            if e.status_code == 404 and e.detail == "pet not found":
                logger.warning(
                    "Pet reference cleanup", extra={"pet_id": pet.pet_id, "user_id": user_id}
                )
    logger.info("Retrieved user's pets", extra={"user_id": user_id, "pet_count": len(pets)})
    return pets


def format_user_response(user: models.UserTableObject, pets: List[models.UserPetResponseObject]):
    user.id  # TODO: figure out why user.model_dump() and user are "empty", is it related to commiting or changes?
    return {**user.model_dump(), "pets": pets}


async def cast_user_to_response(
    user: models.UserTableObject, session: database.SessionDep, api_instance: DefaultApi
):
    if user.id:
        return format_user_response(
            user,
            await get_user_pets_from_pet_service(user.id, session, api_instance),
        )
    else:
        raise HTTPException(status_code=404, detail="user not found")


@app.post("/users/", response_model=models.UserResponseObject)
async def create_user(
    user: models.UserCreateObject,
    session: database.SessionDep,
    api_instance: pet_service_client.ApiClientDep,
):
    logger = getContextualLogger()
    try:
        logger.info("Creating new user", extra={"user_data": user.model_dump()})
        db_user = models.UserTableObject.model_validate(user)
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        response = await cast_user_to_response(db_user, session, api_instance)
        logger.info("Successfully created user", extra={"user_id": db_user.id})
        return response
    except Exception as e:
        logger.error(
            "Failed to create user", extra={"error": str(e), "user_data": user.model_dump()}
        )
        raise HTTPException(status_code=500, detail=f"Error creating user: {e}")


@app.get("/users/{user_id}", response_model=models.UserResponseObject)
async def get_user(
    user_id: int,
    session: database.SessionDep,
    api_instance: pet_service_client.ApiClientDep,
):
    logger = getContextualLogger()
    logger.debug("Fetching user", extra={"user_id": user_id})
    user = session.get(models.UserTableObject, user_id)
    if user is None:
        logger.warning("User not found", extra={"user_id": user_id})
        raise HTTPException(status_code=404, detail="user not found")
    return await cast_user_to_response(user, session, api_instance)


@app.get("/users/", response_model=List[models.UserResponseObject])
async def list_users(
    session: database.SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
    api_instance: DefaultApi = Depends(pet_service_client.getApiClient),
):
    logger = getContextualLogger()
    logger.debug("Listing users", extra={"offset": offset, "limit": limit})
    statement = select(models.UserTableObject).offset(offset).limit(limit)
    logger.debug(
        "Executing SQL",
        extra={"sql": str(statement.compile(compile_kwargs={"literal_binds": True}))},
    )
    users = session.exec(statement).all()
    response = await asyncio.gather(
        *[cast_user_to_response(user, session, api_instance) for user in users]
    )
    logger.info("Retrieved users list", extra={"count": len(users)})
    return response


@app.patch("/users/{user_id}", response_model=models.UserResponseObject)
async def update_user(
    user_id: int,
    user_update: models.UserUpdateObject,
    session: database.SessionDep,
    api_instance: pet_service_client.ApiClientDep,
):
    logger = getContextualLogger()
    logger.debug(
        "Updating user", extra={"user_id": user_id, "update_data": user_update.model_dump()}
    )
    db_user = session.get(models.UserTableObject, user_id)
    if not db_user:
        logger.warning("User not found for update", extra={"user_id": user_id})
        raise HTTPException(status_code=404, detail="user not found")

    user_data = user_update.model_dump(exclude_unset=True)
    db_user.sqlmodel_update(user_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    response = await cast_user_to_response(db_user, session, api_instance)
    logger.info("Successfully updated user", extra={"user_id": user_id})
    return response


@app.delete("/users/{user_id}")
async def delete_user(user_id: int, session: database.SessionDep) -> dict[str, bool]:
    logger = getContextualLogger()
    logger.debug("Attempting to delete user", extra={"user_id": user_id})
    user = session.get(models.UserTableObject, user_id)
    if not user:
        logger.warning("User not found for deletion", extra={"user_id": user_id})
        raise HTTPException(status_code=404, detail="user not found")
    session.delete(user)
    session.commit()
    logger.info("Successfully deleted user", extra={"user_id": user_id})
    return {"ok": True}


@app.post("/users/{user_id}/pets/{pet_id}", response_model=models.UserResponseObject)
async def adopt_pet(
    user_id: int,
    pet_id: int,
    session: database.SessionDep,
    api_instance: pet_service_client.ApiClientDep,
):
    logger = getContextualLogger()
    logger.debug("Processing pet adoption", extra={"user_id": user_id, "pet_id": pet_id})
    user = session.get(models.UserTableObject, user_id)
    if not user:
        logger.warning("User not found for adoption", extra={"user_id": user_id})
        raise HTTPException(status_code=404, detail="user not found")

    pet_response = await get_pet_from_pet_service(pet_id, session, api_instance)
    pet = session.get(models.UserPetTableObject, pet_response and pet_response.id)
    if not pet:
        logger.info(
            "Creating new pet adoption record", extra={"user_id": user_id, "pet_id": pet_id}
        )
        pet = models.UserPetTableObject.model_validate(
            {"pet_id": pet_response.id, "user_id": user_id}
        )
        session.add(pet)
    user.pets_ids.append(pet)
    session.add(user)
    session.commit()
    response = await cast_user_to_response(user, session, api_instance)
    logger.info("Successfully processed pet adoption", extra={"user_id": user_id, "pet_id": pet_id})
    return response


# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)
