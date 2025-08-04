# Contém toda a lógica para buscar indicadores e chamar a OpenAI.
# -------------------------------------------------------------------
import requests
import json
from openai import OpenAI
from app.config import OPENAI_API_KEY, BRAPI_TOKEN

if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)
else:
    client = None

def get_stock_indicators(ticker: str) -> dict | None:
    """Busca indicadores fundamentalistas de uma ação na Brapi.dev."""
    if not BRAPI_TOKEN:
        return None
    try:
        url = f"https://brapi.dev/api/quote/{ticker}?fundamental=true&token={BRAPI_TOKEN}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if "results" in data and data["results"]:
            indicators = data["results"][0]
            key_indicators = {
                "P/L": indicators.get("pL") or indicators.get("priceEarnings"),
                "P/VP": indicators.get("pVp"), "Dividend Yield": indicators.get("dividendYield"),
                "ROE": indicators.get("roe"), "Liquidez Corrente": indicators.get("liquidezCorrente"),
                "Dívida Líquida/Patrimônio": indicators.get("dividaLiquidaPatrimonio"),
                "Margem Líquida": indicators.get("margemLiquida"),
            }
            filtered = {k: v for k, v in key_indicators.items() if v is not None}
            return filtered if filtered else None
        return None
    except Exception as e:
        print(f"DEBUG: Erro ao buscar indicadores da Brapi: {e}")
        return None

def generate_ai_insights(ticker: str, predicted_return: float) -> tuple[str | None, float | None]:
    """
    Gera insights da OpenAI, solicitando uma resposta estruturada em JSON.
    Retorna (análise, projeção_5_anos).
    """
    if not client:
        return "Análise não disponível: Chave da API da OpenAI não configurada.", None

    indicators = get_stock_indicators(ticker)
    if not indicators:
        return "Análise não disponível: Não foi possível obter os indicadores da ação.", None

    indicators_text = "\n".join([f"- {key}: {value}" for key, value in indicators.items()])
    
    # --- PROMPT ATUALIZADO PARA SOLICITAR JSON SIMPLIFICADO ---
    prompt = f"""
    Você é um analista financeiro para investidores iniciantes.
    A ação é {ticker}, com previsão de retorno anual de {predicted_return:.2%}.
    Indicadores:
    {indicators_text}

    Sua resposta DEVE ser um objeto JSON válido com duas chaves: "analysis" e "five_year_return_percentage".

    1.  Para a chave "analysis", crie um texto em português formatado exatamente assim:
        ### Análise da Ação: {ticker} - <nome da empresa>
        **Contexto sobre a empresa**
        [Descreva em 2-3 frases características da empresa, como seu setor de atuação e o tempo de atividade no mercado]
        **Explicação do Resultado:**
        [Explique em 3-4 frases como os indicadores e a previsão se conectam.]
        **Prós de Investir:**
        - [Ponto positivo 1]
        - [Ponto positivo 2]
        **Contras de Investir:**
        - [Ponto negativo 1]
        - [Ponto negativo 2]

    2.  Para a chave "five_year_return_percentage", forneça UM ÚNICO NÚMERO (float) representando a rentabilidade total estimada em 5 anos (ex: 35.5 para 35.5%). Não use só a rentabilidade anual como métrica, considere também as características da empresa, como o tempo de atuação no mercado, indicadores e o setor de atuação.
    """

    try:
        print("DEBUG: Enviando requisição para a OpenAI solicitando JSON...")
        completion = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "Você é um analista financeiro que responde estritamente com objetos JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
        )
        response_text = completion.choices[0].message.content
        data = json.loads(response_text)
        
        analysis = data.get("analysis")
        outlook_pct = data.get("five_year_return_percentage")

        print("DEBUG: Resposta JSON da OpenAI recebida e processada com sucesso.")
        return analysis, outlook_pct

    except Exception as e:
        print(f"DEBUG: Erro ao chamar ou processar resposta da OpenAI: {e}")
        return f"Erro ao gerar análise: {e}", None