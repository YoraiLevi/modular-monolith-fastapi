# type: ignore
import asyncio

try:
    import modular_monolith_api
    from modular_monolith_api.api.default_api import DefaultApi
except ImportError:
    # Bad!
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        pass
    from unittest.mock import Mock

    modular_monolith_api = Mock()
    DefaultApi = Mock()

from .models import PetResponseObject as PetResponseObject

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = modular_monolith_api.Configuration(host="http://localhost:8000")

api_client = None
try:  # ew
    asyncio.get_event_loop()
    # if executed via uvicorn, we get an event loop otherwise not, need better solution
    api_client = modular_monolith_api.ApiClient(configuration)  # needs event loop
except RuntimeError:
    from unittest.mock import Mock

    api_client = Mock()


def getApiClient():
    # depends doesn't call from an event loop context?
    api_instance = modular_monolith_api.DefaultApi(api_client)
    return api_instance
