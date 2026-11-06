"""
Módulo Assistente IA Eletromecânico (AutoScan BR)
Permite fazer perguntas livres à IA, enviando automaticamente a telemetria ao vivo,
tensões do alternador/bateria, falhas DTC e tolerâncias nominais do veículo.
Gera planos de teste práticos com multímetro, ponta de prova e testes elétricos.
"""

import os
import time
import json

class ElectricalAIAssistant:
    # Modelos Gratuitos Oficiais do Google AI Studio com suas características
    FREE_MODELS = {
        "gemini-3.8-flash": "🧠 Gemini 3.8 Flash (Recomendado / Mais Inteligente)",
        "gemini-3.1-flash-lite": "⚡ Gemini 3.1 Flash-Lite (Ultrarrápido & Menor Espera)",
        "gemini-3.5-flash": "🚀 Gemini 3.5 Flash (Equilibrado)",
        "gemini-2.0-flash": "🔹 Gemini 2.0 Flash (Geral)",
    }

    @staticmethod
    def ask_ai_mechanic(question, current_telemetry, active_vehicle, dtcs=None, gemini_key="", preferred_model=None):
        key = gemini_key or os.environ.get("GEMINI_API_KEY", "")
        if not key:
            return (
                "⚠️ CHAVE GEMINI NÃO CONFIGURADA:\n\n"
                "Para conversar com a IA, insira sua chave gratuita do Google AI Studio no botão '⚙️ Configurar Gemini AI' na lateral."
            )

        try:
            from google import genai
            client = genai.Client(api_key=key)

            # Prepara contexto elétrico e mecânico ao vivo
            veh_name = active_vehicle.get("model_name", "Veículo Genérico")
            plate = active_vehicle.get("plate", "---")
            km = active_vehicle.get("km", "---")

            volt = current_telemetry.get("battery_voltage", 0.0)
            rpm = current_telemetry.get("rpm", 0)
            map_kpa = current_telemetry.get("map_kpa", 0)
            temp = current_telemetry.get("coolant_temp", 0)
            stft = current_telemetry.get("stft_b1", 0.0)
            ltft = current_telemetry.get("ltft_b1", 0.0)
            o2 = current_telemetry.get("o2_b1s1", 0.0)
            tps = current_telemetry.get("tps", 0.0)

            dtcs_str = "Nenhum código de falha ativo no momento."
            if dtcs:
                dtcs_str = "\n".join([f"• {d.get('code')}: {d.get('description')}" for d in dtcs])

            system_context = f"""
Você é um Especialista Sênior em Autoelétrica e Injeção Eletrônica Automotiva, auxiliando um mecânico/eletricista em sua oficina.

DADOS DO VEÍCULO CONECTADO NO ELEVADOR:
- Veículo / Motor: {veh_name} (Placa: {plate} | KM: {km})
- Códigos de Falha Ativos (DTC):
{dtcs_str}

TELEMETRIA ATUAL LIDA PELO SCANNER EM TEMPO REAL:
- Tensão da Bateria / Alternador (Linha 30/15): {volt:.1f} V
- Rotação do Motor: {rpm} RPM
- Vácuo / Pressão no Coletor (MAP): {map_kpa} kPa
- Temperatura do Motor: {temp} °C
- Sonda Lambda (O2 Pré): {o2:.2f} V
- Posição da Borboleta (TPS): {tps:.1f} %
- Ajustes de Combustível: Curto Prazo (STFT) {stft:+.1f}% | Longo Prazo (LTFT) {ltft:+.1f}%

PERGUNTA DO ELETRICISTA / MECÂNICO:
"{question}"

INSTRUÇÕES PARA SUA RESPOSTA:
1. Responda como um técnico experiente de oficina elétrica automotiva, direto e objetivo.
2. Analise os dados de telemetria atuais (ex: se a tensão estiver abaixo de 13.5V com motor ligado, aponte defeito no alternador/regulador de voltagem; se o MAP estiver alto, aponte entradas de ar ou ponto; se o LTFT estiver alto, aponte linha de combustível ou vácuo).
3. Forneça um PASSO A PASSO PRÁTICO de testes com:
   - Multímetro (onde colocar ponta preta no terra e ponta vermelha no pino/conector, e qual valor em Volts ou Ohms esperar).
   - Queda de tensão nas massas / aterramentos do motor e chassi (teste de 0.2V máximo).
   - Relés e fusíveis daquele circuito.
4. Conclua com o diagnóstico mais provável e a peça a substituir ou reparar.
"""

            # Ordem de tentativa: o escolhido pelo usuário primeiro, depois fallback nos outros gratuitos
            models_to_try = []
            if preferred_model and preferred_model in ElectricalAIAssistant.FREE_MODELS:
                models_to_try.append(preferred_model)
            for m in ["gemini-3.8-flash", "gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-2.0-flash"]:
                if m not in models_to_try:
                    models_to_try.append(m)

            last_err = None
            for m in models_to_try:
                try:
                    response = client.models.generate_content(
                        model=m,
                        contents=system_context
                    )
                    if response and response.text:
                        return f"[{m}] {response.text}"
                except Exception as ex:
                    last_err = ex
                    time.sleep(0.5)
                    continue

            return f"Instabilidade momentânea nos servidores da Google. Tente novamente em alguns segundos. (Detalhes: {last_err})"
        except Exception as e:
            return f"Erro ao consultar Gemini AI: {e}"

    @staticmethod
    def generate_vehicle_tolerances(car_model_query, gemini_key="", preferred_model=None):
        """Usa a IA para pesquisar e extrair os valores nominais de fábrica de qualquer motor em formato JSON estruturado"""
        key = gemini_key or os.environ.get("GEMINI_API_KEY", "")
        if not key:
            return None, "Chave do Google Gemini não configurada. Configure na barra lateral."

        try:
            from google import genai
            client = genai.Client(api_key=key)

            prompt = f"""
Você é um Engenheiro Mecânico e Especialista em Injeção Eletrônica Automotiva.
Pesquise as especificações técnicas e tolerâncias de fábrica NOMINAIS para o seguinte veículo / motor:
"{car_model_query}"

Retorne ESTRITAMENTE E APENAS um objeto JSON válido (sem blocos markdown ```json, sem comentários, somente o JSON puro) com a seguinte estrutura:

{{
  "name": "Nome Completo com Motor (ex: Fiat Pulse 1.0 Turbo 200 Flex)",
  "category": "Tipo do Motor (ex: 3 Cilindros 12V Turbo Flex)",
  "tolerances": {{
    "idle_rpm": {{"min": 780, "max": 880, "unit": "RPM", "desc": "Marcha Lenta Operacional"}},
    "idle_map": {{"min": 28, "max": 38, "unit": "kPa", "desc": "Vácuo no Coletor em Lenta (Aquecido > 85°C)"}},
    "coolant_temp": {{"min": 86, "max": 102, "unit": "°C", "desc": "Faixa Térmica Ideal"}},
    "idle_tps": {{"min": 10.0, "max": 16.5, "unit": "%", "desc": "Abertura Borboleta em Lenta"}},
    "fuel_trim_total": {{"min": -8.0, "max": 8.0, "unit": "%", "desc": "Ajuste de Combustível Total Ideal"}},
    "lambda_o2": {{"min": 0.09, "max": 0.88, "unit": "V", "desc": "Oscilação Contínua Pré-Catalisador"}},
    "battery_voltage": {{"min": 13.5, "max": 14.8, "unit": "V", "desc": "Tensão com Alternador Carregando"}}
  }},
  "tips": [
    "Dica mecânica prática ou defeito característico mais comum desse motor na oficina."
  ]
}}
"""
            models_to_try = []
            if preferred_model and preferred_model in ElectricalAIAssistant.FREE_MODELS:
                models_to_try.append(preferred_model)
            for m in ["gemini-3.8-flash", "gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-2.0-flash"]:
                if m not in models_to_try:
                    models_to_try.append(m)

            last_err = None
            for m in models_to_try:
                try:
                    resp = client.models.generate_content(
                        model=m,
                        contents=prompt
                    )
                    raw_text = resp.text.strip()
                    if "```" in raw_text:
                        import re
                        m_re = re.search(r"\{.*\}", raw_text, re.DOTALL)
                        if m_re:
                            raw_text = m_re.group(0)

                    data = json.loads(raw_text)
                    return data, "OK"
                except Exception as ex:
                    last_err = ex
                    time.sleep(0.5)
                    continue

            return None, f"Erro ao gerar com IA: {last_err}"
        except Exception as e:
            return None, f"Erro ao gerar com IA: {e}"

