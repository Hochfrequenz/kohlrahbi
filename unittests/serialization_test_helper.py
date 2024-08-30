from typing import Any, Dict, List, Tuple, TypeVar

from deepdiff import DeepDiff
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


# Recursive function to compare two dictionaries
def compare_dicts(d1: Dict[str, Any], d2: Dict[str, Any], path: str = "") -> List[Tuple[str, Any, Any]]:
    differences = []
    for key in d1.keys() | d2.keys():  # Union of keys from both dictionaries
        new_path = f"{path}.{key}" if path else key
        if key not in d1:
            differences.append((new_path, None, d2[key]))
        elif key not in d2:
            differences.append((new_path, d1[key], None))
        elif isinstance(d1[key], dict) and isinstance(d2[key], dict):
            differences.extend(compare_dicts(d1[key], d2[key], new_path))
        elif d1[key] != d2[key]:
            differences.append((new_path, d1[key], d2[key]))
    return differences


def compare_pydantic_models(
    model1: BaseModel, model2: BaseModel, path: str = ""
) -> Tuple[List[str], List[Tuple[str, Any, Any]], List[str]]:
    added = []
    removed = []
    changed = []

    model1_fields = set(model1.model_fields.keys())
    model2_fields = set(model2.model_fields.keys())

    for field in model1_fields.union(model2_fields):
        new_path = f"{path}.{field}" if path else field
        if field not in model1_fields:
            added.append(new_path)
        elif field not in model2_fields:
            removed.append(new_path)
        else:
            value1 = getattr(model1, field)
            value2 = getattr(model2, field)

            if isinstance(value1, BaseModel) and isinstance(value2, BaseModel):
                # Recurse into nested models
                a, c, r = compare_pydantic_models(value1, value2, new_path)
                added.extend(a)
                changed.extend(c)
                removed.extend(r)
            elif value1 != value2:
                changed.append((new_path, value1, value2))

    return added, changed, removed


def assert_serialization_roundtrip(serializable_object: T) -> T:
    """
    Perform a serialization roundtrip and check that the input object is the same after serialization and deserialization.

    :returns the deserialized_object
    """
    json_string = serializable_object.model_dump_json()
    assert json_string is not None

    deserialized_object = serializable_object.model_validate_json(json_data=json_string)

    assert isinstance(deserialized_object, type(serializable_object))

    added, changed, removed = compare_pydantic_models(
        deserialized_object.segments[0].data_elements[0], serializable_object.segments[0].data_elements[0]
    )

    assert serializable_object.segments[0].data_elements[0].value_pool is not None
    assert deserialized_object.segments[0].data_elements[0].value_pool is not None

    serializable_object.segments[0].data_elements[0].value_pool == deserialized_object.segments[0].data_elements[
        0
    ].value_pool

    # # Convert Pydantic models to dictionaries
    # dict1 = serializable_object.model_dump()
    # dict2 = deserialized_object.model_dump()

    # # Compare the dictionaries
    # diff = DeepDiff(dict1, dict2, ignore_order=True)

    # # Categorize the differences
    # added = diff.get("dictionary_item_added", {})
    # removed = diff.get("dictionary_item_removed", {})
    # changed = diff.get("values_changed", {})

    # # Output the differences
    # if added:
    #     print("Added entries:")
    #     for key in added:
    #         print(f"{key}: {added[key]}")

    # if removed:
    #     print("\nRemoved entries:")
    #     for key in removed:
    #         print(f"{key}: {removed[key]}")

    # if changed:
    #     print("\nChanged entries:")
    #     for key, value in changed.items():
    #         print(f"{key}: {value['old_value']} -> {value['new_value']}")

    assert deserialized_object == serializable_object
    return deserialized_object
