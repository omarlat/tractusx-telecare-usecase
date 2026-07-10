from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


# Unidad atómica de información del sistema de teleasistencia.
# Cada evento representa una observación, alerta o incidencia técnica
# generada por un dispositivo o equipo asistencial.
class TeleassistanceEvent(BaseModel):

    case_id: str

    timestamp: datetime

    # Vocabulario controlado de tipos semánticos.
    # Determina el aspecto funcional que el semantic-adapter asignará al evento.
    semantic_type: Literal[
        "oxygen_saturation",
        "heart_rate",
        "fall_detected",
        "technical_alarm",
        "functional_status_change"
    ]

    # Categoría de agrupación del evento, alineada con las categorías
    # de los aspectos definidos en el semantic-adapter
    category: Literal[
        "physiological_observation",
        "assistential_alert",
        "technical_event",
        "functional_status"
    ]

    # Magnitud observada: presente solo en eventos de tipo fisiológico
    # (oxygen_saturation, heart_rate); None para alertas y cambios de estado
    observed_value: Optional[float] = None
    unit: Optional[str] = None

    severity: Literal[
        "low",
        "medium",
        "high"
    ]

    source: str
    description: str
