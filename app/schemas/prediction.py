# app/schemas/prediction.py

from pydantic import BaseModel

class PredictionInput(BaseModel):
    ticker: str
    year: int

class PredictionOutput(BaseModel):
    ticker: str
    predicted_return: float | None = None
    status: str
    analysis: str | None = None
    long_term_outlook: float | None = None