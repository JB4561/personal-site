"""Data shapes for the predictions API.

A Pydantic model is a class that declares the exact fields and types a piece
of data must have. Constructing one from raw data validates it: a missing
field or a wrong type raises an error immediately, instead of a bad value
travelling through the app and surfacing later as a confusing bug.

Two kinds of model live here, on either side of the backend:

    RawPrediction        INPUT contract. One record exactly as the NFL model
                         writes it to predictions.json.
    PredictionsResponse  OUTPUT contract. What /api/predictions returns, and
                         therefore what the React frontend is built against.

Keeping them separate means the upstream file format and the API's own format
can change independently. If the model renames a field, only the translation
between the two changes -- the frontend never notices.
"""

from datetime import date

from pydantic import BaseModel


class RawPrediction(BaseModel):
    """One game record as written by nfl-elo-model's live_predict.py."""

    game_id: str
    season: int
    week: int
    # Declared as `date`, not `str`: Pydantic parses "2026-09-09" into a real
    # date object, so a malformed date is rejected here rather than accepted.
    gameday: date
    away_team: str
    home_team: str
    pred_margin: float
    # `float | None` means the key must be present but its value may be null.
    # The model writes null when the market has not posted a line yet.
    spread_line: float | None


class Game(BaseModel):
    """One game as returned by the API.

    Margins use the model's convention: expected HOME margin in points,
    positive when the home team is favoured.
    """

    game_id: str
    gameday: date
    away_team: str
    home_team: str
    pred_margin: float
    spread_line: float | None
    # Model margin minus market margin. Positive means the model rates the
    # home team higher than the market does. Null whenever spread_line is.
    edge: float | None


class PredictionsResponse(BaseModel):
    """Response body for GET /api/predictions."""

    season: int
    week: int
    games: list[Game]
