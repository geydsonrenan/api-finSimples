# create_artifacts.py

import pickle
import os
from app.core.feature_engineering import FeatureExtractor # Importa do novo local

# Garante que o diretório de modelos exista
os.makedirs(os.path.join("app", "models"), exist_ok=True)

# Define o caminho de saída
output_path = os.path.join("app", "models", "feature_extractor.pkl")

print("Criando uma nova instância do FeatureExtractor...")
extractor = FeatureExtractor()

print(f"Salvando o novo artefato em: {output_path}")
with open(output_path, 'wb') as f:
    pickle.dump(extractor, f)

print("Artefato 'feature_extractor.pkl' recriado com sucesso!")