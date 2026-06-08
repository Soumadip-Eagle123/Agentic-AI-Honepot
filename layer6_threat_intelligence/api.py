# layer6_threat_intelligence/api.py

from fastapi import FastAPI
from fastapi import HTTPException

from layer6_threat_intelligence.analyzer import (
    run_layer6
)

app = FastAPI(

    title="Layer 6 Threat Intelligence",

    description="Behavioral profiling and campaign correlation",

    version="1.0"

)


@app.get("/")
def root():

    return {

        "layer": 6,

        "name":
        "Threat Intelligence Correlation",

        "status":
        "online"

    }


@app.get("/analyze/{session_id}")
def analyze(session_id: str):

    result = run_layer6(
        session_id
    )

    if result is None:

        raise HTTPException(

            status_code=404,

            detail=
            "Session not found"

        )

    return result