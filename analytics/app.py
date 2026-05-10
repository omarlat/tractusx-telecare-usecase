from fastapi import FastAPI

from services import analyze_events

app = FastAPI(
    title="Telecare Analytics"
)


@app.get("/health")
def health():

    return {
        "status": "ok"
    }


@app.get("/derived-assets")
def derived_assets():

    return analyze_events()