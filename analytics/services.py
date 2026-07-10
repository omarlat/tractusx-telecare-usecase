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

        events_by_severity = {"high": [], "medium": [], "low": []}

        for event in events:

            events_by_severity[event["severity"]].append(event)

        if events_by_severity["high"]:

            risk_level = "high"

            priority = 1

        elif events_by_severity["medium"]:

            risk_level = "medium"

            priority = 2

        else:

            risk_level = "low"

            priority = 3

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