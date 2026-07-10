from datetime import datetime

from pydantic import BaseModel


# Activo derivado generado por el módulo analítico (Entidad B) a partir
# de los eventos semánticos de un caso. Representa la clasificación de
# riesgo y la prioridad de intervención para ese caso.
class DerivedAsset(BaseModel):

    case_id: str

    # Nivel de riesgo calculado: "high", "medium" o "low"
    risk_level: str

    # Orden de atención: 1 (máxima urgencia) a 3 (seguimiento rutinario)
    priority: int

    summary: str

    generated_at: datetime

    source: str
