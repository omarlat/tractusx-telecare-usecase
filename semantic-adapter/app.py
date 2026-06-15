from fastapi import FastAPI
from services import get_semantic_events
from services import load_vital_signs_aspect
from services import build_fhir_observation
from services import list_aspects
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Semantic Adapter"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():

    return load_vital_signs_aspect()


# Eventos funcionales enriquecidos semánticamente y validados
@app.get("/semantic-events")
def semantic_events():

    return get_semantic_events()


# Catálogo de aspectos funcionales: aspectos del registro + UnmappedEventAspect
@app.get("/aspects")
def aspects():

    return list_aspects()

# Eventos semánticos serializados como recursos HL7 FHIR Observation
@app.get("/fhir-events")
def fhir_events():

    semantic_events = get_semantic_events()

    return [
        build_fhir_observation(event)
        for event in semantic_events
    ]
