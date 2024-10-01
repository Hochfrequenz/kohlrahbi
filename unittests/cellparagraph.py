from typing import Optional

from docx.shared import Length
from pydantic import BaseModel, ConfigDict, Field, model_validator


class CellParagraph(BaseModel):
    """
    This class provides collects the main parameters we use during parsing. Namely they are
    - text: Text in a cell paragraph
    - tabstop_positions: The positions for each tabstop
    - left_indent_length: The position where the text begins in the current paragraph

    In addition there is a validator which checks if the amount of given tabstop positions is equal to the given tabstop positions.
    """

    text: str = Field(...)
    tabstop_positions: Optional[list[Length]] = Field(None)
    left_indent_length: Length = Field(...)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="after")
    def check_text(self):
        """
        If the text contains tabstop characters `\t`, the amount of tab stops must be equal to the amount of tabstop positions.
        """
        if "\t" in self.text:

            if self.tabstop_positions is None:
                raise ValueError("There is a tab in the text but the tabstop positions is None")
            elif self.text.count("\t") != len(self.tabstop_positions):
                raise ValueError("The amount of tabs in the text attribute must match the amount of tabstop positions")
        return self
