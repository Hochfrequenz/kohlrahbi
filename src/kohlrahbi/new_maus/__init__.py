"""
models are the data classes used to store information from e.g. ahbs.
This module contains methods available to all methods in the package.
"""


def _check_that_string_is_not_whitespace_or_empty(value: str) -> str:
    """
    Check that string value is not empty or consists only of whitespace.
    """
    if not value:
        raise ValueError("The string must not be None or empty")
    if len(value.strip()) == 0:
        raise ValueError(f"The string must not consist only of whitespace: '{value}'")
    return value
