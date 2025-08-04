# app/api/routes_predict.py

from fastapi import APIRouter, HTTPException
from app.schemas.prediction import PredictionInput, PredictionOutput
from app.core.predictor import carregar_modelo_e_predizer

router = APIRouter()

@router.post("/", response_model=PredictionOutput)
def fazer_predicao(dados: PredictionInput):
    retorno, mensagem = carregar_modelo_e_predizer(dados)

    if retorno is None:
        raise HTTPException(status_code=400, detail=mensagem)

    return PredictionOutput(retorno_esperado=retorno, mensagem=mensagem)
