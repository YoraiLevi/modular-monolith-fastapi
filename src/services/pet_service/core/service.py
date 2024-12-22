from datetime import datetime, UTC
from typing import List
from sqlmodel import Session, select
from fastapi import HTTPException
from common.logging import getContextualLogger

from ..models import (
    PetTableObject,
    PetCreateObject,
    PetUpdateObject,
)


class PetService:
    def __init__(self):
        getContextualLogger().info(f"PetService Initialized {id(self)}")

    @staticmethod
    async def create_pet(session: Session, pet: PetCreateObject) -> PetTableObject:
        logger = getContextualLogger()
        logger.info("Creating new pet", extra={"pet_data": pet.model_dump()})
        db_pet = PetTableObject.model_validate(pet)
        session.add(db_pet)
        session.commit()
        session.refresh(db_pet)
        logger.info("Successfully created pet", extra={"pet_id": db_pet.id})
        return db_pet

    @staticmethod
    async def get_pet(session: Session, pet_id: int) -> PetTableObject:
        logger = getContextualLogger()
        logger.debug("Fetching pet", extra={"pet_id": pet_id})
        pet = session.get(PetTableObject, pet_id)
        if pet is None:
            logger.warning("Pet not found", extra={"pet_id": pet_id})
            raise HTTPException(status_code=404, detail="Pet not found")
        return pet

    @staticmethod
    async def list_pets(
        session: Session, offset: int = 0, limit: int = 100
    ) -> List[PetTableObject]:
        logger = getContextualLogger()
        logger.debug("Listing pets", extra={"offset": offset, "limit": limit})
        pets = session.exec(select(PetTableObject).offset(offset).limit(limit)).all()
        logger.info("Retrieved pets list", extra={"count": len(pets)})
        return list(pets)

    @staticmethod
    async def update_pet(
        session: Session, pet_id: int, pet_update: PetUpdateObject
    ) -> PetTableObject:
        logger = getContextualLogger()
        logger.debug(
            "Updating pet", extra={"pet_id": pet_id, "update_data": pet_update.model_dump()}
        )
        db_pet = await PetService.get_pet(session, pet_id)
        pet_data = pet_update.model_dump(exclude_unset=True)
        db_pet.sqlmodel_update(pet_data)
        session.add(db_pet)
        session.commit()
        session.refresh(db_pet)
        logger.info("Successfully updated pet", extra={"pet_id": pet_id})
        return db_pet

    @staticmethod
    async def delete_pet(session: Session, pet_id: int) -> bool:
        logger = getContextualLogger()
        logger.debug("Attempting to delete pet", extra={"pet_id": pet_id})
        pet = await PetService.get_pet(session, pet_id)
        session.delete(pet)
        session.commit()
        logger.info("Successfully deleted pet", extra={"pet_id": pet_id})
        return True

    @staticmethod
    async def hydrate_pet(session: Session, pet_id: int) -> PetTableObject:
        logger = getContextualLogger()
        logger.debug("Hydrating pet", extra={"pet_id": pet_id})
        pet = await PetService.get_pet(session, pet_id)
        pet.last_interaction = datetime.now(UTC)
        session.add(pet)
        session.commit()
        session.refresh(pet)
        logger.info("Successfully hydrated pet", extra={"pet_id": pet_id})
        return pet

    @staticmethod
    async def feed_pet(session: Session, pet_id: int) -> PetTableObject:
        logger = getContextualLogger()
        logger.debug("Feeding pet", extra={"pet_id": pet_id})
        pet = await PetService.get_pet(session, pet_id)
        pet.last_fed = datetime.now(UTC)
        pet.last_interaction = datetime.now(UTC)
        session.add(pet)
        session.commit()
        session.refresh(pet)
        logger.info("Successfully fed pet", extra={"pet_id": pet_id})
        return pet

    @staticmethod
    async def give_treat(session: Session, pet_id: int) -> PetTableObject:
        logger = getContextualLogger()
        logger.debug("Giving treat to pet", extra={"pet_id": pet_id})
        pet = await PetService.get_pet(session, pet_id)
        pet.last_fed = datetime.now(UTC)
        pet.last_interaction = datetime.now(UTC)
        pet.mood = "excited"
        session.add(pet)
        session.commit()
        session.refresh(pet)
        logger.info("Successfully gave treat to pet", extra={"pet_id": pet_id})
        return pet
