from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services import analyze_events

app = FastAPI(
    title="Telecare Analytics"
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


@app.get("/derived-assets")
def derived_assets():

    return analyze_events()