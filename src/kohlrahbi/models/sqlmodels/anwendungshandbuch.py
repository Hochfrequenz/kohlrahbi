"""model classes copy-pasted from kohlrahbi"""

# pylint: disable=too-few-public-methods

try:
    from sqlalchemy import UniqueConstraint
    from sqlmodel import Field, Relationship, SQLModel
except ImportError as import_error:
    import_error.msg += "; Did you install kohlrahbi[sqlmodels]?"
    # sqlmodel is only an optional dependency when kohlrahbi is used to fill a database
    raise
import uuid
from typing import Optional
from uuid import UUID

from efoli import EdifactFormat, EdifactFormatVersion

# the models here do NOT inherit from the original models, because I didn't manage to fix the issue that arise:
# https://github.com/Hochfrequenz/kohlrahbi/issues/556
# <frozen abc>:106: in __new__
#     ???
# E   TypeError: FlatAnwendungshandbuch.__init_subclass__() takes no keyword arguments
#
# or
#
# ..\.tox\dev\Lib\site-packages\sqlmodel\main.py:697: in get_sqlalchemy_type
#     raise ValueError(f"{type_} has no matching SQLAlchemy type")
# E   ValueError: <class 'kohlrahbi.models.anwendungshandbuch.AhbMetaInformation'> has no matching SQLAlchemy type


class FlatAnwendungshandbuch(SQLModel, table=True):  # team
    """
    A flat Anwendungshandbuch (AHB) models an Anwendungshandbuch as combination of some meta data and an ordered list
    of `.class:`.FlatAhbLine s. Basically a flat Anwendungshandbuch is the result of a simple scraping approach.
    You can create instances of this class without knowing anything about the "under the hood" structure of AHBs or MIGs
    """

    id: UUID = Field(primary_key=True, default_factory=uuid.uuid4, description="optional key")
    meta: Optional["AhbMetaInformation"] = Relationship(back_populates="flatanwendungshandbuch")
    lines: list["AhbLine"] = Relationship(back_populates="flatanwendungshandbuch")


class AhbLine(SQLModel, table=True):
    """
    An AhbLine is a single line inside the machine-readable, flat AHB.
    """

    __table_args__ = (UniqueConstraint("ahb_id", "position_inside_ahb", name="IX_position_once_per_ahb"),)
    id: UUID = Field(primary_key=True, default_factory=uuid.uuid4, description="optional key")
    # yes, it's actually that bad already

    position_inside_ahb: int = Field(index=True)
    ahb_id: UUID | None = Field(default=None, foreign_key="flatanwendungshandbuch.id")
    flatanwendungshandbuch: FlatAnwendungshandbuch | None = Relationship(back_populates="lines")

    # fields copy-pasted from original model:
    guid: Optional[UUID]
    segment_group_key: Optional[str]
    segment_code: Optional[str]
    data_element: Optional[str]
    segment_id: Optional[str]
    value_pool_entry: Optional[str]
    name: Optional[str]
    ahb_expression: Optional[str]
    conditions: Optional[str]
    section_name: Optional[str]
    index: Optional[int]


class AhbMetaInformation(SQLModel, table=True):
    """
    Meta information about an AHB like e.g. its title, Prüfidentifikator, possible sender and receiver roles
    """

    __table_args__ = (
        UniqueConstraint("pruefidentifikator", "edifact_format_version", name="IX_pruefi_once_per_format_version"),
    )
    id: UUID = Field(primary_key=True, default_factory=uuid.uuid4, description="optional key")
    edifact_format: EdifactFormat = Field(index=True)
    edifact_format_version: EdifactFormatVersion = Field(index=True)
    flatanwendungshandbuch: Optional[FlatAnwendungshandbuch] = Relationship(
        back_populates="meta", sa_relationship_kwargs={"uselist": False}
    )
    ahb_id: UUID | None = Field(default=None, foreign_key="flatanwendungshandbuch.id")

    # copy-pasted fields from original model:
    pruefidentifikator: str
    maus_version: Optional[str]
    description: Optional[str]
    direction: Optional[str]
