# pylint:disable=too-few-public-methods
"""
EDIFACT components are data structures on different hierarchical levels inside an EDIFACT message.
Components contain not only EDIFACT composits but also segments and segment groups.
"""
import re
from abc import ABC
from enum import Enum
from typing import Callable, Dict, Iterable, List, Mapping, Optional

import attrs
from marshmallow import Schema, fields, post_dump, post_load, pre_dump, pre_load
from marshmallow.fields import Enum as MarshmallowEnum
from pydantic import BaseModel, Field, StringConstraints, field_validator
from typing_extensions import Annotated

from kohlrahbi.new_maus import _check_that_string_is_not_whitespace_or_empty


class DataElementDataType(str, Enum):
    """
    The Data Element Data Type describes with which kind of data element we're dealing with in a data element.
    This information is set but not used anywhere inside MAUS directly but more of a "service" to downstream code.
    """

    TEXT = "TEXT"  #: plain text, e.g. a name
    DATETIME = "DATETIME"  #: a datetime string, usually as RFC3339
    VALUE_POOL = "VALUE_POOL"  #: the user can choose between different possible values


def derive_data_type_from_segment_code(segment_code: str) -> Optional[DataElementDataType]:
    """
    derives the expected data type from the segment code, e.g. `DATETIME` for DTM segments
    :return: The DataType if it can be derived without any doubt, None otherwise
    """
    if segment_code in {"DTM"}:
        return DataElementDataType.DATETIME
    return None


class DataElement(BaseModel, ABC):
    """
    A data element holds specific kinds of data. It is defined in EDIFACT.
    At least for the German energy market communication any data element has a 4 digit key.
    For example in UTILMD the data element that holds the 13 digit market partner ID is data element '3039'
    """

    discriminator: Optional[str] = Field(
        None,
        description="The discriminator uniquely identifies the data element. The discriminator is None if the data element was not found in the MIG.",
    )
    data_element_id: Annotated[str, StringConstraints(strip_whitespace=True, to_upper=True, pattern=r"^\d{4}$")] = (
        Field(
            ...,
            description="The ID of the data element (e.g. '0062') for the Nachrichten-Referenznummer",
        )
    )
    entered_input: Optional[str] = Field(
        None,
        description=(
            "If the message which is evaluated contains data for this data element,"
            "this is set to a value which is not None."
            "The field can either carry a free text or an element from a value pool (depending on the value_type)"
        ),
    )
    value_type: Optional[DataElementDataType] = Field(
        None,
        description=(
            "The value_type allows to describe which type of data we're expecting to be used within this data element."
            "The value_type does not discriminate the type of the data element itself."
        ),
    )

    @field_validator("discriminator", "entered_input", mode="before")
    @classmethod
    def check_optional_fields(cls, v):
        if v is not None:
            _check_that_string_is_not_whitespace_or_empty(v)
        return v

    @field_validator("data_element_id")
    @classmethod
    def check_data_element_id(cls, v):
        if not v or not re.match(r"^\d{4}$", v):
            raise ValueError("data_element_id must be a 4 digit number")
        return v


class DataElementSchema(Schema):
    """
    A Schema to (de-)serialize DataElements
    """

    discriminator = fields.String(required=False, allow_none=True)
    data_element_id = fields.String(required=True)
    entered_input = fields.String(required=False, load_default=None)
    value_type = MarshmallowEnum(DataElementDataType, required=False)

    # pylint:disable= unused-argument
    @post_dump
    def _remove_null_entered_input(self, data: dict, **kwargs) -> dict:  # type:ignore[no-untyped-def,type-arg]
        if "entered_input" in data and data["entered_input"] is None:
            del data["entered_input"]
        return data


