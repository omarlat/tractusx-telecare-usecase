from datetime import datetime, timezone

import requests

from models import DerivedAsset


SEMANTIC_EVENTS_URL = (
    "http://localhost:8001/semantic-events"
)


def analyze_events():

    response = requests.get(
        SEMANTIC_EVENTS_URL
    )

    semantic_events = response.json()

    grouped_cases = {}

    for event in semantic_events:

        case_id = event["case_id"]

        if case_id not in grouped_cases:

            grouped_cases[case_id] = []

        grouped_cases[case_id].append(event)

    derived_assets = []

    for case_id, events in grouped_cases.items():

        risk_level = "medium"

        priority = 2

        for event in events:

            if event["severity"] == "high":

                risk_level = "high"

                priority = 1

        derived_asset = DerivedAsset(
            case_id=case_id,
            risk_level=risk_level,
            priority=priority,
            summary="Synthetic teleassistance risk evaluation",
            generated_at=datetime.now(timezone.utc),
            source="Módulo analítico Entidad B"
        )

        derived_assets.append(derived_asset)

    return derived_assets