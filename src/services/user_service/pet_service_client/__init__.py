from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pet_service_api
    from pet_service_api.api.default_api import DefaultApi
    from pet_service_api.configuration import Configuration
    from pet_service_api.api_client import ApiClient
    from .models import PetResponseObject as PetResponseObject
else:
    try:
        import pet_service_api
        from pet_service_api.api.default_api import DefaultApi
        from pet_service_api.configuration import Configuration
        from pet_service_api.api_client import ApiClient
        from .models import PetResponseObject as PetResponseObject
    except ImportError:
        from unittest import mock

        pet_service_api = mock.Mock()
        DefaultApi = mock.Mock()
        Configuration = mock.Mock()
        ApiClient = mock.Mock()
        PetResponseObject = mock.Mock()


def create_pet_service_api_client(host: str) -> ApiClient:
    # See configuration.py for a list of all supported configuration parameters.
    configuration = Configuration(host=host)
    return ApiClient(configuration)


def create_pet_service_default_api_client(api_client: ApiClient):
    return DefaultApi(api_client)
