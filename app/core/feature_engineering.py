# app/core/feature_engineering.py

import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin

class FeatureExtractor(BaseEstimator, TransformerMixin):
    """Classe para extração avançada de features"""
    def __init__(self):
        self.features_to_use = []
    
    def fit(self, X, y=None):
        return self
    
    def transform(self, df):
        df = df.copy()
        
        if 'data_pregao' in df.columns:
            df['data_pregao'] = pd.to_datetime(df['data_pregao'])
            df = df.sort_values(['cod_negociacao', 'data_pregao'])
        
        gb = df.groupby('cod_negociacao')['preco_fechamento']
        
        for window in [4, 8, 12, 26]:
            df[f'media_{window}w'] = gb.rolling(window=window).mean().reset_index(level=0, drop=True)
            df[f'vol_{window}w'] = gb.rolling(window=window).std().reset_index(level=0, drop=True)
        
        def safe_return(current, past, min_price=0.01):
            with np.errstate(divide='ignore', invalid='ignore'):
                return np.where(
                    (past > min_price) & (current > min_price),
                    (current - past) / past,
                    np.nan
                )
        
        for weeks, periods in [(1,0), (4,3), (12,11), (26,25)]:
            preco_passado = gb.shift(periods)
            df[f'retorno_{weeks}w'] = safe_return(df['preco_fechamento'], preco_passado)
        
        def calculate_rsi(series, window=14):
            delta = series.diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            avg_gain = gain.rolling(window=window, min_periods=1).mean()
            avg_loss = loss.rolling(window=window, min_periods=1).mean()
            
            rs = avg_gain / avg_loss.replace(0, np.nan)
            return 100 - (100 / (1 + rs.replace(np.inf, 100)))
        
        df['rsi_14'] = df.groupby('cod_negociacao')['preco_fechamento'].transform(calculate_rsi)
        
        for lag in [1, 2, 3, 4]:
            if 'retorno_1w' in df.columns:
                 df[f'retorno_lag_{lag}w'] = df.groupby('cod_negociacao')['retorno_1w'].shift(lag)
        
        df['ema_12'] = df.groupby('cod_negociacao')['preco_fechamento'].transform(
            lambda x: x.ewm(span=12).mean()
        )
        
        if 'volume' in df.columns:
            vol_gb = df.groupby('cod_negociacao')['volume']
            for window in [4, 12]:
                df[f'volume_medio_{window}w'] = vol_gb.rolling(window=window).mean().reset_index(level=0, drop=True)
        
        self.features_to_use = [
            'media_4w', 'media_12w', 'vol_4w', 'vol_12w',
            'retorno_4w', 'retorno_12w',
            'volume_medio_4w', 'ema_12', 'rsi_14'
        ]
        
        return df