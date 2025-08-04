# app/core/predictor.py

import os
import yfinance as yf
import pandas as pd
import pickle
from datetime import datetime, timedelta
from xgboost import XGBRegressor
from app.schemas.prediction import PredictionInput
import requests
from dotenv import load_dotenv

# Importa a classe do seu módulo centralizado
from app.core.feature_engineering import FeatureExtractor

import requests_cache
from pathlib import Path

MODELO_PATH = os.path.join("app", "models", "modelo_xgb.json")
FEATURE_EXTRACTOR_PATH = os.path.join("app", "models", "feature_extractor.pkl")

load_dotenv()
BRAPI_TOKEN = os.environ.get("BRAPI_TOKEN", "")

CACHE_DIR = Path("app/yf_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_FILE = CACHE_DIR / "yfinance.cache"


def get_data_from_brapi(ticker: str, session: requests.Session) -> pd.DataFrame | None:
    """
    Obtém dados históricos da Brapi.dev como uma fonte alternativa.
    """
    print(f"DEBUG: yfinance falhou. Tentando obter dados da Brapi.dev para {ticker}...")
    if not BRAPI_TOKEN:
        print("DEBUG: Token da Brapi.dev não foi configurado.")
        return None
        
    try:
        # --- CORREÇÃO APLICADA AQUI: Ajuste do período para o plano gratuito ---
        # Alterado de '1y' para '6mo' para se adequar às limitações do plano free da Brapi.
        url = f"https://brapi.dev/api/quote/{ticker}?range=3mo&interval=1d&token={BRAPI_TOKEN}"
        
        response = session.get(url)
        response.raise_for_status()
        data = response.json()
        
        if 'results' not in data or not data['results'] or 'historicalDataPrice' not in data['results'][0]:
            print(f"DEBUG: Brapi.dev não retornou dados para {ticker}")
            return None
        
        historical_data = data['results'][0]['historicalDataPrice']
        df = pd.DataFrame(historical_data)

        df['data_pregao'] = pd.to_datetime(df['date'], unit='s')
        df = df.rename(columns={'close': 'preco_fechamento', 'volume': 'volume'})
        df['cod_negociacao'] = ticker
        
        print(f"DEBUG: Dados obtidos com sucesso da Brapi.dev!")
        return df[['data_pregao', 'cod_negociacao', 'preco_fechamento', 'volume']]
    except Exception as e:
        print(f"DEBUG: Erro ao buscar dados da Brapi.dev: {e}")
        return None

def get_expected_annual_return(ticker: str) -> tuple[float | None, str]:
    """
    Carrega o modelo e o feature extractor, obtém dados de uma ação,
    prepara as features e retorna a predição de rentabilidade anual.
    """
    try:
        modelo = XGBRegressor()
        with open(MODELO_PATH, 'rb') as model_file:
            modelo.load_model(bytearray(model_file.read()))
        with open(FEATURE_EXTRACTOR_PATH, 'rb') as f:
            feature_extractor = pickle.load(f)
    except Exception as e:
        return None, f"Erro ao carregar modelo ou extractor: {str(e)}"

    # Bloco para obter dados da ação
    try:
        session = requests_cache.CachedSession(str(CACHE_FILE))
        session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        
        print(f"DEBUG: Tentando obter dados do yfinance para {ticker}...")
        stock = yf.Ticker(ticker + ".SA", session=session)
        df = stock.history(period="1y")

        if df.empty:
            df = get_data_from_brapi(ticker, session)

        if df is None or df.empty:
            return None, f"Nenhum dado encontrado para o ticker {ticker} em nenhuma das fontes (yfinance, Brapi)."

        if 'Date' in df.columns:
            df = df.reset_index().rename(columns={
                'Date': 'data_pregao',
                'Close': 'preco_fechamento',
                'Volume': 'volume'
            })
            df['cod_negociacao'] = ticker
            
    except Exception as e:
        return None, f"Erro ao obter dados da ação: {str(e)}"

    # Bloco para extrair features
    try:
        df_features = feature_extractor.transform(df)
        X = df_features[feature_extractor.features_to_use].iloc[[-1]]
    except Exception as e:
        return None, f"Erro ao preparar features: {str(e)}"

    # Bloco para realizar a predição
    try:
        pred = modelo.predict(X)
        return float(pred[0]), "Previsão realizada com sucesso"
    except Exception as e:
        return None, f"Erro ao fazer previsão: {str(e)}"

def carregar_modelo_e_predizer(dados: PredictionInput) -> tuple[float | None, str]:
    return get_expected_annual_return(dados.ticker)
