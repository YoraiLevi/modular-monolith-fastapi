import pytest
from datetime import datetime, UTC

from ..models import UserPetResponseObject
from ..pet_service_client import getApiClient, DefaultApi


@pytest.fixture
async def api_instance():
    return await getApiClient()


def mock_pet_response(id: int):
    return UserPetResponseObject(
        id=id,
        name="TestPet",
        species="dog",
        age=3,
        mood="happy",
        last_fed=datetime.now(UTC),
        last_interaction=datetime.now(UTC),
    )


@pytest.mark.anyio
async def test_get_pet(mocker, api_instance):
    # Create a mock API instance
    id = 1
    mocker.patch.object(api_instance, "get_pet_pets_pet_id_get", return_value=mock_pet_response(id))

    # Call the method
    response = await api_instance.get_pet_pets_pet_id_get(id)

    # Verify the response
    assert response.id == id
    assert response.name == "TestPet"
    assert response.species == "dog"
    assert response.age == 3
    assert response.mood == "happy"


@pytest.mark.anyio
async def test_get_pet_from_pet_service(mocker):
    # Create a mock API instance
    id = 1
    mocker.patch.object(DefaultApi, "get_pet_pets_pet_id_get", return_value=mock_pet_response(id))

    # Call the method
    response = await (await getApiClient()).get_pet_pets_pet_id_get(id)

    # Verify the response
    assert response.id == id
    assert response.name == "TestPet"
    assert response.species == "dog"
    assert response.age == 3
    assert response.mood == "happy"


@pytest.mark.anyio
async def test_get_pet_not_found(mocker, api_instance):
    # Create a mock API instance
    id = 1
    mocker.patch.object(api_instance, "get_pet_pets_pet_id_get", return_value=None)

    # Call the method
    response = await api_instance.get_pet_pets_pet_id_get(id)

    assert response is None


@pytest.mark.anyio
async def test_get_api_client():
    # Test the getApiClient function
    api_instance = await getApiClient()
    assert isinstance(api_instance, DefaultApi)
