from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


class TeleassistanceEvent(BaseModel):
    case_id: str
    timestamp: datetime

    semantic_type: Literal[
        "oxygen_saturation",
        "heart_rate",
        "fall_detected",
        "technical_alarm",
        "functional_status_change"
    ]

    category: Literal[
        "physiological_observation",
        "assistential_alert",
        "technical_event",
        "functional_status"
    ]

    observed_value: Optional[float] = None
    unit: Optional[str] = None

    severity: Literal[
        "low",
        "medium",
        "high"
    ]

    source: str
    description: str