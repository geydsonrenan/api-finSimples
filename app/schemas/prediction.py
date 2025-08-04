# app/schemas/prediction.py

from pydantic import BaseModel

class PredictionInput(BaseModel):
    ticker: str

class PredictionOutput(BaseModel):
    retorno_esperado: float
    mensagem: str
