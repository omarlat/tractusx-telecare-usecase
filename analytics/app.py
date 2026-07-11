from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services import analyze_events, classify_events

app = FastAPI(
    title="Telecare Analytics"
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


# Ejecuta el análisis sobre los eventos semánticos actuales y devuelve
# un DerivedAsset por cada caso presente en el EVENT_STORE del generator.
# Llama directamente a semantic-adapter: solo para pruebas manuales
# (ver DEV.md), el flujo de la demo usa POST /analyze.
@app.get("/derived-assets")
def derived_assets():

    return analyze_events()


class AnalyzeRequest(BaseModel):

    semantic_events: list[dict]


# Analiza los eventos semánticos recibidos en el body, sin llamar a
# semantic-adapter: es lo que usa la demo con los eventos que llegaron
# a través del espacio de datos (dataspace-connector)
@app.post("/analyze")
def analyze(request: AnalyzeRequest):

    return classify_events(request.semantic_events)