class DataElementFreeText(DataElement):
    """
    A DataElementFreeText is a data element that allows entering arbitrary data.
    This is the main difference to the :class:`DataElementValuePool` which has a finite set of allowed values attached.
    """

    value_type: Optional[DataElementDataType] = Field(
        default=DataElementDataType.TEXT,
        description=(
            "The value_type allows to describe which type of data we're expecting to be used within this data element."
            "The value_type does not discriminate the type of the data element itself."
        ),
    )
    ahb_expression: str = Field(
        ..., description="Any freetext data element has an ahb expression attached. Could be 'X' but also 'M [13]'"
    )

    @field_validator("value_type", mode="before")
    @classmethod
    def validate_value_type(cls, v):
        if v is not None and not isinstance(v, DataElementDataType):
            raise ValueError("value_type must be an instance of DataElementDataType")
        return v

    @field_validator("ahb_expression")
    @classmethod
    def validate_ahb_expression(cls, v):
        if not isinstance(v, str) or not v.strip():
            raise ValueError("ahb_expression must be a non-empty string")
        return v


class DataElementFreeTextSchema(DataElementSchema):
    """
    A Schema to serialize DataElementFreeTexts
    """

    ahb_expression = fields.String(allow_none=True, required=True)

    # pylint:disable=unused-argument
    @post_load
    def deserialize(self, data, **kwargs) -> DataElementFreeText:  # type:ignore[no-untyped-def]
        """
        Converts the barely typed data dictionary into an actual :class:`.DataElementFreeText`
        """
        return DataElementFreeText(**data)


#: a pattern that matches most of the qualifiers we find in the AHBs
_simple_edifact_qualifier_pattern = re.compile(r"^([A-Z\d]+)|(\d+\.\d+[a-z])$")

#: a pattern that matches the GABi qualifiers: They contain with "-" and lower case "i"/"o"/"n"
gabi_edifact_qualifier_pattern = re.compile(r"^(?!MP-ID)(GABi)?[A-Z\d\-]+(RLM(o|m)T)?$")


def _check_is_edifact_qualifier(value: str) -> str:
    """
    Checks that the given attribute is a valid EDIFACT qualifier.
    Raises a ValueError if not.
    """
    _check_that_string_is_not_whitespace_or_empty(value)
    simple_match = _simple_edifact_qualifier_pattern.match(value)
    if simple_match is not None:
        return value
    gabi_match = gabi_edifact_qualifier_pattern.match(value)
    if gabi_match is not None:
        return value
    raise ValueError(f"The qualifier '{value}' is invalid")


class ValuePoolEntry(BaseModel):
    """
    A value pool entry contains the EDIFACT qualifier, a meaning (German text) and an ahb expression.
    A value pool consists of 1 to n ValuePoolEntries.
    The data element 3055 in UTILMD is a good example for a value pool.
    It is used in the segments NAD+MS and NAD+MR. Its ValuePoolEntries are:
    - (key: "9", meaning: "GS1", ahb_expression: "X")
    - (key: "293", meaning: "DE, BDEW", ahb_expression: "X")
    - (key: "332", meaning: "DE, DVGW", ahb_expression: "X")
    """

    #: the qualifier in edifact, might be e.g. "E01", "D", "9", "1.1a", "G_0057"
    qualifier: str = Field(..., description="The qualifier in EDIFACT")
    meaning: str = Field(
        ...,
        description="The meaning as it is written in the AHB,"
        "e.g. 'Einzug', 'Entwurfs-Version', 'GS1', 'Codeliste Gas G_0057'",
    )
    ahb_expression: str = Field(
        ...,
        description="The AHB expression, in most cases this is a simple 'X'; it must not be empty",
    )

    @field_validator("qualifier")
    @classmethod
    def validate_qualifier(cls, v):
        return _check_is_edifact_qualifier(v)

    @field_validator("meaning", "ahb_expression")
    @classmethod
    def validate_non_empty_string(cls, v):
        return _check_that_string_is_not_whitespace_or_empty(v)


class ValuePoolEntrySchema(Schema):
    """
    A Schema to serialize ValuePoolEntries
    """

    # this looks like a plain Dict[str,str] but we prefer typed access over loose string key value pairs
    qualifier = fields.String(required=True)
    meaning = fields.String(required=True)
    ahb_expression = fields.String(required=True)

    # pylint:disable=unused-argument
    @post_load
    def deserialize(self, data, **kwargs) -> ValuePoolEntry:  # type:ignore[no-untyped-def]
        """
        Converts the barely typed data dictionary into an actual :class:`.ValuePoolEntry`
        """
        return ValuePoolEntry(**data)


