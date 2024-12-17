# type: ignore
try:
    from modular_monolith_api.models.pet_response_object import PetResponseObject
except ImportError:
    # Bad!
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        pass
    from pydantic import BaseModel

    class PetResponseObject(BaseModel): ...

    # PetResponseObject = Mock()
