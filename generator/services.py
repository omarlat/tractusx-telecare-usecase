from scenarios import (
    low_oxygen_scenario,
    fall_alert_scenario,
    mixed_risk_scenario,
    low_risk_scenario,
    medium_risk_scenario,
    high_risk_scenario
)

# Almacén en memoria de todos los eventos generados durante la sesión.
# Se reinicia al reiniciar el servicio; no hay persistencia entre ejecuciones.
EVENT_STORE = []

# Tabla de despacho que relaciona el nombre de escenario recibido en la URL
# con la función generadora correspondiente
SCENARIO_MAP = {
    "low-oxygen":  low_oxygen_scenario,
    "fall-alert":  fall_alert_scenario,
    "mixed-risk":  mixed_risk_scenario,
    "low-risk":    low_risk_scenario,
    "medium-risk": medium_risk_scenario,
    "high-risk":   high_risk_scenario,
}


# Ejecuta el escenario indicado, acumula sus eventos en EVENT_STORE
# y los devuelve. Devuelve lista vacía si el nombre no existe.
def generate_scenario(scenario_name: str):

    fn = SCENARIO_MAP.get(scenario_name)

    if fn is None:
        return []

    events = fn()
    EVENT_STORE.extend(events)
    return events