class DataElementValuePool(DataElement):
    """
    A DataElementValuePool is a data element with a finite set of allowed values.
    These allowed values are referred to as keys of the "value pool".
    The value pool is defined both on MIG level and AHB level
    The set of values allowed according to the AHB is always a subset of the values allowed according to the MIG.
    """

    value_type: Optional[DataElementDataType] = Field(
        default=DataElementDataType.VALUE_POOL, description="Type of the value, if known"
    )
    value_pool: List[ValuePoolEntry] = Field(
        ..., description="The value pool contains at least one value :class:`.ValuePoolEntry`"
    )

    @field_validator("value_type", mode="before")
    @classmethod
    def validate_value_type(cls, v):
        if v is not None and not isinstance(v, DataElementDataType):
            raise ValueError("value_type must be an instance of DataElementDataType")
        return v

    @field_validator("value_pool")
    @classmethod
    def validate_value_pool(cls, v):
        if not isinstance(v, list) or not all(isinstance(i, ValuePoolEntry) for i in v):
            raise ValueError("value_pool must be a list of ValuePoolEntry instances")
        return v

    def replace_value_pool(
        self,
        edifact_to_domain_mapping: Mapping[str, str],
        meaning_qualifier_merger: Optional[Callable[[str, str], str]] = None,
    ) -> None:
        """
        If your data model comes from another domain than edifact the value pool from the AHBs, you can, in general, not
        use the same keys. Think e.g. of the Transaktionsgrund in UTILMD. In EDIFACT you might have the values:
        Edifact Domain:
        - E01 = Einzug/Auszug
        - E03 = Wechsel
        - Z33 = Auszug/Stilllegung
        ...
        But if, in your application, you're modelling these values with other values (think e.g. of readable enums):
        Application Domain:
        - EINZUG = Einzug/Auszug
        - WECHSEL = Wechsel
        - STILLLEGUNG = Auszug/Stilllegung
        ...
        You need to transform the value pool from edifact to something that matches the domain from your application.
        To do so, provide this method with an edifact_to_domain_mapping:
        {"E01": "EINZUG","E02": "WECHSEL","E03": "STILLLEGUNG"}
        where each entry represents the mapping of an edifact qualifier to your application domain.

        This method replaces the keys of the ValuePoolEntries if they are found in the mapping.
        By doing so, it allows transforming checks against value pools from the edifact to your application domain.
        This problem does not occur for free text data elements.

        Provide an optional meaning_qualifier_merger that allows you to 'store' the old qualifier in the meaning.
        This is an _unstructured_ way to save the information that is lost with the replacement.
        """
        existing_value_pool_entries: Dict[str, ValuePoolEntry] = {x.qualifier: x for x in self.value_pool}
        for existing_value_pool_qualifier, value_pool_entry in existing_value_pool_entries.items():
            if existing_value_pool_qualifier in edifact_to_domain_mapping:
                if meaning_qualifier_merger is not None:
                    value_pool_entry.meaning = meaning_qualifier_merger(
                        value_pool_entry.meaning, existing_value_pool_qualifier
                    )
                value_pool_entry.qualifier = edifact_to_domain_mapping[existing_value_pool_qualifier]

    def has_value_pool_which_is_subset_of(self, entries: Iterable[str]) -> bool:
        """
        returns true iff all qualifiers from the data elements value pool are found in entries
        """
        return all(x.qualifier in entries for x in self.value_pool)


class DataElementValuePoolSchema(DataElementSchema):
    """
    A Schema to serialize DataElementValuePool
    """

    value_pool = fields.List(fields.Nested(ValuePoolEntrySchema), required=True)

    # pylint:disable=unused-argument
    @post_load
    def deserialize(self, data, **kwargs) -> DataElementValuePool:  # type:ignore[no-untyped-def]
        """
        Converts the barely typed data dictionary into an actual :class:`.DataElementValuePool`
        """
        return DataElementValuePool(**data)


