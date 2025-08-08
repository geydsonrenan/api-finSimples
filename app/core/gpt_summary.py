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

def generate_ai_insights(ticker: str, predicted_return: float, year: int) -> tuple[str | None, float | None]:
    """
    Gera insights da OpenAI, solicitando uma resposta estruturada em JSON.
    Retorna (análise, projeção_5_anos).
    """
    if year == 1:
        year = 5

    if not client:
        return "Análise não disponível: Chave da API da OpenAI não configurada.", None

    indicators = get_stock_indicators(ticker)
    if not indicators:
        return "Análise não disponível: Não foi possível obter os indicadores da ação.", None

    indicators_text = "\n".join([f"- {key}: {value}" for key, value in indicators.items()])
    
    # --- PROMPT ATUALIZADO PARA SOLICITAR JSON SIMPLIFICADO ---
    prompt = f"""
    Você é um analista financeiro cético e conservador, escrevendo para investidores iniciantes.
    A ação em análise é a {ticker}.

    DADOS DISPONÍVEIS:
    1.  Previsão de Retorno Anual (modelo quantitativo): {predicted_return:.2%}
    2.  Indicadores Financeiros Atuais:
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

    2.  Para a chave "five_year_return_percentage", calcule uma projeção de retorno total para {year} anos.
        Assuma o papel de um analista financeiro conservador.

        **Objetivo:** Calcular a projeção de retorno total de uma ação em {year} anos, de forma realista e fundamentada.

        **Dados de Entrada:**
        * **Retorno Projetado (1 ano):** {predicted_return:.2%}

        **Instruções de Cálculo:**
        1.  Comece com o retorno projetado para 1 ano, mas **não o extrapole matematicamente** para {year} anos (Ex: não faça `retorno_1_ano * {year}`).
        2.  Avalie a tendência de longo prazo do setor da empresa usando a tabela abaixo.
        3.  Aplique um **fator de ajuste qualitativo** baseado na tendência do setor e em uma visão conservadora do mercado brasileiro. Ações com retornos anuais muito altos devem ser ajustadas para baixo, refletindo a dificuldade de manter tal performance. Ações com rentabilidade negativa não significam necessariamente rentabilidades negativas ao longo prazo. Tudo depende do setor.
        4.  Com base nesta análise, estabeleça uma projeção de **retorno total acumulado** para os {year} anos.

        **Tabela de Referência Setorial:**
        * "Financeiro": "Estável com crescimento moderado"
        * "Consumo": "Ligado à renda e confiança do consumidor"
        * "Industrial": "Cíclico e dependente de investimentos"
        * "Agropecuária": "Forte crescimento e vocação exportadora"
        * "Saúde": "Crescimento sólido e defensivo"
        * "Varejo": "Altamente competitivo e em transformação"
        * "Energia": "Estável com forte viés de transição"
        * "Tecnologia": "Alto crescimento e inovação constante"
        * "Saneamento": "Estável com enorme potencial de crescimento"
        * "Siderurgia/Metalurgia/Mineração": "Altamente cíclico e ligado a commodities"
        * "Construção Civil/Imobiliário": "Altamente cíclico e sensível aos juros"
        * "Papel e Celulose": "Forte vocação exportadora e competitiva"
        * *(outros setores da sua lista)*

        **Formato da Resposta:**
        * Retorne **apenas o número final** da projeção de retorno total em {year} anos, como um valor de ponto flutuante (float).
        * **Exemplo:** Se a projeção for de 45.8%, retorne `45.8`.
    """

    try:
        print("DEBUG: Enviando requisição para a OpenAI solicitando JSON...")
        completion = client.chat.completions.create(
            model="gpt-4.1",
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