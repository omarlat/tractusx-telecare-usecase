from pydantic import BaseModel


class DerivedAsset(BaseModel):

    case_id: str

    risk_level: str

    priority: int

    summary: str