class _FreeTextOrValuePool:
    """
    A class that is easily serializable as dictionary and allows us to _not_ use the marshmallow-union package.
    """

    def __init__(
        self, free_text: Optional[DataElementFreeText] = None, value_pool: Optional[DataElementValuePool] = None
    ):
        self.free_text = free_text
        self.value_pool = value_pool

    free_text: Optional[DataElementFreeText] = attrs.field(
        validator=attrs.validators.optional(attrs.validators.instance_of(DataElementFreeText))
    )
    value_pool: Optional[DataElementValuePool] = attrs.field(
        validator=attrs.validators.optional(attrs.validators.instance_of(DataElementValuePool))
    )


class _FreeTextOrValuePoolSchema(Schema):
    """
    A schema that represents data of the kind Union[DataElementFreeText,DataElementValuePool]
    There is a python package for that: https://github.com/adamboche/python-marshmallow-union
    but is only has 15 stars; not sure if it's worth the dependency
    """

    # disable unnecessary lambda warning because of circular imports
    free_text = fields.Nested("DataElementFreeTextSchema", allow_none=True, required=False)
    value_pool = fields.Nested("DataElementValuePoolSchema", required=False, allow_none=True)
    # see https://github.com/fuhrysteve/marshmallow-jsonschema/issues/164

    # pylint:disable= unused-argument
    @post_load
    def deserialize(self, data, **kwargs) -> DataElement:  # type:ignore[no-untyped-def]
        """
        select the correct part of the data to deserialize
        """
        if "free_text" in data and data["free_text"]:
            return data["free_text"]  # type:ignore[no-any-return]
        if "value_pool" in data and data["value_pool"]:
            return data["value_pool"]  # type:ignore[no-any-return]
        return data  # type:ignore[no-any-return]

    # pylint:disable= unused-argument
    @post_dump
    def post_dump_helper(self, data, **kwargs) -> dict:  # type:ignore[no-untyped-def, type-arg]
        """
        truncate the part _FreeTextOrValuePool that is not needed
        """
        if "value_pool" in data and data["value_pool"]:
            return data["value_pool"]  # type:ignore[no-any-return]
        if "free_text" in data and data["free_text"]:
            return data["free_text"]  # type:ignore[no-any-return]
        raise NotImplementedError(f"Data {data} is not implemented for JSON serialization")

    # pylint:disable= unused-argument
    @pre_load
    def pre_load_helper(self, data, **kwargs) -> dict:  # type:ignore[no-untyped-def, type-arg]
        """
        Put the untyped data into a structure that is deserializable as _FreeTextOrValuePool
        """
        if "value_pool" in data:
            return {
                "free_text": None,
                "value_pool": data,
            }
        if "entered_input" in data:
            return {
                "free_text": data,
                "value_pool": None,
            }
        # entered_input may be None and not have been dumped
        return {"free_text": data, "value_pool": None}

    # pylint:disable= unused-argument
    @pre_dump
    def prepare_for_serialization(self, data, **kwargs) -> _FreeTextOrValuePool:  # type:ignore[no-untyped-def]
        """
        Detect if data are FreeText or ValuePool data elements
        """
        if isinstance(data, DataElementValuePool):
            return _FreeTextOrValuePool(free_text=None, value_pool=data)
        if isinstance(data, DataElementFreeText):
            return _FreeTextOrValuePool(free_text=data, value_pool=None)
        raise NotImplementedError(f"Data type of {data} is not implemented for JSON serialization")


class SegmentLevel(BaseModel, ABC):
    """
    SegmentLevel describes @annika: what does it describe?
    """

    discriminator: str  # no validator here, because it might be None on initialization and will be set later (trust me)
    ahb_expression: str = Field(
        ...,
        description="AHB expression",
    )
    ahb_line_index: Optional[int] = Field(
        default=None,
        description="Allows sorting the segments depending on where they occurred in the FlatAnwendungshandbuch. It won't be serialized though.",
    )

    @field_validator("ahb_expression")
    @classmethod
    def validate_ahb_expression(cls, v):
        return _check_that_string_is_not_whitespace_or_empty(v)

    @field_validator("ahb_line_index")
    @classmethod
    def validate_ahb_line_index(cls, v):
        if v is not None and not isinstance(v, int):
            raise ValueError("ahb_line_index must be an instance of int")
        return v

    def reset_ahb_line_index(self) -> None:
        """
        sets the ahb_line_index to None.
        This is to allow comparisons regardless of the index
        """
        self.ahb_line_index = None


