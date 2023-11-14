"""
This module contains the UnfoldedAhbLine class.
"""

from attrs import define


# pylint: disable=too-few-public-methods
@define(auto_attribs=True, kw_only=True)
class UnfoldedAhbLine:
    """
    This class represents one unfolded line of the AHB.
    Unfolded means that we separate segment_name and segment_gruppe as well as code and qualifier

    Example:

    AhbLine(
        guid=None,
        section_name="Ansprechpartner",
        segment_group_key="SG3",
        segment_code=None,
        data_element=None,
        value_pool_entry=None,
        name=None,
        ahb_expression="Kann",
        index=0,
    )

    AhbLine(
        guid=None,
        section_name="Ansprechpartner",
        segment_group_key="SG3",
        segment_code=None,
        data_element=None,
        value_pool_entry=None,
        name=None,
        ahb_expression="Kann",
        index=1,
    )

    AhbLine(
        guid=None,
        section_name="Ansprechpartner",
        segment_group_key="SG3",
        segment_code="CTA",
        data_element=None,
        value_pool_entry=None,
        name=None,
        ahb_expression="Muss",
        index=2,
    )

    AhbLine(
        guid=None,
        section_name="Ansprechpartner",
        segment_group_key="SG3",
        segment_code="CTA",
        data_element="3139",
        value_pool_entry="IC",
        name="Informationskontakt",
        ahb_expression="X",
        index=3,
    )

    AhbLine(
        guid=None,
        section_name="Ansprechpartner",
        segment_group_key="SG3",
        segment_code="CTA",
        data_element="3412",
        value_pool_entry=None,
        name="Name vom Ansprechpartner",
        ahb_expression="X",
        index=4,
    )

    """

    # pylint: disable=fixme
    # TODO: add class variable which increments the index with each created instance
    index: int
    segment_name: str  # Ansprechpartner
    segment_gruppe: str | None  # SG3
    segment: str | None  # CTA
    datenelement: str | None  # 3055
    code: str | None  # IC
    qualifier: str | None  # Name vom Ansprechpartner
    beschreibung: str | None  # Informationskontakt
    bedingung_ausdruck: str | None  # Muss / X / X [1P0..1]
    bedingung: str | None  # [492] Wenn MP-ID in NAD+MR (Nachrichtenempfänger) aus Sparte Strom
