from typing import Generator

from fastapi import FastAPI
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from services.user_service.core.service import UserService
from services.user_service.dependencies.pet_service import get_pet_service_api_client
from services.user_service.dependencies.service import get_user_service_instance
from ..models import UserPetResponseObject
from datetime import datetime, UTC
from ..pet_service_client import DefaultApi
from sqlmodel import select
from ..main import app
from ..dependencies.database import get_session
from ..models import UserTableObject, UserPetTableObject

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


@pytest.fixture(name="userServiceInstance")
def get_user_service_instance_fixture() -> UserService:
    return UserService()


@pytest.fixture(name="app")
def app_fixture() -> FastAPI:
    return app(database_url=TEST_DATABASE_URL)


@pytest.fixture(name="client")
def client_fixture(
    mocker, app: FastAPI, session: Session, userServiceInstance: UserService
) -> Generator[TestClient, None, None]:
    def get_session_override():
        return session

    def get_user_service_instance_override():
        return userServiceInstance

    def get_pet_service_api_client_override():
        return mocker.AsyncMock()

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_user_service_instance] = get_user_service_instance_override
    app.dependency_overrides[get_pet_service_api_client] = get_pet_service_api_client_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="mock_pet_service")
def mock_pet_service():
    with patch(
        "services.user_service.dependencies.pet_service.get_pet_service_default_api_client"
    ) as mock:
        mock_client = AsyncMock()
        mock.return_value = mock_client
        # Configure the mock to return proper values
        mock_client.get_pet_pet_id_get = AsyncMock()
        mock_client.get_pet_pet_id_get.return_value = None  # Default return value
        yield mock_client


