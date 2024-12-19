from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from ..main import app
from ..database import get_session
from ..models import PetTableObject

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite://"


@pytest.fixture(name="session")
def session_fixture() -> Generator[Session, None, None]:
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(session: Session) -> Generator[TestClient, None, None]:
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.mark.anyio
def test_create_pet(client: TestClient):
    pet_data = {"name": "Fluffy", "species": "cat", "age": 3}  # mood is optional with default
    response = client.post("/pets/", json=pet_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == pet_data["name"]
    assert data["species"] == pet_data["species"]
    assert data["age"] == pet_data["age"]
    assert data["mood"] == "happy"  # default value
    assert "id" in data
    assert "last_fed" in data
    assert "last_interaction" in data


@pytest.mark.anyio
def test_create_pet_invalid(client: TestClient):
    response = client.post("/pets/", json={"name": "Invalid"})  # missing required fields
    assert response.status_code == 422


@pytest.mark.anyio
def test_read_pets(client: TestClient, session: Session):
    # Create test pets
    pet1 = PetTableObject(name="Pet1", species="dog", age=2)
    pet2 = PetTableObject(name="Pet2", species="cat", age=3)
    session.add(pet1)
    session.add(pet2)
    session.commit()

    response = client.get("/pets/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Pet1"
    assert data[1]["name"] == "Pet2"


@pytest.mark.anyio
def test_read_pet(client: TestClient, session: Session):
    pet = PetTableObject(name="TestPet", species="dog", age=2)
    session.add(pet)
    session.commit()

    response = client.get(f"/pets/{pet.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "TestPet"
    assert data["species"] == "dog"
    assert data["age"] == 2
    assert data["mood"] == "happy"  # default value
    assert "last_fed" in data
    assert "last_interaction" in data


@pytest.mark.anyio
def test_read_pet_not_found(client: TestClient):
    response = client.get("/pets/999")
    assert response.status_code == 404


@pytest.mark.anyio
def test_update_pet(client: TestClient, session: Session):
    pet = PetTableObject(name="OldName", species="dog", age=2)
    session.add(pet)
    session.commit()
    session.refresh(pet)

    update_data = {
        "name": "NewName",
        "species": "cat",
        "age": 3,
        "mood": "excited",
    }
    response = client.patch(f"/pets/{pet.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == pet.id
    assert data["name"] == update_data["name"]
    assert data["species"] == update_data["species"]
    assert data["age"] == update_data["age"]
    assert data["mood"] == update_data["mood"]
    assert "last_fed" in data
    assert "last_interaction" in data


@pytest.mark.anyio
def test_update_pet_no_changes_undefined_fields(client: TestClient, session: Session):
    pet = PetTableObject(name="OldName", species="dog", age=2)
    session.add(pet)
    session.commit()
    session.refresh(pet)
    update_data = {}
    response = client.patch(f"/pets/{pet.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == pet.id
    assert data["name"] == pet.name
    assert data["species"] == pet.species
    assert data["age"] == pet.age
    assert data["mood"] == "happy"  # default value


@pytest.mark.anyio
def test_update_pet_partial(client: TestClient, session: Session):
    pet = PetTableObject(name="OldName", species="dog", age=2)
    session.add(pet)
    session.commit()
    session.refresh(pet)
    update_data = {
        "name": "NewName",
        "species": "cat",
    }
    response = client.patch(f"/pets/{pet.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == pet.id
    assert data["name"] == update_data["name"]
    assert data["species"] == update_data["species"]
    assert data["age"] == pet.age
    assert data["mood"] == "happy"  # default value


@pytest.mark.anyio
def test_delete_pet(client: TestClient, session: Session):
    pet = PetTableObject(name="ToDelete", species="dog", age=2)
    session.add(pet)
    session.commit()

    response = client.delete(f"/pets/{pet.id}")
    assert response.status_code == 200
    assert response.json() == {"ok": True}

    # Verify pet is deleted
    response = client.get(f"/pets/{pet.id}")
    assert response.status_code == 404


@pytest.mark.anyio
def test_delete_pet_not_found(client: TestClient):
    response = client.delete("/pets/999")
    assert response.status_code == 404


@pytest.mark.anyio
def test_list_pets_pagination(client: TestClient, session: Session):
    # Create 15 test pets
    for i in range(15):
        pet = PetTableObject(name=f"Pet{i}", species="dog", age=i)
        session.add(pet)
    session.commit()

    # Test default pagination
    response = client.get("/pets/")
    assert response.status_code == 200
    assert len(response.json()) == 15  # Default limit is 100

    # Test with limit
    response = client.get("/pets/?limit=5")
    assert response.status_code == 200
    assert len(response.json()) == 5

    # Test with offset
    response = client.get("/pets/?offset=10")
    assert response.status_code == 200
    assert len(response.json()) == 5  # Should get last 5 pets

    # Test with both offset and limit
    response = client.get("/pets/?offset=5&limit=5")
    assert response.status_code == 200
    assert len(response.json()) == 5
    assert response.json()[0]["name"] == "Pet5"


@pytest.mark.anyio
def test_hydrate_pet(client: TestClient, session: Session):
    pet = PetTableObject(name="TestPet", species="dog", age=2)
    session.add(pet)
    session.commit()
    session.refresh(pet)

    initial_interaction = pet.last_interaction
    response = client.post(f"/pets/{pet.id}/hydrate")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == pet.id
    assert data["last_interaction"] > initial_interaction.isoformat()  # type: ignore


@pytest.mark.anyio
def test_hydrate_pet_not_found(client: TestClient):
    response = client.post("/pets/999/hydrate")
    assert response.status_code == 404


@pytest.mark.anyio
def test_feed_pet(client: TestClient, session: Session):
    pet = PetTableObject(name="TestPet", species="dog", age=2)
    session.add(pet)
    session.commit()
    session.refresh(pet)

    initial_fed = pet.last_fed
    initial_interaction = pet.last_interaction
    response = client.post(f"/pets/{pet.id}/feed")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == pet.id
    assert data["last_fed"] > initial_fed.isoformat()  # type: ignore
    assert data["last_interaction"] > initial_interaction.isoformat()  # type: ignore


@pytest.mark.anyio
def test_feed_pet_not_found(client: TestClient):
    response = client.post("/pets/999/feed")
    assert response.status_code == 404


@pytest.mark.anyio
def test_give_treat(client: TestClient, session: Session):
    pet = PetTableObject(name="TestPet", species="dog", age=2)
    session.add(pet)
    session.commit()
    session.refresh(pet)

    initial_fed = pet.last_fed
    initial_interaction = pet.last_interaction
    initial_mood = pet.mood
    response = client.post(f"/pets/{pet.id}/treat")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == pet.id
    assert data["last_fed"] > initial_fed.isoformat()  # type: ignore
    assert data["last_interaction"] > initial_interaction.isoformat()  # type: ignore
    assert data["mood"] == "excited"
    assert data["mood"] != initial_mood


@pytest.mark.anyio
def test_give_treat_not_found(client: TestClient):
    response = client.post("/pets/999/treat")
    assert response.status_code == 404
