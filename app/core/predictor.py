import os
import yfinance as yf
import pandas as pd
import pickle
from xgboost import XGBRegressor
import requests
import requests_cache
from pathlib import Path

from app.schemas.prediction import PredictionInput
from app.core.feature_engineering import FeatureExtractor
from app.config import BRAPI_TOKEN # Importa o token do config

MODELO_PATH = os.path.join("app", "models", "modelo_xgb.json")
FEATURE_EXTRACTOR_PATH = os.path.join("app", "models", "feature_extractor.pkl")

CACHE_DIR = Path("app/yf_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_FILE = CACHE_DIR / "yfinance.cache"

def get_data_from_brapi(ticker: str, session: requests.Session) -> pd.DataFrame | None:
    print(f"DEBUG: yfinance falhou. Tentando obter dados da Brapi.dev para {ticker}...")
    if not BRAPI_TOKEN:
        print("DEBUG: Token da Brapi.dev não foi configurado.")
        return None
    try:
        url = f"https://brapi.dev/api/quote/{ticker}?range=3mo&interval=1d&token={BRAPI_TOKEN}"
        response = session.get(url)
        response.raise_for_status()
        data = response.json()
        if 'results' not in data or not data['results'] or 'historicalDataPrice' not in data['results'][0]:
            return None
        historical_data = data['results'][0]['historicalDataPrice']
        df = pd.DataFrame(historical_data)
        df['data_pregao'] = pd.to_datetime(df['date'], unit='s')
        df = df.rename(columns={'close': 'preco_fechamento', 'volume': 'volume'})
        df['cod_negociacao'] = ticker
        print("DEBUG: Dados obtidos com sucesso da Brapi.dev!")
        return df[['data_pregao', 'cod_negociacao', 'preco_fechamento', 'volume']]
    except Exception as e:
        print(f"DEBUG: Erro ao buscar dados da Brapi.dev: {e}")
        return None

def get_expected_annual_return(ticker: str) -> tuple[float | None, str, pd.DataFrame | None]:
    try:
        modelo = XGBRegressor()
        with open(MODELO_PATH, 'rb') as model_file:
            modelo.load_model(bytearray(model_file.read()))
        with open(FEATURE_EXTRACTOR_PATH, 'rb') as f:
            feature_extractor = pickle.load(f)
    except Exception as e:
        return None, f"Erro ao carregar modelo ou extractor: {str(e)}", None

    try:
        session = requests_cache.CachedSession(str(CACHE_FILE))
        session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        
        stock = yf.Ticker(ticker + ".SA", session=session)
        df = stock.history(period="1y")

        if df.empty:
            df = get_data_from_brapi(ticker, session)

        if df is None or df.empty:
            return None, f"Nenhum dado encontrado para o ticker {ticker}", None

        if 'Date' in df.columns:
            df = df.reset_index().rename(columns={
                'Date': 'data_pregao',
                'Close': 'preco_fechamento',
                'Volume': 'volume'
            })
            df['cod_negociacao'] = ticker
    except Exception as e:
        return None, f"Erro ao obter dados da ação: {str(e)}", None

    try:
        df_features = feature_extractor.transform(df)
        X = df_features[feature_extractor.features_to_use].iloc[[-1]]
        pred = modelo.predict(X)
        return float(pred[0]), "Previsão realizada com sucesso", df
    except Exception as e:
        return None, f"Erro ao fazer previsão: {str(e)}", None