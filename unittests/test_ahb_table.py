import pytest
import attrs


@attrs.define(auto_attribs=True, kw_only=True)
class TestAhbTable:
    """
    All tests regarding the AhbTable class
    """

    def test_append_ahb_sub_table(self):
        """
        Test appending of an AHB subtable
        """
