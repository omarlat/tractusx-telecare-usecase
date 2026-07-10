from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services import (
    EVENT_STORE,
    generate_scenario
)

app = FastAPI(
    title="Teleassistance Synthetic Generator"
)

# CORS abierto para permitir llamadas desde la demo-ui y herramientas
# de desarrollo sin restricción de origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


# Devuelve todos los eventos acumulados en EVENT_STORE desde el inicio
# de la sesión, independientemente del escenario que los generó
@app.get("/events")
def get_events():
    return EVENT_STORE


# Genera los eventos del escenario indicado y los acumula en EVENT_STORE.
# Los escenarios disponibles se listan en GET /scenarios.
@app.post("/generate/{scenario}")
def generate(scenario: str):
    return generate_scenario(scenario)


# Filtra EVENT_STORE por case_id para recuperar todos los eventos
# asociados a un caso concreto
@app.get("/events/{case_id}")
def get_case_events(case_id: str):
    return [
        event
        for event in EVENT_STORE
        if event.case_id == case_id
    ]


# Catálogo de escenarios disponibles en el generador
@app.get("/scenarios")
def get_scenarios():
    return [
        "low-oxygen",
        "fall-alert",
        "mixed-risk",
        "low-risk",
        "medium-risk",
        "high-risk"
    ]
