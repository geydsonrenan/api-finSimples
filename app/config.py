# Centraliza o gerenciamento de todas as chaves e configurações.
# -------------------------------------------------------------------
import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env para o ambiente
load_dotenv()

# Chave da API da Brapi.dev
BRAPI_TOKEN = os.environ.get("BRAPI_TOKEN", "")

# Chave da API da OpenAI
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")