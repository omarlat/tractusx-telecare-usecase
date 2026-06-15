from datetime import datetime

from pydantic import BaseModel


class DerivedAsset(BaseModel):

    case_id: str

    risk_level: str

    priority: int

    summary: str

    generated_at: datetime

    source: str