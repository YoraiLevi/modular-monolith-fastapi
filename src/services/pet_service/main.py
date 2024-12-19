from typing import Annotated, List

from fastapi import HTTPException, Query
from sqlmodel import select
import uvicorn

from ._app import app
from . import database, models
from common.routers import status_OK
from common.logging import getContextualLogger

app.include_router(status_OK.router, prefix="/health")


@app.post("/pets/", response_model=models.PetResponseObject)
async def create_pet(pet: models.PetCreateObject, session: database.SessionDep):
    logger = getContextualLogger()
    try:
        logger.info("Creating new pet", extra={"pet_data": pet.model_dump()})
        db_pet = models.PetTableObject.model_validate(pet)
        session.add(db_pet)
        session.commit()
        session.refresh(db_pet)
        logger.info("Successfully created pet", extra={"pet_id": db_pet.id})
        return db_pet
    except Exception as e:
        logger.error("Failed to create pet", extra={"error": str(e), "pet_data": pet.model_dump()})
        raise HTTPException(status_code=500, detail=f"Error creating pet: {e}")


@app.get("/pets/{pet_id}", response_model=models.PetResponseObject)
async def get_pet(pet_id: int, session: database.SessionDep):
    logger = getContextualLogger()
    logger.debug("Fetching pet", extra={"pet_id": pet_id})
    pet = session.get(models.PetTableObject, pet_id)
    if pet is None:
        logger.warning("Pet not found", extra={"pet_id": pet_id})
        raise HTTPException(status_code=404, detail="Pet not found")
    return pet


@app.get("/pets/", response_model=List[models.PetResponseObject])
async def list_pets(
    session: database.SessionDep, offset: int = 0, limit: Annotated[int, Query(le=100)] = 100
):
    logger = getContextualLogger()
    logger.debug("Listing pets", extra={"offset": offset, "limit": limit})
    pets = session.exec(select(models.PetTableObject).offset(offset).limit(limit)).all()
    logger.info("Retrieved pets list", extra={"count": len(pets)})
    return pets


@app.patch("/pets/{pet_id}", response_model=models.PetResponseObject)
async def update_pet(pet_id: int, pet_update: models.PetUpdateObject, session: database.SessionDep):
    logger = getContextualLogger()
    logger.debug("Updating pet", extra={"pet_id": pet_id, "update_data": pet_update.model_dump()})
    db_pet = session.get(models.PetTableObject, pet_id)
    if not db_pet:
        logger.warning("Pet not found for update", extra={"pet_id": pet_id})
        raise HTTPException(status_code=404, detail="Pet not found")

    pet_data = pet_update.model_dump(exclude_unset=True)
    db_pet.sqlmodel_update(pet_data)
    session.add(db_pet)
    session.commit()
    session.refresh(db_pet)
    logger.info("Successfully updated pet", extra={"pet_id": pet_id})
    return db_pet


@app.delete("/pets/{pet_id}")
async def delete_pet(pet_id: int, session: database.SessionDep) -> dict[str, bool]:
    logger = getContextualLogger()
    logger.debug("Attempting to delete pet", extra={"pet_id": pet_id})
    pet = session.get(models.PetTableObject, pet_id)
    if not pet:
        logger.warning("Pet not found for deletion", extra={"pet_id": pet_id})
        raise HTTPException(status_code=404, detail="Pet not found")
    session.delete(pet)
    session.commit()
    logger.info("Successfully deleted pet", extra={"pet_id": pet_id})
    return {"ok": True}


@app.post("/pets/{pet_id}/hydrate", response_model=models.PetResponseObject)
async def hydrate_pet(pet_id: int, session: database.SessionDep):
    logger = getContextualLogger()
    logger.debug("Hydrating pet", extra={"pet_id": pet_id})
    pet = session.get(models.PetTableObject, pet_id)
    if not pet:
        logger.warning("Pet not found for hydration", extra={"pet_id": pet_id})
        raise HTTPException(status_code=404, detail="Pet not found")

    from datetime import datetime, UTC

    pet.last_interaction = datetime.now(UTC)
    session.add(pet)
    session.commit()
    session.refresh(pet)
    logger.info("Successfully hydrated pet", extra={"pet_id": pet_id})
    return pet


@app.post("/pets/{pet_id}/feed", response_model=models.PetResponseObject)
async def feed_pet(pet_id: int, session: database.SessionDep):
    logger = getContextualLogger()
    logger.debug("Feeding pet", extra={"pet_id": pet_id})
    pet = session.get(models.PetTableObject, pet_id)
    if not pet:
        logger.warning("Pet not found for feeding", extra={"pet_id": pet_id})
        raise HTTPException(status_code=404, detail="Pet not found")

    from datetime import datetime, UTC

    pet.last_fed = datetime.now(UTC)
    pet.last_interaction = datetime.now(UTC)
    session.add(pet)
    session.commit()
    session.refresh(pet)
    logger.info("Successfully fed pet", extra={"pet_id": pet_id})
    return pet


@app.post("/pets/{pet_id}/treat", response_model=models.PetResponseObject)
async def give_treat(pet_id: int, session: database.SessionDep):
    logger = getContextualLogger()
    logger.debug("Giving treat to pet", extra={"pet_id": pet_id})
    pet = session.get(models.PetTableObject, pet_id)
    if not pet:
        logger.warning("Pet not found for treat", extra={"pet_id": pet_id})
        raise HTTPException(status_code=404, detail="Pet not found")

    from datetime import datetime, UTC

    pet.last_fed = datetime.now(UTC)
    pet.last_interaction = datetime.now(UTC)
    pet.mood = "excited"  # Treats make pets excited!
    session.add(pet)
    session.commit()
    session.refresh(pet)
    logger.info("Successfully gave treat to pet", extra={"pet_id": pet_id})
    return pet


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
