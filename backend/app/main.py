"""Personal site API.

Serves NFL Elo model predictions and related data to the site's frontend.
"""

from fastapi import FastAPI

from app.models import PredictionsResponse
from app.predictions import get_predictions

app = FastAPI(
    title="Personal Site API",
    version="0.1.0",
)


@app.get("/api/health")
def health() -> dict:
    """Liveness check.

    Has no external dependencies, so a successful response confirms the
    service is up independently of upstream data sources. Suitable for use
    as a hosting platform health check.
    """
    return {"status": "ok", "service": "personal-site-api"}


# response_model tells FastAPI the shape this route returns. It uses it to
# serialise the PredictionsResponse object to JSON, and to publish that shape
# in the /docs page -- so the frontend's contract is documented automatically.
@app.get("/api/predictions", response_model=PredictionsResponse)
def predictions() -> PredictionsResponse:
    """Current week's NFL Elo model predictions, with edge versus the market."""
    return get_predictions()
