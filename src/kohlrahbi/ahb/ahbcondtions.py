import pandas as pd
from maus.edifact import EdifactFormat
from pydantic import BaseModel, ConfigDict


class AhbConditions(BaseModel):
    edifact_format: EdifactFormat = None
    conditions: pd.DataFrame
    model_config = ConfigDict(arbitrary_types_allowed=True)
