import random
from datetime import datetime, timezone, timedelta
from models import TeleassistanceEvent


# Escenario de baja saturación de oxígeno.
# Simula la detección de valores anómalos de SpO2 acompañados
# de información fisiológica complementaria (frecuencia cardíaca).
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


# Escenario de detección de caída.
# Representa una situación asistencial en la que sensores domiciliarios
# detectan una caída, acompañada del registro de frecuencia cardíaca.
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


# Escenario de riesgo combinado.
# Combina eventos fisiológicos, asistenciales y técnicos dentro del mismo
# caso para validar situaciones de mayor complejidad y riesgo simultáneo.
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
        ),

        TeleassistanceEvent(
            case_id="USR-0099",
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=random.randint(0, 30)),
            semantic_type="functional_status_change",
            category="functional_status",
            observed_value=None,
            unit=None,
            severity="medium",
            source="care_team_assessment",
            description="Recent loss of mobility reported"
        )

    ]


# Escenario de riesgo bajo.
# Incluye únicamente observaciones fisiológicas dentro de parámetros
# normales; no se generan alertas ni eventos técnicos.
def low_risk_scenario():

    return [
        TeleassistanceEvent(
            case_id="USR-0021",
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=random.randint(0, 30)),
            semantic_type="oxygen_saturation",
            category="physiological_observation",
            observed_value=round(random.uniform(96.0, 99.0), 1),
            unit="%",
            severity="low",
            source="home_oximeter",
            description="Oxygen saturation within normal range"
        ),
        TeleassistanceEvent(
            case_id="USR-0021",
            timestamp=datetime.now(timezone.utc),
            semantic_type="heart_rate",
            category="physiological_observation",
            observed_value=random.randint(62, 80),
            unit="bpm",
            severity="low",
            source="smart_watch",
            description="Heart rate within normal range"
        )
    ]


# Escenario de riesgo medio.
# Incorpora incidencias moderadas que requieren seguimiento pero
# no desencadenan intervención inmediata.
def medium_risk_scenario():

    return [
        TeleassistanceEvent(
            case_id="USR-0055",
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=random.randint(0, 30)),
            semantic_type="oxygen_saturation",
            category="physiological_observation",
            observed_value=round(random.uniform(91.0, 94.0), 1),
            unit="%",
            severity="medium",
            source="home_oximeter",
            description="Slightly low oxygen saturation, monitoring required"
        ),
        TeleassistanceEvent(
            case_id="USR-0055",
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=random.randint(0, 30)),
            semantic_type="heart_rate",
            category="physiological_observation",
            observed_value=random.randint(88, 100),
            unit="bpm",
            severity="medium",
            source="smart_watch",
            description="Mildly elevated heart rate"
        ),
        TeleassistanceEvent(
            case_id="USR-0055",
            timestamp=datetime.now(timezone.utc),
            semantic_type="functional_status_change",
            category="functional_status",
            observed_value=None,
            unit=None,
            severity="medium",
            source="care_team_assessment",
            description="Decreased daily activity level, follow-up scheduled"
        )
    ]


# Escenario de riesgo alto.
# Agrupa múltiples eventos críticos de distintas categorías que
# desencadenan la generación de activos derivados con máxima prioridad.
def high_risk_scenario():

    return [
        TeleassistanceEvent(
            case_id="USR-0077",
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=random.randint(0, 30)),
            semantic_type="oxygen_saturation",
            category="physiological_observation",
            observed_value=round(random.uniform(82.0, 87.0), 1),
            unit="%",
            severity="high",
            source="home_oximeter",
            description="Critical oxygen saturation, immediate intervention required"
        ),
        TeleassistanceEvent(
            case_id="USR-0077",
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=random.randint(0, 30)),
            semantic_type="heart_rate",
            category="physiological_observation",
            observed_value=random.randint(118, 135),
            unit="bpm",
            severity="high",
            source="smart_watch",
            description="Tachycardia detected"
        ),
        TeleassistanceEvent(
            case_id="USR-0077",
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=random.randint(0, 30)),
            semantic_type="fall_detected",
            category="assistential_alert",
            observed_value=None,
            unit=None,
            severity="high",
            source="home_sensor",
            description="Fall detected, user unresponsive to intercom"
        ),
        TeleassistanceEvent(
            case_id="USR-0077",
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=random.randint(0, 30)),
            semantic_type="technical_alarm",
            category="technical_event",
            observed_value=None,
            unit=None,
            severity="high",
            source="teleassistance_gateway",
            description="Gateway disconnected, communication link lost"
        ),
        TeleassistanceEvent(
            case_id="USR-0077",
            timestamp=datetime.now(timezone.utc),
            semantic_type="functional_status_change",
            category="functional_status",
            observed_value=None,
            unit=None,
            severity="high",
            source="care_team_assessment",
            description="Acute functional deterioration, emergency protocol activated"
        )
    ]
