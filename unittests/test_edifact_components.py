import pytest  # type:ignore[import]

from kohlrahbi.models.edifact_components import (
    DataElementDataType,
    DataElementFreeText,
    DataElementValuePool,
    EdifactStack,
    EdifactStackLevel,
    Segment,
    SegmentGroup,
    ValuePoolEntry,
)
from unittests.serialization_test_helper import assert_serialization_roundtrip  # type:ignore[import]


class TestEdifactComponents:
    """
    Tests the behaviour of the Edifact Components
    """

    @pytest.mark.parametrize(
        "free_text",
        [
            pytest.param(
                DataElementFreeText(
                    ahb_expression="Muss [1]",
                    free_text="Hello Maus",
                    discriminator="foo",
                    data_element_id="2222",
                    value_type=DataElementDataType.TEXT,
                )
            ),
        ],
    )
    def test_free_text_serialization_roundtrip(self, free_text: DataElementFreeText):
        assert_serialization_roundtrip(free_text)

    @pytest.mark.parametrize(
        "value_pool",
        [
            pytest.param(
                DataElementValuePool(
                    value_pool=[
                        ValuePoolEntry(qualifier="HELLO", meaning="world", ahb_expression="X"),
                        ValuePoolEntry(qualifier="MAUS", meaning="rocks", ahb_expression="X"),
                    ],
                    discriminator="foo",
                    data_element_id="0022",
                ),
            ),
        ],
    )
    def test_value_pool_serialization_roundtrip(self, value_pool: DataElementValuePool):
        assert_serialization_roundtrip(value_pool)

    @pytest.mark.parametrize(
        "segment",
        [
            pytest.param(
                Segment(
                    ahb_expression="X",
                    section_name="foo",
                    data_elements=[
                        DataElementValuePool(
                            value_type=DataElementDataType.VALUE_POOL,
                            value_pool=[
                                ValuePoolEntry(qualifier="HELLO", meaning="world", ahb_expression="X"),
                                ValuePoolEntry(qualifier="MAUS", meaning="rocks", ahb_expression="X"),
                            ],
                            discriminator="baz",
                            data_element_id="0329",
                        ),
                        DataElementFreeText(
                            value_type=DataElementDataType.TEXT,
                            ahb_expression="Muss [1]",
                            free_text="Hello Maus",
                            discriminator="bar",
                            data_element_id="0330",
                        ),
                    ],
                    discriminator="foo",
                ),
            ),
        ],
    )
    def test_segment_serialization_roundtrip(self, segment: Segment):
        assert_serialization_roundtrip(segment)

    @pytest.mark.parametrize(
        "segment,expected_result_length",
        [
            pytest.param(
                Segment(
                    ahb_expression="X",
                    section_name="foo",
                    data_elements=[
                        DataElementValuePool(
                            value_pool=[
                                ValuePoolEntry(qualifier="HELLO", meaning="world", ahb_expression="X"),
                                ValuePoolEntry(qualifier="MAUS", meaning="rocks", ahb_expression="X"),
                            ],
                            discriminator="baz",
                            data_element_id="0329",
                        ),
                        DataElementFreeText(
                            ahb_expression="Muss [1]",
                            free_text="Hello Maus",
                            discriminator="bar",
                            data_element_id="0330",
                        ),
                    ],
                    discriminator="foo",
                ),
                1,
            )
        ],
    )
    def test_segment_get_value_pools(self, segment: Segment, expected_result_length: int):
        actual = segment.get_all_value_pools()
        assert len(actual) == expected_result_length

    @pytest.mark.parametrize(
        "segment_group",
        [
            pytest.param(
                SegmentGroup(
                    ahb_expression="expr A",
                    discriminator="disc A",
                    segments=[
                        Segment(
                            ahb_expression="expr B",
                            discriminator="disc B",
                            section_name="bar",
                            data_elements=[
                                DataElementValuePool(
                                    value_type=DataElementDataType.VALUE_POOL,
                                    value_pool=[
                                        ValuePoolEntry(qualifier="HELLO", meaning="world", ahb_expression="X"),
                                        ValuePoolEntry(qualifier="MAUS", meaning="rocks", ahb_expression="X"),
                                    ],
                                    discriminator="baz",
                                    data_element_id="3333",
                                ),
                                DataElementFreeText(
                                    value_type=DataElementDataType.TEXT,
                                    ahb_expression="Muss [1]",
                                    free_text="Hello Maus",
                                    discriminator="bar",
                                    data_element_id="4444",
                                ),
                            ],
                        ),
                    ],
                    segment_groups=[
                        SegmentGroup(
                            discriminator="disc C",
                            ahb_expression="expr C",
                            segments=[
                                Segment(
                                    section_name="foo",
                                    ahb_expression="expr Y",
                                    discriminator="disc Y",
                                    data_elements=[],
                                )
                            ],
                            segment_groups=None,
                        ),
                    ],
                ),
            ),
        ],
    )
    def test_segment_group_serialization_roundtrip(self, segment_group: SegmentGroup):
        assert_serialization_roundtrip(segment_group)

    @pytest.mark.parametrize(
        "stack_x, stack_y, x_is_sub_stack_of_y, x_is_parent_of_y",
        [
            pytest.param(EdifactStack(levels=[]), EdifactStack(levels=[]), True, True, id="equality"),
            pytest.param(
                EdifactStack(levels=[EdifactStackLevel(name="x", is_groupable=False)]),
                EdifactStack(levels=[]),
                True,
                False,
                id="any stack is sub stack of root",
            ),
            pytest.param(
                EdifactStack(levels=[]),
                EdifactStack(levels=[EdifactStackLevel(name="x", is_groupable=False)]),
                False,
                True,
                id="other too deep",
            ),
            pytest.param(
                EdifactStack(levels=[EdifactStackLevel(name="x", is_groupable=True)]),
                EdifactStack(levels=[EdifactStackLevel(name="x", is_groupable=False)]),
                False,
                False,
                id="different groubability",
            ),
            pytest.param(
                EdifactStack(levels=[EdifactStackLevel(name="x", is_groupable=True)]),
                EdifactStack(levels=[EdifactStackLevel(name="y", is_groupable=True)]),
                False,
                False,
                id="different name",
            ),
            pytest.param(
                EdifactStack(
                    levels=[
                        EdifactStackLevel(name="a", is_groupable=True),
                        EdifactStackLevel(name="b", is_groupable=True),
                    ]
                ),
                EdifactStack(levels=[EdifactStackLevel(name="a", is_groupable=True)]),
                True,
                False,
                id="yes",
            ),
        ],
    )
    def test_edifact_stack_is_sub_or_parent_of(
        self, stack_x: EdifactStack, stack_y: EdifactStack, x_is_sub_stack_of_y: bool, x_is_parent_of_y: bool
    ):
        assert stack_x.is_sub_stack_of(stack_y) == x_is_sub_stack_of_y
        assert stack_x.is_parent_of(stack_y) == x_is_parent_of_y

    @pytest.mark.parametrize(
        "json_path",
        [
            pytest.param('$["foo"][0]["asd"]["bar"][29]["sss(asd)"][2]'),
            pytest.param('$["asd"][223239102]["Hallo ()asd90e34A)SD=A)D"]["bar"][29]["sss(asd)"][2]'),
        ],
    )
    def test_edifact_stack_to_from_json_path(self, json_path: str):
        stack = EdifactStack.from_json_path(json_path)
        assert stack.to_json_path() == json_path

    def test_segment_group_can_be_instantiated_without_explicitly_defining_sub_groups(self):
        """
        Tests https://github.com/Hochfrequenz/mig_ahb_utility_stack/issues/41
        """
        sg = SegmentGroup(
            discriminator="Foo",
            ahb_expression="Muss [1]",
        )  # must not throw an exception
        assert sg is not None
        assert sg.segment_groups is None
        assert sg.segments is None

    @pytest.mark.parametrize(
        "segment_group, expected_result_length",
        [
            pytest.param(
                SegmentGroup(
                    ahb_expression="expr A",
                    discriminator="disc A",
                    segments=[
                        Segment(
                            ahb_expression="expr B",
                            discriminator="disc B",
                            section_name="bar",
                            data_elements=[
                                DataElementValuePool(
                                    value_pool=[
                                        ValuePoolEntry(qualifier="HELLO", meaning="world", ahb_expression="X"),
                                        ValuePoolEntry(qualifier="MAUS", meaning="rocks", ahb_expression="X"),
                                    ],
                                    discriminator="baz",
                                    data_element_id="3333",
                                ),
                                DataElementFreeText(
                                    ahb_expression="Muss [1]",
                                    free_text="Hello Maus",
                                    discriminator="bar",
                                    data_element_id="4444",
                                ),
                            ],
                        ),
                    ],
                    segment_groups=[
                        SegmentGroup(
                            discriminator="disc C",
                            ahb_expression="expr C",
                            segments=[
                                Segment(
                                    section_name="foo",
                                    ahb_expression="expr Y",
                                    discriminator="disc Y",
                                    data_elements=[
                                        DataElementValuePool(
                                            value_pool=[
                                                ValuePoolEntry(qualifier="HELLO", meaning="world", ahb_expression="X"),
                                                ValuePoolEntry(qualifier="MAUS", meaning="rocks", ahb_expression="X"),
                                            ],
                                            discriminator="baz",
                                            data_element_id="3333",
                                        ),
                                    ],
                                )
                            ],
                            segment_groups=None,
                        ),
                    ],
                ),
                2,
            )
        ],
    )
    def test_segment_group_get_value_pools(self, segment_group: SegmentGroup, expected_result_length: int):
        actual = segment_group.get_all_value_pools()
        assert len(actual) == expected_result_length

    def test_replacing_value_pool_entries(self):
        data_element = DataElementValuePool(
            value_pool=[
                ValuePoolEntry(qualifier="HELLO", meaning="world", ahb_expression="A"),
                ValuePoolEntry(qualifier="MAUS", meaning="rocks", ahb_expression="B"),
                ValuePoolEntry(qualifier="FOO", meaning="bar", ahb_expression="C"),
            ],
            discriminator="foo",
            data_element_id="0022",
        )
        mapping = {"HELLO": "GOODBYE", "MAUS": "KATZE"}
        data_element.replace_value_pool(mapping)
        # the same instance of the data element has been modified. we're not working on a copy.
        assert data_element.value_pool == [
            ValuePoolEntry(qualifier="GOODBYE", meaning="world", ahb_expression="A"),
            ValuePoolEntry(qualifier="KATZE", meaning="rocks", ahb_expression="B"),
            ValuePoolEntry(qualifier="FOO", meaning="bar", ahb_expression="C"),
        ]

    def test_replacing_value_pool_entries_with_merger(self):
        data_element = DataElementValuePool(
            value_pool=[
                ValuePoolEntry(qualifier="HELLO", meaning="world", ahb_expression="A"),
                ValuePoolEntry(qualifier="MAUS", meaning="rocks", ahb_expression="B"),
                ValuePoolEntry(qualifier="FOO", meaning="bar", ahb_expression="C"),
            ],
            discriminator="foo",
            data_element_id="0022",
        )
        mapping = {"HELLO": "GOODBYE", "MAUS": "KATZE"}

        def merge_meaning_and_old_qualifier(meaning: str, old_qualifier: str) -> str:
            # just a dummy function to demonstrate the behaviour
            return meaning + f" ({old_qualifier})"

        data_element.replace_value_pool(mapping, merge_meaning_and_old_qualifier)
        # the same instance of the data element has been modified. we're not working on a copy.
        assert data_element.value_pool == [
            ValuePoolEntry(qualifier="GOODBYE", meaning="world (HELLO)", ahb_expression="A"),
            ValuePoolEntry(qualifier="KATZE", meaning="rocks (MAUS)", ahb_expression="B"),
            ValuePoolEntry(qualifier="FOO", meaning="bar", ahb_expression="C"),  # this hasn't been replaced
        ]

    @pytest.mark.parametrize(
        "candidate,expected",
        [
            pytest.param({"asd"}, False),
            pytest.param({"HELLO"}, False),
            pytest.param({"HELLO", "MAUS", "FOO"}, True),
            pytest.param(["FOO", "MAUS", "HELLO"], True),
        ],
    )
    def test_has_value_pool_which_is_subset_of(self, candidate, expected: bool):
        data_element = DataElementValuePool(
            value_pool=[
                ValuePoolEntry(qualifier="HELLO", meaning="world", ahb_expression="A"),
                ValuePoolEntry(qualifier="MAUS", meaning="rocks", ahb_expression="B"),
                ValuePoolEntry(qualifier="FOO", meaning="bar", ahb_expression="C"),
            ],
            discriminator="foo",
            data_element_id="0022",
        )
        assert data_element.has_value_pool_which_is_subset_of(candidate) == expected
