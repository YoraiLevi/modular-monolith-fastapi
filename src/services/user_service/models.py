# type: ignore
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel

from .pet_service_client.models import PetResponseObject as UserPetResponseObject


class User(SQLModel):
    name: str = Field(index=True)


class UserCreateObject(User):
    pass


class UserResponseObject(User):
    id: int
    pets: List[UserPetResponseObject]


class UserPet(SQLModel):
    id: int


class UserPetCreateObject(UserPet):
    pass


class UserUpdateObject(User):
    name: Optional[str] = None
    pets_ids: Optional[List[int]] = None


class UserTableObject(User, table=True):
    id: int | None = Field(default=None, primary_key=True)
    pets_ids: list["UserPetTableObject"] = Relationship(back_populates="user")


class UserPetTableObject(UserPet, table=True):
    id: int | None = Field(default=None, primary_key=True)
    pet_id: int = Field(index=True)
    user_id: int = Field(foreign_key="usertableobject.id", index=True)
    user: UserTableObject | None = Relationship(back_populates="pets_ids")
