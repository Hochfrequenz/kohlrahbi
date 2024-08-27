import json
from typing import TypeVar

from deepdiff import DeepDiff
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def assert_serialization_roundtrip(serializable_object: T, expected_json_dict: dict) -> T:
    """
    Serializes the serializable_object,
    asserts, that the result is equal to the expected_json_dict
    then deserializes it again and asserts on equality with the original serializable_object

    :returns the deserialized_object
    """
    json_string = serializable_object.model_dump_json(exclude_unset=True)
    assert json_string is not None

    expected_object = serializable_object.__class__.model_validate(expected_json_dict)

    serializable_object_dict = serializable_object.model_dump(exclude_unset=True, exclude_defaults=True, mode="json")
    expected_object_dict = expected_object.model_dump(exclude_unset=True, exclude_defaults=True, mode="json")

    diff = DeepDiff(serializable_object_dict, expected_object_dict)

    assert serializable_object_dict == expected_object_dict

    deserialized_object = serializable_object.model_validate_json(json_string)
    assert isinstance(deserialized_object, type(serializable_object))
    assert deserialized_object == serializable_object
    return deserialized_object