class SegmentLevelSchema(Schema):
    """
    A Schema to serialize SegmentLevels
    """

    discriminator = fields.String(required=True)
    ahb_expression = fields.String(allow_none=True, required=True)
    # ahb_line =


class Segment(SegmentLevel):
    """
    A Segment contains multiple data elements.
    """

    data_elements: List[DataElement]
    section_name: Optional[str] = Field(
        default=None,
        description="For the MIG matching it might be necessary to know the section in which the data element occured in the AHB. This might be necessary to e.g. distinguish gas and electricity fields which look the same otherwise. See e.g. UTILMD 'Geplante Turnusablesung des MSB (Strom)' vs. 'Geplante Turnusablesung des NB (Gas)'",
    )
    segment_id: Optional[
        Annotated[str, StringConstraints(strip_whitespace=True, to_upper=True, pattern=r"^\d{5}$")]
    ] = Field(
        default=None,
        description=(
            "The 5 digit segment id,"
            "e.g. '00522' for UTILMD Strom SG12, NAD 'Korrespondenzanschrift des Kunden des Lieferanten'"
        ),
    )

    @field_validator("section_name")
    @classmethod
    def validate_section_name(cls, v):
        if v is not None and not isinstance(v, str):
            raise ValueError("section_name must be an instance of str")
        return v

    @field_validator("segment_id")
    @classmethod
    def validate_segment_id(cls, v):
        if v is not None and not isinstance(v, str):
            raise ValueError("segment_id must be an instance of str")
        return v

    def get_all_value_pools(self) -> List[DataElementValuePool]:
        """
        find all value pools in this segment
        :return: a list of all value pools
        """
        return [de for de in self.data_elements if isinstance(de, DataElementValuePool)]


class SegmentSchema(SegmentLevelSchema):
    """
    A Schema to serialize Segments
    """

    data_elements = fields.List(fields.Nested(_FreeTextOrValuePoolSchema))
    section_name = fields.String(required=False)
    segment_id = fields.String(required=False, allow_none=True)

    # pylint:disable=unused-argument
    @post_load
    def deserialize(self, data, **kwargs) -> Segment:  # type:ignore[no-untyped-def]
        """
        Converts the barely typed data dictionary into an actual :class:`.Segment`
        """
        return Segment(**data)


@attrs.define(auto_attribs=True, kw_only=True)
class SegmentGroup(SegmentLevel):
    """
    A segment group that contains segments and nested groups.
    On root level of a message there might be a "virtual" segment group of all segments that formally don't have a group
    This group has the key "root".
    """

    segments: Optional[List[Segment]] = attrs.field(
        validator=attrs.validators.optional(
            attrs.validators.deep_iterable(
                member_validator=attrs.validators.instance_of(Segment),
                iterable_validator=attrs.validators.instance_of(list),
            )
        ),
        default=None,
    )  #: the segments inside this very group
    segment_groups: Optional[List["SegmentGroup"]] = attrs.field(
        default=None
    )  #: groups that are nested into this group

    def reset_ahb_line_index(self) -> None:
        self.ahb_line_index = None
        if self.segment_groups:
            for segment_group in self.segment_groups:
                segment_group.reset_ahb_line_index()
        if self.segments:
            for segment in self.segments:
                segment.reset_ahb_line_index()

    def find_segments(self, predicate: Callable[[Segment], bool], search_recursively: bool = True) -> List[Segment]:
        """
        Search for a segment that matches the predicate (in this group and subgroups if 'search_recursively' is set),
        Return results, if found. Return empty list otherwise.
        """
        result: List[Segment] = []
        if self.segments is not None:
            for segment in self.segments:
                if predicate(segment):
                    result.append(segment)
        if search_recursively and self.segment_groups is not None:
            for sub_group in self.segment_groups:
                sub_result = sub_group.find_segments(predicate, search_recursively)
                result += sub_result
        return result

    def get_all_value_pools(self) -> List[DataElementValuePool]:
        """
        recursively find all value pools in this segmentgroup
        :return: a list of all value pools
        """
        result: List[DataElementValuePool] = []
        for segment in self.find_segments(lambda _: True):
            result += segment.get_all_value_pools()
        return result


