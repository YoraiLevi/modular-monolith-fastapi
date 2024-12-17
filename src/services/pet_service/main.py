from typing import Annotated, List

from fastapi import HTTPException, Query
from sqlmodel import select
import uvicorn

from ._app import app
from . import database, models


@app.post("/pets/", response_model=models.PetResponseObject)
async def create_pet(pet: models.PetCreateObject, session: database.SessionDep):
    try:
        db_pet = models.PetTableObject.model_validate(pet)
        session.add(db_pet)
        session.commit()
        session.refresh(db_pet)
        return db_pet
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating pet: {e}")


@app.get("/pets/{pet_id}", response_model=models.PetResponseObject)
async def get_pet(pet_id: int, session: database.SessionDep):
    pet = session.get(models.PetTableObject, pet_id)
    if pet is None:
        raise HTTPException(status_code=404, detail="Pet not found")
    return pet


@app.get("/pets/", response_model=List[models.PetResponseObject])
async def list_pets(
    session: database.SessionDep, offset: int = 0, limit: Annotated[int, Query(le=100)] = 100
):
    pets = session.exec(select(models.PetTableObject).offset(offset).limit(limit)).all()
    return pets


@app.patch("/pets/{pet_id}", response_model=models.PetResponseObject)
async def update_pet(pet_id: int, pet_update: models.PetUpdateObject, session: database.SessionDep):
    db_pet = session.get(models.PetTableObject, pet_id)
    if not db_pet:
        raise HTTPException(status_code=404, detail="Pet not found")

    pet_data = pet_update.model_dump(exclude_unset=True)
    db_pet.sqlmodel_update(pet_data)
    session.add(db_pet)
    session.commit()
    session.refresh(db_pet)
    return db_pet


@app.delete("/pets/{pet_id}")
async def delete_pet(pet_id: int, session: database.SessionDep) -> dict[str, bool]:
    pet = session.get(models.PetTableObject, pet_id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    session.delete(pet)
    session.commit()
    return {"ok": True}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
