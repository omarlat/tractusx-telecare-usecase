from fastapi import FastAPI
from services import get_semantic_events
from services import load_vital_signs_aspect
from services import build_fhir_observation
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


@app.get("/semantic-events")
def semantic_events():

    return get_semantic_events()

@app.get("/fhir-events")
def fhir_events():

    semantic_events = get_semantic_events()

    return [
        build_fhir_observation(event)
        for event in semantic_events
    ]