class SegmentGroupSchema(SegmentLevelSchema):
    """
    A Schema to serialize SegmentGroups.
    """

    segments = fields.List(fields.Nested(SegmentSchema), load_default=None, required=False)
    segment_groups = fields.List(
        fields.Nested("SegmentGroupSchema"),
        # see https://github.com/fuhrysteve/marshmallow-jsonschema/issues/164
        load_default=None,
        required=False,
    )

    # pylint:disable=unused-argument
    @post_load
    def deserialize(self, data, **kwargs) -> SegmentGroup:  # type:ignore[no-untyped-def]
        """
        Converts the barely typed data dictionary into an actual :class:`.SegmentGroup`
        """
        return SegmentGroup(**data)


@attrs.define(auto_attribs=True, kw_only=True)
class EdifactStackLevel:
    """
    The EDIFACT stack level describes the hierarchy level of information inside an EDIFACT message.
    """

    #: the name of the level, e.g. 'Dokument' or 'Nachricht' or 'Meldepunkt'
    name: str = attrs.field(validator=attrs.validators.instance_of(str))
    #: describes if this level is groupable / if there are multiple instances of this level within the same message
    is_groupable: bool = attrs.field(validator=attrs.validators.instance_of(bool))
    #: the index if present (e.g. 0)
    index: Optional[int] = attrs.field(
        default=None, validator=attrs.validators.optional(attrs.validators.instance_of(int))
    )


#: a pattern that matches parts of the json path: https://regex101.com/r/iQzdXK/1
_level_pattern = re.compile(r"\[\"(?P<level_name>[^\[\]]+?)\"\](?:\[(?P<index>\d+)\])?")


@attrs.define(auto_attribs=True, kw_only=True)
class EdifactStack:
    """
    The EdifactStack describes where inside an EDIFACT message data are found.
    The stack is independent of the actual implementation used to create the EDIFACT (be it XML, JSON whatever).
    """

    #: levels describe the nesting inside an edifact message
    levels: List[EdifactStackLevel] = attrs.field(
        validator=attrs.validators.deep_iterable(
            member_validator=attrs.validators.instance_of(EdifactStackLevel),
            iterable_validator=attrs.validators.instance_of(list),
        )
    )

    @staticmethod
    def from_json_path(json_path: str) -> "EdifactStack":
        """
        reads a json path as it is created by "to_json_path" and returns the corresponding edifact stack
        """
        levels: List[EdifactStackLevel] = []
        for level_match in _level_pattern.finditer(json_path):
            level = EdifactStackLevel(name=level_match["level_name"], is_groupable=level_match["index"] is not None)
            if level.is_groupable:
                level.index = int(level_match["index"])
            levels.append(level)
        return EdifactStack(levels=levels)

    def is_sub_stack_of(self, other: "EdifactStack") -> bool:
        """
        Returns true iff this (self) stack is a sub stack of the other provided stack.
        ([Foo][0][Bar]).is_sub_stack_of([Foo][0]) is true.
        """
        if len(other.levels) > len(self.levels):
            # self cannot be a sub path of other if other is "deeper"
            return False
        for level_self, level_other in zip(other.levels, self.levels):  # , strict=False):  # type:ignore[call-overload]
            # strict is False because it's ok if we stop the iteration if self.levels is "exhausted"; explicit is better
            # the type-ignore for the strict=False is necessary for Python<3.10
            if level_self != level_other:
                return False
        # the iteration stopped meaning that for all levels that both other and self share, they are identical.
        # That's the definition of a sub stack. It also means that any stack is a sub stack of itself.
        return True

    def is_parent_of(self, other: "EdifactStack") -> bool:
        """
        Returns true iff this other stack is a sub stack of self.
        """
        return other.is_sub_stack_of(self)

    def to_json_path(self) -> str:
        """
        Transforms this instance into a JSON Path.
        """
        result: str = "$"
        # https://stackoverflow.com/questions/47972143/using-attr-with-pylint
        # pylint: disable=not-an-iterable
        for level in self.levels:
            result += '["' + level.name + '"]'
            if level.index is not None:
                result += f"[{level.index}]"
            elif level.is_groupable:
                result += "[0]"
        return result
