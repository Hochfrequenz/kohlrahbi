"""
This module provides the ChangeHistorySubTable class
"""
import attrs
import pandas as pd


@attrs.define(auto_attribs=True, kw_only=True)
class ChangeHistorySubTable:
    """
    This class  contains the change history table.
    """

    table: pd.DataFrame
