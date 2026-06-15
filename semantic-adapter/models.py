from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


class FunctionalEvent(BaseModel):

    case_id: str

    timestamp: datetime

    semantic_type: str

    category: str

    observed_value: Optional[float] = None

    unit: Optional[str] = None

    severity: Literal[
        "low",
        "medium",
        "high"
    ]

    source: str

    description: str


class SemanticEvent(FunctionalEvent):

    aspect: dict

    common_case_aspect: dict

    semantic_context: str

    semantic_version: str

    validation_status: str

    validation_errors: list[str] = []