import asyncio
from typing import Annotated
from fastapi import Depends
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import modular_monolith_api
    from modular_monolith_api.api.default_api import DefaultApi
    from modular_monolith_api.configuration import Configuration
    from modular_monolith_api.api_client import ApiClient
    from .models import PetResponseObject as PetResponseObject
else:
    try:
        import modular_monolith_api
        from modular_monolith_api.api.default_api import DefaultApi
        from modular_monolith_api.configuration import Configuration
        from modular_monolith_api.api_client import ApiClient
        from .models import PetResponseObject as PetResponseObject
    except ImportError:
        from unittest import mock

        modular_monolith_api = mock.Mock()
        DefaultApi = mock.Mock()
        Configuration = mock.Mock()
        ApiClient = mock.Mock()
        PetResponseObject = mock.Mock()


async def getApiClient():
    # depends doesn't call from an event loop context?
    api_instance = DefaultApi(api_client)
    return api_instance


ApiClientDep = Annotated[DefaultApi, Depends(getApiClient)]


# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = Configuration(host="http://localhost:8000")

api_client = None
try:  # ew
    asyncio.get_running_loop()
    # if executed via uvicorn, we get an event loop otherwise not, need better solution
    api_client = ApiClient(configuration)  # needs event loop
except RuntimeError:
    api_client = None
