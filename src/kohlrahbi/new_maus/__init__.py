"""
models are the data classes used to store information from e.g. ahbs.
This module contains methods available to all methods in the package.
"""


# pylint: disable=unused-argument
def _check_that_string_is_not_whitespace_or_empty(instance, attribute, value):
    """
    Check that string in the instance attribute value is not empty
    """
    if not value:
        raise ValueError(f"The string {attribute.name} must not be None or empty")
    if len(value.strip()) == 0:
        raise ValueError(f"The string {attribute.name} must not consist only of whitespace: '{value}'")
