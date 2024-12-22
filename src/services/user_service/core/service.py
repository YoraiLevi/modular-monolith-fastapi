from typing import List
import asyncio
from fastapi import HTTPException
from sqlmodel import Session, delete, select
from common.logging import getContextualLogger
from ..models import (
    UserTableObject,
    UserCreateObject,
    UserUpdateObject,
    UserPetTableObject,
    UserPetResponseObject,
)
from ..pet_service_client import DefaultApi


class UserService:
    def __init__(self):
        getContextualLogger().info(f"UserService Initialized {id(self)}")

    @staticmethod
    async def get_pet_from_pet_service(pet_id: int, session: Session, api_instance: DefaultApi):
        logger = getContextualLogger()
        logger.debug("Fetching pet from pet service", extra={"pet_id": pet_id})
        pet_response = None
        try:
            pet_response = await api_instance.get_pet_pet_id_get(pet_id)
        except Exception as e:
            logger.error(
                "Failed to fetch pet from pet service", extra={"pet_id": pet_id, "error": str(e)}
            )
            print("Exception when calling DefaultApi->get_pet_pet_id_get: %s\n" % e)
        if not pet_response:
            logger.warning(
                "Pet not found in pet service, cleaning up references", extra={"pet_id": pet_id}
            )
            statement = delete(UserPetTableObject).where(
                UserPetTableObject.pet_id == pet_id  # type: ignore
            )
            logger.debug(
                "Executing SQL",
                extra={"sql": str(statement.compile(compile_kwargs={"literal_binds": True}))},
            )
            session.exec(statement)  # type: ignore
            session.commit()
            raise HTTPException(status_code=404, detail="pet not found")
        return pet_response

    @staticmethod
    def format_user_response(user: UserTableObject, pets: List[UserPetResponseObject]):
        user.id  # TODO: figure out why user.model_dump() and user are "empty"
        return {**user.model_dump(), "pets": pets}

    @staticmethod
    async def cast_user_to_response(
        user: UserTableObject, session: Session, api_instance: DefaultApi
    ):
        if user.id:
            return UserService.format_user_response(
                user,
                await UserService.get_user_pets_from_pet_service(user.id, session, api_instance),
            )
        else:
            raise HTTPException(status_code=404, detail="user not found")

    @staticmethod
    async def get_user_pets_from_pet_service(
        user_id: int, session: Session, api_instance: DefaultApi
    ):
        logger = getContextualLogger()
        logger.debug("Fetching user's pets", extra={"user_id": user_id})
        user = session.get(UserTableObject, user_id)
        if not user:
            logger.warning("User not found", extra={"user_id": user_id})
            raise HTTPException(status_code=404, detail="user not found")
        pets = []
        for pet in user.pets_ids:
            try:
                pet_response = await UserService.get_pet_from_pet_service(
                    pet.pet_id, session, api_instance
                )
                pets.append(pet_response)
            except HTTPException as e:
                if e.status_code == 404 and e.detail == "pet not found":
                    logger.warning(
                        "Pet reference cleanup", extra={"pet_id": pet.pet_id, "user_id": user_id}
                    )
        logger.info("Retrieved user's pets", extra={"user_id": user_id, "pet_count": len(pets)})
        return pets

    @staticmethod
    async def create_user(user: UserCreateObject, session: Session, api_instance: DefaultApi):
        logger = getContextualLogger()
        try:
            logger.info("Creating new user", extra={"user_data": user.model_dump()})
            db_user = UserTableObject.model_validate(user)
            session.add(db_user)
            session.commit()
            session.refresh(db_user)
            response = await UserService.cast_user_to_response(db_user, session, api_instance)
            logger.info("Successfully created user", extra={"user_id": db_user.id})
            return response
        except Exception as e:
            logger.error(
                "Failed to create user", extra={"error": str(e), "user_data": user.model_dump()}
            )
            raise HTTPException(status_code=500, detail=f"Error creating user: {e}")

    @staticmethod
    async def get_user(user_id: int, session: Session, api_instance: DefaultApi):
        logger = getContextualLogger()
        logger.debug("Fetching user", extra={"user_id": user_id})
        user = session.get(UserTableObject, user_id)
        if user is None:
            logger.warning("User not found", extra={"user_id": user_id})
            raise HTTPException(status_code=404, detail="user not found")
        return await UserService.cast_user_to_response(user, session, api_instance)

    @staticmethod
    async def list_users(session: Session, offset: int, limit: int, api_instance: DefaultApi):
        logger = getContextualLogger()
        logger.debug("Listing users", extra={"offset": offset, "limit": limit})
        statement = select(UserTableObject).offset(offset).limit(limit)
        logger.debug(
            "Executing SQL",
            extra={"sql": str(statement.compile(compile_kwargs={"literal_binds": True}))},
        )
        users = session.exec(statement).all()
        response = await asyncio.gather(
            *[UserService.cast_user_to_response(user, session, api_instance) for user in users]
        )
        logger.info("Retrieved users list", extra={"count": len(users)})
        return response

    @staticmethod
    async def update_user(
        user_id: int, user_update: UserUpdateObject, session: Session, api_instance: DefaultApi
    ):
        logger = getContextualLogger()
        logger.debug(
            "Updating user", extra={"user_id": user_id, "update_data": user_update.model_dump()}
        )
        db_user = session.get(UserTableObject, user_id)
        if not db_user:
            logger.warning("User not found for update", extra={"user_id": user_id})
            raise HTTPException(status_code=404, detail="user not found")

        user_data = user_update.model_dump(exclude_unset=True)
        db_user.sqlmodel_update(user_data)
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        response = await UserService.cast_user_to_response(db_user, session, api_instance)
        logger.info("Successfully updated user", extra={"user_id": user_id})
        return response

    @staticmethod
    async def delete_user(user_id: int, session: Session) -> dict[str, bool]:
        logger = getContextualLogger()
        logger.debug("Attempting to delete user", extra={"user_id": user_id})
        user = session.get(UserTableObject, user_id)
        if not user:
            logger.warning("User not found for deletion", extra={"user_id": user_id})
            raise HTTPException(status_code=404, detail="user not found")
        session.delete(user)
        session.commit()
        logger.info("Successfully deleted user", extra={"user_id": user_id})
        return {"ok": True}

    @staticmethod
    async def adopt_pet(user_id: int, pet_id: int, session: Session, api_instance: DefaultApi):
        logger = getContextualLogger()
        logger.debug("Processing pet adoption", extra={"user_id": user_id, "pet_id": pet_id})
        user = session.get(UserTableObject, user_id)
        if not user:
            logger.warning("User not found for adoption", extra={"user_id": user_id})
            raise HTTPException(status_code=404, detail="user not found")

        pet_response = await UserService.get_pet_from_pet_service(pet_id, session, api_instance)
        pet = session.get(UserPetTableObject, pet_response and pet_response.id)
        if not pet:
            logger.info(
                "Creating new pet adoption record", extra={"user_id": user_id, "pet_id": pet_id}
            )
            pet = UserPetTableObject.model_validate({"pet_id": pet_response.id, "user_id": user_id})
            session.add(pet)
        user.pets_ids.append(pet)
        session.add(user)
        session.commit()
        response = await UserService.cast_user_to_response(user, session, api_instance)
        logger.info(
            "Successfully processed pet adoption", extra={"user_id": user_id, "pet_id": pet_id}
        )
        return response