@pytest.mark.anyio
def test_create_user(client: TestClient, mock_pet_service):
    # Mock the pet service to return empty list of pets
    mock_pet_service.get_pet_pet_id_get.side_effect = Exception("Not Found")

    response = client.post(
        "/",
        json={"name": "John Doe"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "John Doe"
    assert "id" in data
    assert data["pets"] == []


@pytest.mark.anyio
def test_create_user_invalid(client: TestClient):
    response = client.post("/", json={})  # Missing required name field
    assert response.status_code == 422


@pytest.mark.anyio
def test_read_user(client: TestClient, mock_pet_service, session: Session):
    # Mock the pet service to return empty list of pets
    mock_pet_service.get_pet_pet_id_get.side_effect = Exception("Not Found")

    # Create a user directly in the database
    user = UserTableObject(name="Jane Doe")
    session.add(user)
    session.commit()

    response = client.get(f"/{user.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Jane Doe"
    assert data["pets"] == []


@pytest.mark.anyio
def test_read_users(client: TestClient, mock_pet_service, session: Session):
    # Mock the pet service to return empty list of pets
    mock_pet_service.get_pet_pet_id_get.side_effect = Exception("Not Found")

    # Create test users
    user1 = UserTableObject(name="User1")
    user2 = UserTableObject(name="User2")
    session.add(user1)
    session.add(user2)
    session.commit()

    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "User1"
    assert data[1]["name"] == "User2"


@pytest.mark.anyio
def test_update_user(client: TestClient, mock_pet_service, session: Session):
    # Mock the pet service to return empty list of pets
    mock_pet_service.get_pet_pet_id_get.side_effect = Exception("Not Found")

    # Create a user
    user = UserTableObject(name="Old Name")
    session.add(user)
    session.commit()
    session.refresh(user)

    update_data = {"name": "New Name"}
    response = client.patch(f"/{user.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"


@pytest.mark.anyio
def test_update_user_no_changes(client: TestClient, mock_pet_service, session: Session):
    # Mock the pet service to return empty list of pets
    mock_pet_service.get_pet_pet_id_get.side_effect = Exception("Not Found")

    user = UserTableObject(name="Test Name")
    session.add(user)
    session.commit()
    session.refresh(user)

    update_data = {}
    response = client.patch(f"/{user.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == user.name


@pytest.mark.anyio
def test_delete_user(client: TestClient, mock_pet_service, session: Session):
    # Mock the pet service to return empty list of pets
    mock_pet_service.get_pet_pet_id_get.side_effect = Exception("Not Found")

    user = UserTableObject(name="ToDelete")
    session.add(user)
    session.commit()

    response = client.delete(f"/{user.id}")
    assert response.status_code == 200
    assert response.json() == {"ok": True}

    # Verify user is deleted
    response = client.get(f"/{user.id}")
    assert response.status_code == 404


@pytest.mark.anyio
def test_adopt_pet(mocker, client: TestClient, mock_pet_service, session: Session):
    # Mock the pet service to return a pet
    mock_pet = UserPetResponseObject(
        id=1,
        name="TestPet",
        species="dog",
        age=3,
        mood="happy",
        last_fed=datetime.now(UTC),
        last_interaction=datetime.now(UTC),
    )
    # Configure the mock to return our pet data
    # mocker.patch.object(mock_pet_service, "get_pet_pet_id_get", return_value=mock_pet)
    mocker.patch.object(DefaultApi, "get_pet_pet_id_get", return_value=mock_pet)

    # Create a user
    user = UserTableObject(name="Pet Owner")
    session.add(user)
    session.commit()

    # Adopt a pet
    response = client.post(f"/{user.id}/pets/{mock_pet.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["pets"]) == 1
    assert data["pets"][0]["name"] == "TestPet"

    # Verify the pet association in the database
    pet_association = session.exec(
        select(UserPetTableObject).where(UserPetTableObject.user_id == user.id)
    ).first()
    assert pet_association is not None
    assert pet_association.pet_id == mock_pet.id


@pytest.mark.anyio
def test_adopt_same_pet_twice(mocker, client: TestClient, mock_pet_service, session: Session):
    # Mock the pet service to return a pet
    mock_pet = UserPetResponseObject(
        id=1,
        name="TestPet",
        species="dog",
        age=3,
        mood="happy",
        last_fed=datetime.now(UTC),
        last_interaction=datetime.now(UTC),
    )
    # Configure the mock to return our pet data
    # mocker.patch.object(mock_pet_service, "get_pet_pet_id_get", return_value=mock_pet)
    mocker.patch.object(DefaultApi, "get_pet_pet_id_get", return_value=mock_pet)

    # Create a user
    user = UserTableObject(name="Pet Owner")
    session.add(user)
    session.commit()

    # Adopt the same pet twice
    response1 = client.post(f"/{user.id}/pets/{mock_pet.id}")
    response2 = client.post(f"/{user.id}/pets/{mock_pet.id}")

    assert response1.status_code == 200
    assert response2.status_code == 200

    # Verify only one association exists
    pet_associations = session.exec(
        select(UserPetTableObject).where(UserPetTableObject.user_id == user.id)
    ).all()
    assert len(pet_associations) == 1


@pytest.mark.anyio
def test_list_users_pagination(client: TestClient, mock_pet_service, session: Session):
    # Mock the pet service to return empty list of pets
    mock_pet_service.get_pet_pet_id_get.side_effect = Exception("Not Found")

    # Create 15 test users
    for i in range(15):
        user = UserTableObject(name=f"User{i}")
        session.add(user)
    session.commit()

    # Test default pagination
    response = client.get("/")
    assert response.status_code == 200
    assert len(response.json()) == 15  # Default limit is 100

    # Test with limit
    response = client.get("/?limit=5")
    assert response.status_code == 200
    assert len(response.json()) == 5

    # Test with offset
    response = client.get("/?offset=10")
    assert response.status_code == 200
    assert len(response.json()) == 5  # Should get last 5 users

    # Test with both offset and limit
    response = client.get("/?offset=5&limit=5")
    assert response.status_code == 200
    assert len(response.json()) == 5
    assert response.json()[0]["name"] == "User5"


@pytest.mark.anyio
def test_read_nonexistent_user(client: TestClient):
    response = client.get("/999999")
    assert response.status_code == 404


@pytest.mark.anyio
def test_update_nonexistent_user(client: TestClient):
    response = client.patch(
        "/999999",
        json={"name": "New Name"},
    )
    assert response.status_code == 404


@pytest.mark.anyio
def test_delete_nonexistent_user(client: TestClient):
    response = client.delete("/999999")
    assert response.status_code == 404
