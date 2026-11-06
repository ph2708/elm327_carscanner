"""
Módulo de Diagnóstico Dinâmico de Test-Drive e Análise de Parâmetros
Compara leituras nominais da injeção, arrefecimento e combustão durante a rodagem.
Gera relatórios automáticos e integra com Google Gemini AI.
"""

import os
import time
import json
import numpy as np

class TestDriveDiagnosticAnalyzer:
    @staticmethod
    def analyze_session(frames):
        """
        Recebe a lista de frames coletados durante o test-drive e gera a análise técnica
        """
        if not frames or len(frames) < 5:
            return {
                "status": "DADOS_INSUFICIENTES",
                "message": "Poucos dados coletados durante o test-drive (mínimo 5 segundos de rodagem)."
            }

        # Extrai séries
        rpms = [f.get("rpm", 0) for f in frames]
        speeds = [f.get("speed", 0) for f in frames]
        coolants = [f.get("coolant_temp", 0) for f in frames]
        maps = [f.get("map_kpa", 0) for f in frames]
        tps_list = [f.get("tps", 0) for f in frames]
        stfts = [f.get("stft_b1", 0) for f in frames]
        ltfts = [f.get("ltft_b1", 0) for f in frames]
        o2_list = [f.get("o2_b1s1", 0.45) for f in frames]

        duration_sec = len(frames) * 0.2 # estimado
        max_speed = float(np.max(speeds))
        avg_speed = float(np.mean(speeds))
        max_rpm = float(np.max(rpms))
        avg_rpm = float(np.mean(rpms))
        min_coolant = float(np.min(coolants))
        max_coolant = float(np.max(coolants))

        avg_stft = float(np.mean(stfts))
        avg_ltft = float(np.mean(ltfts))
        total_trim = avg_ltft + avg_stft

        anomalies = []
        health_score = 100

        # 1. Análise de Combustível / Injeção (LTFT + STFT)
        fuel_status = "PERFEITO (Dentro da Tolerância Nominal)"
        if total_trim > 12.0:
            fuel_status = "MISTURA POBRE EXCESSIVA (ECU enriquecendo muito)"
            health_score -= 25
            anomalies.append({
                "sistema": "Alimentação / Injeção",
                "gravidade": "ALTA",
                "titulo": "Ajuste de Combustível Positivo Elevado (+{:.1f}%)".format(total_trim),
                "descricao": "A ECU está sendo forçada a injetar combustível extra. Causas prováveis: Entrada falsa de ar no coletor/vácuo, bicos injetores parcialmente entupidos ou pressão de linha da bomba de combustível abaixo da especificação."
            })
        elif total_trim < -12.0:
            fuel_status = "MISTURA RICA EXCESSIVA (ECU empobrecendo muito)"
            health_score -= 25
            anomalies.append({
                "sistema": "Alimentação / Injeção",
                "gravidade": "ALTA",
                "titulo": "Ajuste de Combustível Negativo Excessivo ({:.1f}%)".format(total_trim),
                "descricao": "A ECU está cortando injeção porque há combustível demais. Causas prováveis: Bico travado aberto, sensor MAP descalibrado indicando carga excessiva ou canister saturado/válvula purga travada aberta."
            })

        # 2. Análise do Sistema de Arrefecimento
        cooling_status = "NORMAL (Temperatura Estável)"
        if max_coolant > 105.0:
            cooling_status = "ALERTA DE SUPERAQUECIMENTO"
            health_score -= 30
            anomalies.append({
                "sistema": "Arrefecimento",
                "gravidade": "CRÍTICA",
                "titulo": f"Pico de Temperatura Alta ({max_coolant:.1f}°C)",
                "descricao": "O motor operou acima do limite térmico seguro. Verificar nível de líquido no reservatório, acionamento do eletroventilador (1ª e 2ª velocidade) e estado do radiador."
            })
        elif max_speed > 60.0 and min_coolant < 75.0:
            cooling_status = "VÁLVULA TERMOSTÁTICA INEFICIENTE"
            health_score -= 15
            anomalies.append({
                "sistema": "Arrefecimento",
                "gravidade": "MÉDIA",
                "titulo": f"Queda Anormal de Temperatura em Rodagem ({min_coolant:.1f}°C)",
                "descricao": "Com o fluxo de vento em velocidade, o motor esfriou além do ideal. Forte indício de válvula termostática travada aberta ou ausente, aumentando o consumo de combustível e desgaste interno."
            })

        # 3. Análise da Sonda Lambda (O2)
        o2_variance = float(np.var(o2_list))
        lambda_status = "NORMAL (Chaveamento Ativo)"
        if o2_variance < 0.005 and len(o2_list) > 20:
            lambda_status = "SONDA LAMBDA LENTA / TRAVADA"
            health_score -= 20
            anomalies.append({
                "sistema": "Exaustão / Emissões",
                "gravidade": "ALTA",
                "titulo": "Variação Insuficiente na Sonda Lambda",
                "descricao": "A sonda de oxigênio pré-catalisador apresentou pouca oscilação durante o percurso. Sensor envelhecido/contaminado que não responde rápido às transições de mistura rica/pobre."
            })

        health_score = max(10, min(100, health_score))

        return {
            "status": "CONCLUIDO",
            "health_score": health_score,
            "duration_sec": int(duration_sec),
            "samples_count": len(frames),
            "metrics": {
                "max_speed": max_speed,
                "avg_speed": avg_speed,
                "max_rpm": max_rpm,
                "avg_rpm": avg_rpm,
                "min_coolant": min_coolant,
                "max_coolant": max_coolant,
                "avg_stft": avg_stft,
                "avg_ltft": avg_ltft,
                "total_fuel_trim": total_trim
            },
            "subsystems": {
                "combustivel": fuel_status,
                "arrefecimento": cooling_status,
                "sonda_lambda": lambda_status
            },
            "anomalies": anomalies
        }

    @staticmethod
    def generate_ai_report(analysis_data, api_key=None):
        """
        Gera parecer pericial completo com IA Gemini
        """
        key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if not key:
            return "Chave do Google Gemini não configurada. Insira sua chave gratuita nas configurações para gerar laudos explicativos com IA."

        try:
            from google import genai
            client = genai.Client(api_key=key)

            prompt = f"""
Você é um Engenheiro Mecânico Automotivo especialista em diagnóstico veicular avançado OBD-II e telemetria.
Analise os seguintes dados coletados após um Test-Drive real no veículo:

RESUMO DA RODAGEM:
- Score de Saúde do Motor: {analysis_data['health_score']}/100
- Duração do Teste: {analysis_data['duration_sec']} segundos ({analysis_data['samples_count']} amostras gravadas)
- Velocidade Máxima: {analysis_data['metrics']['max_speed']:.1f} km/h (Média: {analysis_data['metrics']['avg_speed']:.1f} km/h)
- RPM Máximo: {analysis_data['metrics']['max_rpm']:.0f} RPM (Média: {analysis_data['metrics']['avg_rpm']:.0f} RPM)
- Temperatura Água: Mín {analysis_data['metrics']['min_coolant']:.1f}°C | Máx {analysis_data['metrics']['max_coolant']:.1f}°C
- Ajuste de Combustível Total (LTFT + STFT): {analysis_data['metrics']['total_fuel_trim']:+.1f}% (Longo Prazo: {analysis_data['metrics']['avg_ltft']:+.1f}%)
- Status dos Subsistemas:
  • Sistema de Combustível: {analysis_data['subsystems']['combustivel']}
  • Sistema de Arrefecimento: {analysis_data['subsystems']['arrefecimento']}
  • Sonda Lambda: {analysis_data['subsystems']['sonda_lambda']}

ANOMALIAS DETECTADAS:
{json.dumps(analysis_data['anomalies'], indent=2, ensure_ascii=False)}

Por favor, elabore um LAUDO TÉCNICO PROFISSIONAL contendo:
1. Parecer Geral da Condição do Veículo.
2. Explicação Didática dos Problemas e Riscos Mecânicos caso não corrigidos.
3. Testes de Bancada recomendados para a oficina (Ex: teste de estanqueidade, máquina de fumaça, pressão da bomba, multímetro na sonda).
4. Veredito final: Aprovado para uso imediato ou requer intervenção preventiva/corretiva.
"""
            models_to_try = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-3.8-flash"]
            for m in models_to_try:
                try:
                    response = client.models.generate_content(
                        model=m,
                        contents=prompt
                    )
                    if response and response.text:
                        return response.text
                except Exception:
                    time.sleep(0.5)
                    continue

            return "Instabilidade temporária nos servidores do Gemini AI. Tente novamente em alguns segundos."
        except Exception as e:
            return f"Erro ao consultar Gemini AI: {e}"

