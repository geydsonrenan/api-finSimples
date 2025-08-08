# app/api/routes_predict.py

# Orquestra a chamada para predição e para a análise.
# -------------------------------------------------------------------
from fastapi import APIRouter, HTTPException
from app.schemas.prediction import PredictionInput, PredictionOutput
from app.core.predictor import get_expected_annual_return
from app.core.gpt_summary import generate_ai_insights

router = APIRouter()

@router.post("/predict", response_model=PredictionOutput)
def predict_stock_return(data: PredictionInput):
    ticker = data.ticker.upper()
    year = data.years
    
    predicted_return, status, _ = get_expected_annual_return(ticker)

    if predicted_return is None:
        raise HTTPException(status_code=404, detail=status)

    # Chama a função que agora retorna apenas dois valores
    analysis_text, outlook_value = generate_ai_insights(ticker, predicted_return, year)

    return PredictionOutput(
        ticker=ticker,
        predicted_return=predicted_return,
        status=status,
        analysis=analysis_text,
        long_term_outlook=outlook_value
    )