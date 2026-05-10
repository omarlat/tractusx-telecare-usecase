from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services import (
    EVENT_STORE,
    generate_scenario
)

app = FastAPI(
    title="Teleassistance Synthetic Generator"
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
    return {
        "status": "ok"
    }


@app.get("/events")
def get_events():
    return EVENT_STORE


@app.post("/generate/{scenario}")
def generate(scenario: str):

    return generate_scenario(scenario)

@app.get("/events/{case_id}")
def get_case_events(case_id: str):

    return [
        event
        for event in EVENT_STORE
        if event.case_id == case_id
    ]

@app.get("/scenarios")
def get_scenarios():

    return [
        "low-oxygen",
        "fall-alert",
        "mixed-risk"
    ]