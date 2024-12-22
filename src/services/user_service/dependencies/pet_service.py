from typing import Annotated
from fastapi import Depends

from ..pet_service_client import DefaultApi, ApiClient, create_pet_service_default_api_client


async def get_pet_service_api_client() -> ApiClient:
    raise NotImplementedError("get_pet_service_api_client is not implemented")


petServiceApiClientDep = Annotated[ApiClient, Depends(get_pet_service_api_client)]


async def get_pet_service_default_api_client(api_client: petServiceApiClientDep):
    return create_pet_service_default_api_client(api_client)


petServiceDefaultApiClientDep = Annotated[DefaultApi, Depends(get_pet_service_default_api_client)]
