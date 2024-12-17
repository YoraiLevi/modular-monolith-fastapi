# type: ignore
from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime


class BasePet(SQLModel):
    name: Optional[str] = None
    species: Optional[str] = None
    age: Optional[int] = None
    mood: Optional[str] = None


class PetStrictSchema(BasePet):
    name: str = Field(index=True)
    species: str
    age: int = Field(default=None, index=True)
    mood: str = Field(default="happy")


class PetCreateObject(PetStrictSchema):
    pass


class PetResponseObject(PetStrictSchema):
    id: int
    last_fed: datetime | None
    last_interaction: datetime | None


class PetUpdateObject(BasePet):
    name: Optional[str] = None
    species: Optional[str] = None
    age: Optional[int] = None
    mood: Optional[str] = None


class PetTableObject(PetStrictSchema, table=True):
    id: int | None = Field(default=None, primary_key=True)
    last_interaction: datetime | None = Field(default_factory=datetime.utcnow, index=True)
    last_fed: datetime | None = Field(default_factory=datetime.utcnow, index=True)
