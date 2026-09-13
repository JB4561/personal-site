"""Personal site API.

Serves NFL Elo model predictions and related data to the site's frontend.
"""

from fastapi import FastAPI

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
