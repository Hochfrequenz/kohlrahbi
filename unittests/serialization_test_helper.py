"""

"""

from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def assert_serialization_roundtrip(serializable_object: T) -> T:
    """
    Perform a serialization roundtrip and check that the input object is the same after serialization and deserialization.

    :returns the deserialized_object
    """
    json_string = serializable_object.model_dump_json()
    assert json_string is not None

    deserialized_object = serializable_object.model_validate_json(json_data=json_string)

    assert isinstance(deserialized_object, type(serializable_object))

    assert deserialized_object == serializable_object
    return deserialized_object
