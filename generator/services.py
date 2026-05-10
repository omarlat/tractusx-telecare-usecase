from scenarios import (
    low_oxygen_scenario,
    fall_alert_scenario,
    mixed_risk_scenario
)

EVENT_STORE = []


def generate_scenario(scenario_name: str):

    if scenario_name == "low-oxygen":

        events = low_oxygen_scenario()

        EVENT_STORE.extend(events)

        return events
    
    if scenario_name == "fall-alert":

        events = fall_alert_scenario()

        EVENT_STORE.extend(events)

        return events

    if scenario_name == "mixed-risk":

        events = mixed_risk_scenario()

        EVENT_STORE.extend(events)

        return events

    return []