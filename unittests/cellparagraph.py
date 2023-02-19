from typing import Optional

from attr import define, field
from docx.shared import Length  # type:ignore[import]


@define(auto_attribs=True, kw_only=True)
class CellParagraph:
    """
    This class provides collects the main parameters we use during parsing. Namely they are
    - text: Text in a cell paragraph
    - tabstop_positions: The postions for each tabstop
    - left_indent_length: The position where the text begins in the current paragraph

    In addition there is a validator which checks if the amount of given tabstop positions is equal to the given tabstop postions.
    """

    text: str = field()
    tabstop_positions: Optional[list[Length]] = field()
    left_indent_length: Length = field()

    @text.validator
    def _check_text(self, attribute, value) -> None:
        """
        If the text contains tabstop characters `\t`, the amount of tab stops must be equal to the amount of tabstop positions.
        """
        if "\t" in value:
            if self.tabstop_positions is None:
                raise ValueError("There is a tab in the text but the tabstop positions is None")
            elif value.count("\t") != len(self.tabstop_positions):
                raise ValueError("The amount of tabs in the text attribute must match the amount of tabstop positions")
