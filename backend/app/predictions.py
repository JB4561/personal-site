"""Fetch the NFL model's predictions and shape them into the API response.

This module knows nothing about HTTP routes or FastAPI. It is plain Python:
get data, check it, transform it. Keeping that separate from main.py means the
logic can be tested by calling functions directly, and the route handler stays
a one-liner.
"""

import httpx
from pydantic import TypeAdapter

from app.models import Game, PredictionsResponse, RawPrediction

# The raw.githubusercontent.com host serves a file's contents directly, rather
# than the GitHub web page that wraps it. Pointing at `main` means the site
# always reads whatever the model repo last pushed.
PREDICTIONS_URL = (
    "https://raw.githubusercontent.com/JB4561/nfl-elo-model/main/predictions.json"
)

# Seconds to wait for GitHub before giving up. Without a timeout, a slow or
# hung upstream would hold the request open indefinitely -- and the browser
# waiting on /api/predictions would hang with it.
FETCH_TIMEOUT_SECONDS = 10.0

# BaseModel validates a single object. TypeAdapter does the same job for a type
# that is not a model class -- here, a *list* of RawPrediction.
_raw_list_adapter = TypeAdapter(list[RawPrediction])


def fetch_raw_predictions() -> list[RawPrediction]:
    """Download predictions.json from GitHub and validate every record.

    This is the backend acting as a CLIENT: the same kind of GET request a
    browser makes to our API, made by our server to GitHub's.

    Raises on any failure -- network error, non-2xx status, or a record that
    does not match RawPrediction. Handling those gracefully is chunk 2b.
    """
    response = httpx.get(PREDICTIONS_URL, timeout=FETCH_TIMEOUT_SECONDS)
    # Turns a 404 or 500 from GitHub into an exception. Without this, an error
    # page's body would be passed on to the JSON parser as if it were data.
    response.raise_for_status()
    return _raw_list_adapter.validate_python(response.json())


def compute_edge(pred_margin: float, spread_line: float | None) -> float | None:
    """Model margin minus market margin, or None when there is no market line.

    Both inputs share a sign convention (positive = home favoured), so plain
    subtraction is correct. Rounded because float subtraction produces values
    like 4.6 - 3.5 = 1.0999999999999996.
    """
    if spread_line is None:
        return None
    return round(pred_margin - spread_line, 2)


def build_response(records: list[RawPrediction]) -> PredictionsResponse:
    """Translate raw model records into the API's response shape.

    Season and week move from every record up to the top level. That is only
    valid if the file holds a single slate, which live_predict.py guarantees,
    so it is checked rather than assumed: mixing two weeks under one label
    would display silently wrong data.
    """
    slates = {(r.season, r.week) for r in records}
    if len(slates) != 1:
        raise ValueError(
            f"Expected predictions for exactly one season/week, found {sorted(slates)}"
        )
    (season, week), = slates

    games = [
        Game(
            game_id=r.game_id,
            gameday=r.gameday,
            away_team=r.away_team,
            home_team=r.home_team,
            pred_margin=r.pred_margin,
            spread_line=r.spread_line,
            edge=compute_edge(r.pred_margin, r.spread_line),
        )
        # Order is preserved: the model already sorts games by kickoff.
        for r in records
    ]
    return PredictionsResponse(season=season, week=week, games=games)


def get_predictions() -> PredictionsResponse:
    """Fetch and build the current predictions response."""
    return build_response(fetch_raw_predictions())
