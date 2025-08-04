# app/core/predictor.py

import os
import yfinance as yf
import pandas as pd
import pickle
from datetime import datetime, timedelta
from xgboost import XGBRegressor
from app.schemas.prediction import PredictionInput

MODELO_PATH = os.path.join("app", "models", "modelo_xgb.json")
FEATURE_EXTRACTOR_PATH = os.path.join("app", "models", "feature_extractor.pkl")

def get_expected_annual_return(ticker: str) -> tuple[float | None, str]:
    try:
        modelo = XGBRegressor()
        modelo.load_model(MODELO_PATH)

        with open(FEATURE_EXTRACTOR_PATH, 'rb') as f:
            feature_extractor = pickle.load(f)
    except Exception as e:
        return None, f"Erro ao carregar modelo ou extractor: {str(e)}"

    try:
        stock = yf.Ticker(ticker + ".SA")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        df = stock.history(start=start_date, end=end_date)
        if df.empty:
            return None, "Nenhum dado encontrado para o ticker"

        df = df.reset_index().rename(columns={
            'Date': 'data_pregao',
            'Close': 'preco_fechamento',
            'Volume': 'volume'
        })
        df['cod_negociacao'] = ticker
    except Exception as e:
        return None, f"Erro ao obter dados: {str(e)}"

    try:
        df_features = feature_extractor.transform(df)
        X = df_features[feature_extractor.features_to_use].iloc[[-1]]
    except Exception as e:
        return None, f"Erro ao preparar features: {str(e)}"

    try:
        pred = modelo.predict(X)
        return float(pred[0]), "Previsão realizada com sucesso"
    except Exception as e:
        return None, f"Erro ao fazer previsão: {str(e)}"

def carregar_modelo_e_predizer(dados: PredictionInput) -> tuple[float | None, str]:
    return get_expected_annual_return(dados.ticker)
