from scenarios import (
    low_oxygen_scenario,
    fall_alert_scenario,
    mixed_risk_scenario,
    low_risk_scenario,
    medium_risk_scenario,
    high_risk_scenario
)

EVENT_STORE = []

SCENARIO_MAP = {
    "low-oxygen":  low_oxygen_scenario,
    "fall-alert":  fall_alert_scenario,
    "mixed-risk":  mixed_risk_scenario,
    "low-risk":    low_risk_scenario,
    "medium-risk": medium_risk_scenario,
    "high-risk":   high_risk_scenario,
}


def generate_scenario(scenario_name: str):

    fn = SCENARIO_MAP.get(scenario_name)

    if fn is None:
        return []

    events = fn()
    EVENT_STORE.extend(events)
    return events
