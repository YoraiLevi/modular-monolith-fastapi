from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modular_monolith_api.models.pet_response_object import PetResponseObject
else:
    try:
        from modular_monolith_api.models.pet_response_object import PetResponseObject
    except ImportError:
        from pydantic import BaseModel

        class PetResponseObject(BaseModel): ...
