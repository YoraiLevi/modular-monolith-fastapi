from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pet_service_api.models.pet_response_object import PetResponseObject
else:
    try:
        from pet_service_api.models.pet_response_object import PetResponseObject
    except ImportError:
        from pydantic import BaseModel

        class PetResponseObject(BaseModel): ...
