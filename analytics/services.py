import os
from datetime import datetime, timezone

import requests

from models import DerivedAsset


# URL del semantic-adapter: el análisis parte de los eventos ya
# enriquecidos semánticamente, no directamente del generator
SEMANTIC_EVENTS_URL = os.environ.get(
    "SEMANTIC_EVENTS_URL",
    "http://localhost:8001/semantic-events"
)


# Obtiene los eventos semánticos llamando directamente a semantic-adapter.
# Solo para pruebas manuales (ver DEV.md); el flujo de la demo usa
# classify_events() con los eventos recibidos vía el espacio de datos.
def analyze_events():

    response = requests.get(
        SEMANTIC_EVENTS_URL
    )

    return classify_events(response.json())


# Agrupa los eventos semánticos por caso y genera un DerivedAsset por
# caso con su clasificación de riesgo y prioridad. Función pura: no le
# importa de dónde vienen los eventos (llamada directa o vía EDC).
def classify_events(semantic_events):

    # Agrupación por case_id para analizar cada caso de forma independiente
    grouped_cases = {}

    for event in semantic_events:

        case_id = event["case_id"]

        if case_id not in grouped_cases:

            grouped_cases[case_id] = []

        grouped_cases[case_id].append(event)

    derived_assets = []

    for case_id, events in grouped_cases.items():

        # Clasificación de los eventos del caso por nivel de severidad
        events_by_severity = {"high": [], "medium": [], "low": []}

        for event in events:

            events_by_severity[event["severity"]].append(event)

        # El nivel de riesgo del caso lo determina la severidad más alta
        # presente; la prioridad sigue el mismo orden descendente (1 = máxima)
        if events_by_severity["high"]:

            risk_level = "high"
            priority = 1

        elif events_by_severity["medium"]:

            risk_level = "medium"
            priority = 2

        else:

            risk_level = "low"
            priority = 3

        # Tipos semánticos que justifican el nivel de riesgo asignado,
        # deduplicados y ordenados para reproducibilidad del resumen
        driving_types = sorted({
            event["semantic_type"]
            for event in events_by_severity[risk_level]
        })

        summary = (
            f"{len(events)} event(s) analyzed "
            f"({len(events_by_severity['high'])} high, "
            f"{len(events_by_severity['medium'])} medium, "
            f"{len(events_by_severity['low'])} low). "
            f"Risk classified as {risk_level.upper()} based on: "
            f"{', '.join(driving_types)}."
        )

        derived_asset = DerivedAsset(
            case_id=case_id,
            risk_level=risk_level,
            priority=priority,
            summary=summary,
            generated_at=datetime.now(timezone.utc),
            source="Módulo analítico Entidad B"
        )

        derived_assets.append(derived_asset)

    return derived_assets
