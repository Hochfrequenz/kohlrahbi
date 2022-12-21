from docx.shared import Length
from attr import define, field


@define(auto_attribs=True, kw_only=True)
class BodyCellParagraph:
    text: str = field()
    tabstop_positions: list[Length]
    left_indent_length: Length

    @text.validator
    def _check_text(self, attribute, value):
        """
        This validator checks if the amount of tabstop characters `\t` is equal to the amount of tabstop positions
        """
        if value.count("\t") != len(self.tabstop_positions):
            raise ValueError("The amount of tabs in the text attribute must match the amount of tabstop positions")
