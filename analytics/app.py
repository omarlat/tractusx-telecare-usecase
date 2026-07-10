from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services import analyze_events

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
# un DerivedAsset por cada caso presente en el EVENT_STORE del generator
@app.get("/derived-assets")
def derived_assets():

    return analyze_events()
