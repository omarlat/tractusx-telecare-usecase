import random
from datetime import datetime, timezone, timedelta
from models import TeleassistanceEvent


def low_oxygen_scenario():

    return [
        TeleassistanceEvent(
            case_id="USR-0042",
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=random.randint(0, 30)),
            semantic_type="oxygen_saturation",
            category="physiological_observation",
            observed_value=random.randint(84, 98),
            unit="%",
            severity="high",
            source="home_oximeter",
            description="Low oxygen saturation detected"
        ),
        TeleassistanceEvent(
            case_id="USR-0042",
            timestamp=datetime.now(timezone.utc),
            semantic_type="heart_rate",
            category="physiological_observation",
            observed_value=random.randint(60, 130),
            unit="bpm",
            severity="medium",
            source="smart_watch",
            description="Elevated heart rate"
        )
    ]

def fall_alert_scenario():

    return [
        TeleassistanceEvent(
            case_id="USR-0088",
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=random.randint(0, 30)),
            semantic_type="fall_detected",
            category="assistential_alert",
            observed_value=None,
            unit=None,
            severity="high",
            source="home_sensor",
            description="Fall detected in living room"
        ),
        TeleassistanceEvent(
            case_id="USR-0088",
            timestamp=datetime.now(timezone.utc),
            semantic_type="heart_rate",
            category="physiological_observation",
            observed_value=random.randint(60, 130),
            unit="bpm",
            severity="medium",
            source="smart_watch",
            description="Elevated heart rate after fall"
        )
    ]

def mixed_risk_scenario():

    return [

        TeleassistanceEvent(
            case_id="USR-0099",
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=random.randint(0, 30)),
            semantic_type="oxygen_saturation",
            category="physiological_observation",
            observed_value=random.randint(84, 98),
            unit="%",
            severity="high",
            source="home_oximeter",
            description="Low oxygen saturation detected"
        ),

        TeleassistanceEvent(
            case_id="USR-0099",
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=random.randint(0, 30)),
            semantic_type="fall_detected",
            category="assistential_alert",
            observed_value=None,
            unit=None,
            severity="high",
            source="home_sensor",
            description="Fall detected in bedroom"
        ),

        TeleassistanceEvent(
            case_id="USR-0099",
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=random.randint(0, 30)),
            semantic_type="technical_alarm",
            category="technical_event",
            observed_value=None,
            unit=None,
            severity="medium",
            source="teleassistance_gateway",
            description="Device battery level below threshold"
        )

    ]