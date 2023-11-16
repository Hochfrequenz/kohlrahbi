"""
This module provides the ChangeHistoryTable class
"""

import attrs
import pandas as pd


@attrs.define(auto_attribs=True, kw_only=True)
class ChangeHistoryTable:
    """
    This class  contains the change history table.
    """

    table: pd.DataFrame
