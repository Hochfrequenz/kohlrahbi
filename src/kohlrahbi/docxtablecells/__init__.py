"""
This __init__ module collects all cell classes
"""

KNOW_SUFFIXES = ["g", "ung", "gs-", "vall", "n", "m", "t", "rage", "sgrund"]

from .bedinungscell import BedingungCell
from .bodycell import BodyCell
from .edifactstrukturcell import EdifactStrukturCell

__all__ = ["BedingungCell", "BodyCell", "EdifactStrukturCell"]
