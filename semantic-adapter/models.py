from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


# Contrato estructural de un evento de teleasistencia,
# usado por validate_structure para validar los eventos recibidos.
class FunctionalEvent(BaseModel):

    case_id: str

    timestamp: datetime

    semantic_type: str

    category: str

    observed_value: Optional[float] = None

    unit: Optional[str] = None

    # Vocabulario controlado de severidad
    severity: Literal[
        "low",
        "medium",
        "high"
    ]

    source: str

    description: str


# Evento enriquecido semánticamente y validado
class SemanticEvent(FunctionalEvent):

    # Aspecto funcional específico resuelto para el evento
    aspect: dict

    # CommonCaseAspect: aspecto común a todo evento (case_id, timestamp, source)
    common_case_aspect: dict

    semantic_context: str

    semantic_version: str

    # "valid" / "invalid", resultado combinado de las validaciones aplicadas
    validation_status: str

    validation_errors: list[str] = []
