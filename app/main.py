# app/main.py

from fastapi import FastAPI
from app.api.routes_predict import router as predict_router

app = FastAPI(
    title="API FinSimples",
    description="API que utiliza um modelo XGBoost para previsão de ações.",
    version="1.0.0",
)

# Inclui as rotas definidas em routes_predict.py
app.include_router(predict_router, prefix="/api")
