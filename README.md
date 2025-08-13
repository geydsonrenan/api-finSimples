# FinSimples — API (FastAPI)

API do **FinSimples** para projetar o **retorno percentual** de ativos da **B3** em **1–5 anos** e gerar **contexto em linguagem simples** (empresa/setor/alertas) com ChatGPT.

> **Status do MVP**
> - TTV atual ≈ **60 s** (com cache a meta é ≤ **15 s**)
> - Período aceito: **1–5 anos**
> - **PDF**: apenas nas versões pagas (**não implementado** no MVP)

---

## 🔧 Stack
- **Python 3.10+**, **FastAPI**, **Uvicorn**
- **pandas / numpy / scikit-learn** (projeção estatística/ML)
- **yfinance** (dados históricos)
- **OpenAI API** (narrativa opcional – empresa e setor)
- (Opcional) **Redis** para cache
- Deploy/observabilidade: **bravi.dev** (ou similar)

---

## 📁 Estrutura (simplificada)
O código-fonte fica dentro de **`app/`** (entrada da API).  
Há **`requirements.txt`** e **`Procfile`** na raiz para execução/deploy.

> **Execução no Procfile**
> ```bash
> web: gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
> ```

---

## ▶️ Como rodar localmente

### 1) Clonar e instalar
```bash
git clone https://github.com/geydsonrenan/api-finSimples.git
cd api-finSimples

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
````

### 2) Variáveis de ambiente

```env
APP_ENV=dev
LOG_LEVEL=INFO
PORT=8000
CORS_ORIGINS=http://localhost:3000

# OpenAI (narrativa opcional)
OPENAI_API_KEY=coloque_sua_chave_aqui
OPENAI_MODEL=gpt-4o-mini

# Limites
MIN_PERIOD_YEARS=1
MAX_PERIOD_YEARS=5

# (Opcional) Cache
REDIS_URL=redis://localhost:6379/0
```

### 3) Subir a API

```bash
uvicorn app.main:app --reload --port 8000
```

---

## 🔌 Endpoints (MVP)

### `GET /health`

Healthcheck da API.

**Resposta exemplo**

```json
{"status": "ok", "env": "dev"}
```

---

### `GET /assets/{ticker}/history?start=YYYY-MM-DD&end=YYYY-MM-DD`

Retorna a série histórica (para o frontend plotar o gráfico).

**Resposta exemplo**

```json
{
  "ticker": "PETR4.SA",
  "currency": "BRL",
  "data": [
    {
      "date": "2025-07-29",
      "open": 31.00,
      "high": 31.80,
      "low": 30.95,
      "close": 31.45,
      "volume": 12345678
    }
  ],
  "source": "yfinance"
}
```

---

### `POST /predict`

Projeção + intervalo simples; narrativa opcional via LLM.

**Body**

```json
{
  "ticker": "PETR4.SA",
  "period_years": 3,
  "include_narrative": true
}
```

**Resposta exemplo**

```json
{
  "ticker": "PETR4.SA",
  "period_years": 3,
  "as_of": "2025-08-13",
  "projection_pct": 6.0,
  "ci_low_pct": 1.5,
  "ci_high_pct": 10.5,
  "stats": {
    "cagr": 0.082,
    "volatility_annual": 0.24,
    "mean_return_annual": 0.08
  },
  "risk_bullets": [
    "Volatilidade ligada ao preço do petróleo",
    "Impacto de câmbio e decisões da OPEP"
  ],
  "narrative": "Texto claro sobre empresa e setor (sem jargões/sem call de compra ou venda).",
  "disclaimer": "Projeções baseadas em dados históricos; não garantem resultados."
}
```

**Erros comuns**

* `400` — ticker/período inválido
* `422` — payload inválido (Pydantic)
* `500` — erro interno

---

## 🛡️ Validação, Segurança e LGPD

* **Ticker**: whitelist/regex `^[A-Za-z0-9.\-]{1,12}$` + normalização
* **Período**: inteiro `1..5`
* **Prompt-safety (LLM)**: narrativa neutra e sem recomendações
* **LGPD**: sem PII; logs anonimizados e expurgo ≤ 7 dias
* **CORS**: restrito a origens confiáveis (`CORS_ORIGINS`)

---

## ⚡ Performance & Cache

* Cache de séries do `yfinance` e respostas do LLM (se Redis disponível)
* TTL curto (5–15 min) para dados recentes
* Meta de latência: ≤ 2 s (p95)
* Objetivo TTV: ≤ 15 s após otimizações

---

## 🐳 Docker (opcional)

**Dockerfile**

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -U pip && pip install -r requirements.txt
COPY . .
ENV PORT=8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml** com Redis:

```yaml
version: "3.9"
services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      - redis

  redis:
    image: redis:7
    ports:
      - "6379:6379"
```

---

## 🧪 Testes

* Unit/integração: **pytest**
* Carga: **k6 / locust**
* Segurança: fuzzing + OWASP ZAP

**Rodar testes**

```bash
pytest -q
```

---

## 📈 Observabilidade

* Logs estruturados (JSON)
* Sentry para exceções
* Datadog/Grafana: p95, throughput, error rate
* Alertas: p95 > 2 s, error rate > 1%

---

## 🔜 Roadmap (curto prazo)

* Cache agressivo e paralelismo de I/O
* API para parceiros (auth por chave, rate limit)
* Alertas de volatilidade (jobs)
* PDF (pago): mini-relatório (não implementado)

---

## 🤝 Contribuição

1. Abra uma issue
2. Crie um branch `feature/nome`
3. Envie PR com descrição e testes
4. CI: lint + testes

---

## 📄 Licença

Defina a licença (ex.: MIT) e adicione o arquivo `LICENSE` na raiz.

