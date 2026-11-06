"""
Banco de Dados de Modelos, Motores e Tolerâncias Nominais de Fábrica.
Inclui valores de referência para marcha lenta, temperatura, vácuo MAP e fuel trims,
além de guias didáticos de diagnóstico e leitura mecânica para a frota brasileira.
"""

import os
import json

CUSTOM_PROFILES_PATH = os.path.join(os.path.expanduser("~"), ".autoscan_custom_tolerances.json")

def load_all_vehicle_profiles():
    """Carrega os perfis embutidos e mescla com quaisquer perfis ou calibrações personalizadas salvas pelo usuário"""
    profiles = dict(VEHICLE_PROFILES_DATABASE)
    if os.path.exists(CUSTOM_PROFILES_PATH):
        try:
            with open(CUSTOM_PROFILES_PATH, "r", encoding="utf-8") as f:
                custom = json.load(f)
                profiles.update(custom)
        except Exception as e:
            print(f"Erro ao carregar calibrações customizadas: {e}")
    return profiles

def save_custom_profile(model_key, profile_data):
    """Salva ou atualiza um perfil no arquivo JSON de customizações do usuário"""
    custom = {}
    if os.path.exists(CUSTOM_PROFILES_PATH):
        try:
            with open(CUSTOM_PROFILES_PATH, "r", encoding="utf-8") as f:
                custom = json.load(f)
        except Exception:
            pass
    custom[model_key] = profile_data
    try:
        with open(CUSTOM_PROFILES_PATH, "w", encoding="utf-8") as f:
            json.dump(custom, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Erro ao salvar calibração personalizada: {e}")
        return False

def delete_custom_profile(model_key):
    """Remove uma calibração customizada, restaurando o padrão original se existir"""
    if os.path.exists(CUSTOM_PROFILES_PATH):
        try:
            with open(CUSTOM_PROFILES_PATH, "r", encoding="utf-8") as f:
                custom = json.load(f)
            if model_key in custom:
                del custom[model_key]
                with open(CUSTOM_PROFILES_PATH, "w", encoding="utf-8") as f:
                    json.dump(custom, f, indent=2, ensure_ascii=False)
                return True
        except Exception:
            pass
    return False

VEHICLE_PROFILES_DATABASE = {
    # =========================================================================
    # 1. CHEVROLET / GM
    # =========================================================================
    "GM_CELTA_CORSA_VHC": {
        "name": "Chevrolet Celta / Classic / Corsa / Prisma 1.0 e 1.4 8V VHC / VHC-E",
        "category": "8V Flex Aspirado (Alta Compressão)",
        "tolerances": {
            "idle_rpm": {"min": 820, "max": 920, "unit": "RPM", "desc": "Marcha Lenta Operacional VHC"},
            "idle_map": {"min": 34, "max": 45, "unit": "kPa", "desc": "Vácuo em Lenta (Motor aquecido > 85°C)"},
            "coolant_temp": {"min": 88, "max": 102, "unit": "°C", "desc": "Temperatura Normal (Ventoinha arma ~98-101°C)"},
            "idle_tps": {"min": 0.0, "max": 12.0, "unit": "%", "desc": "Posição Borboleta a Cabo / Passo"},
            "fuel_trim_total": {"min": -8.0, "max": 8.0, "unit": "%", "desc": "Ajuste de Combustível Total"},
            "lambda_o2": {"min": 0.08, "max": 0.88, "unit": "V", "desc": "Oscilação Sonda Lambda"},
            "battery_voltage": {"min": 13.5, "max": 14.6, "unit": "V", "desc": "Alternador Carregando"}
        },
        "tips": [
            "Motor VHC possui taxa de compressão alta (12.6:1). Combustível adulterado causa detonação forte e retardo de ponto.",
            "Falhas em marcha lenta: limpe o atuador de marcha lenta (IAC) e teste a mangueira do sensor MAP quanto a trincas."
        ]
    },
    "GM_FAMILIA_1_10_14": {
        "name": "Chevrolet Onix / Prisma / Spin / Cobalt 1.0, 1.4 e 1.8 8V SPE/4",
        "category": "8V Flex Aspirado",
        "tolerances": {
            "idle_rpm": {"min": 780, "max": 860, "unit": "RPM", "desc": "Marcha Lenta Operacional"},
            "idle_map": {"min": 32, "max": 42, "unit": "kPa", "desc": "Vácuo no Coletor em Lenta"},
            "coolant_temp": {"min": 88, "max": 102, "unit": "°C", "desc": "Faixa Térmica Normal"},
            "idle_tps": {"min": 11.0, "max": 16.5, "unit": "%", "desc": "Abertura Borboleta Eletrônica em Lenta"},
            "fuel_trim_total": {"min": -8.0, "max": 8.0, "unit": "%", "desc": "Ajuste de Combustível Total"},
            "lambda_o2": {"min": 0.08, "max": 0.90, "unit": "V", "desc": "Oscilação Lambda"},
            "battery_voltage": {"min": 13.5, "max": 14.7, "unit": "V", "desc": "Carga Alternador"}
        },
        "tips": [
            "Bobina de ignição de 4 saídas costuma queimar um par (cilindros 1-4 ou 2-3) e gerar código P0300.",
            "Válvula de purga do canister travada aberta puxa vapor em excesso e faz o carro afogar na partida após abastecer."
        ]
    },
    "GM_TURBO_10_12_ONIX": {
        "name": "Chevrolet Onix / Onix Plus / Tracker / Montana 1.0 e 1.2 12V Turbo CSS Prime",
        "category": "3 Cilindros 12V Turbo Flex",
        "tolerances": {
            "idle_rpm": {"min": 800, "max": 900, "unit": "RPM", "desc": "Marcha Lenta Operacional (3 Cilindros)"},
            "idle_map": {"min": 32, "max": 42, "unit": "kPa", "desc": "Vácuo no Coletor em Lenta"},
            "coolant_temp": {"min": 86, "max": 103, "unit": "°C", "desc": "Temperatura Operacional"},
            "idle_tps": {"min": 11.0, "max": 17.0, "unit": "%", "desc": "Borboleta em Lenta"},
            "fuel_trim_total": {"min": -8.0, "max": 8.0, "unit": "%", "desc": "Ajuste de Combustível Total"},
            "lambda_o2": {"min": 0.10, "max": 0.88, "unit": "V", "desc": "Oscilação Lambda"},
            "battery_voltage": {"min": 13.5, "max": 14.7, "unit": "V", "desc": "Alternador Pilotado (Linha LIN/PWM)"}
        },
        "tips": [
            "Possui correia banhada a óleo. O uso de óleo fora da especificação Dexos1 Gen2/Gen3 esfarela a correia e entope o pescador de óleo.",
            "Alternador pilotado via PWM pelo módulo: oscilação de 13.2V a 14.7V em rodagem é comportamento normal de gerenciamento de carga."
        ]
    },
    "GM_CRUZE_TRACKER_14T": {
        "name": "Chevrolet Cruze / Tracker 1.4 16V Turbo Ecotec SIDI Flex",
        "category": "4 Cilindros 16V Turbo Injeção Direta",
        "tolerances": {
            "idle_rpm": {"min": 700, "max": 800, "unit": "RPM", "desc": "Marcha Lenta Suave"},
            "idle_map": {"min": 32, "max": 41, "unit": "kPa", "desc": "Vácuo Coletor em Lenta"},
            "coolant_temp": {"min": 88, "max": 104, "unit": "°C", "desc": "Temperatura Ideal"},
            "idle_tps": {"min": 10.0, "max": 15.5, "unit": "%", "desc": "Posição Borboleta Lenta"},
            "fuel_trim_total": {"min": -7.0, "max": 7.0, "unit": "%", "desc": "Ajuste Combustível Injeção Direta"},
            "lambda_o2": {"min": 0.08, "max": 0.88, "unit": "V", "desc": "Sonda Lambda Linear"},
            "battery_voltage": {"min": 13.6, "max": 14.8, "unit": "V", "desc": "Alternador Inteligente AGM"}
        },
        "tips": [
            "Membrana da tampa de válvulas (válvula PCV) rasgada gera ruído estridente de sucção e código P0171 (mistura muito pobre).",
            "Bomba de alta pressão de combustível deve marcar acima de 3.5 MPa em lenta e até 15-20 MPa em aceleração plena."
        ]
    },

    # =========================================================================
    # 2. VOLKSWAGEN
    # =========================================================================
    "VW_EA111_10_16": {
        "name": "Volkswagen Gol / Fox / Voyage / Saveiro 1.0 e 1.6 8V EA111",
        "category": "8V Flex Aspirado",
        "tolerances": {
            "idle_rpm": {"min": 780, "max": 860, "unit": "RPM", "desc": "Marcha Lenta Operacional"},
            "idle_map": {"min": 32, "max": 42, "unit": "kPa", "desc": "Vácuo no Coletor em Lenta (Motor quente)"},
            "coolant_temp": {"min": 87, "max": 102, "unit": "°C", "desc": "Faixa Térmica Normal"},
            "idle_tps": {"min": 11.0, "max": 16.0, "unit": "%", "desc": "Abertura Borboleta TPS em Lenta"},
            "fuel_trim_total": {"min": -8.0, "max": 8.0, "unit": "%", "desc": "Ajuste de Combustível Total"},
            "lambda_o2": {"min": 0.08, "max": 0.88, "unit": "V", "desc": "Oscilação Lambda"},
            "battery_voltage": {"min": 13.5, "max": 14.6, "unit": "V", "desc": "Tensão Alternador Carregando"}
        },
        "tips": [
            "Campeão histórico de oficina. Atenção ao tubo d'água traseiro ressecado e sensor de rotação traseiro no retentor da árvore de manivelas.",
            "TBI sujo faz o carro apagar em reduções de marcha e o TPS subir acima de 19% em lenta."
        ]
    },
    "VW_EA211_10_16": {
        "name": "Volkswagen Gol / Voyage / Fox / Polo / Up! 1.0 12V e 1.6 16V EA211 MPI",
        "category": "3/4 Cilindros 12V/16V Flex",
        "tolerances": {
            "idle_rpm": {"min": 780, "max": 870, "unit": "RPM", "desc": "Marcha Lenta Operacional (3 cilindros tem lenta ligeiramente mais alta)"},
            "idle_map": {"min": 28, "max": 36, "unit": "kPa", "desc": "Vácuo no Coletor em Lenta"},
            "coolant_temp": {"min": 85, "max": 104, "unit": "°C", "desc": "Faixa Térmica Ideal"},
            "idle_tps": {"min": 10.0, "max": 16.0, "unit": "%", "desc": "Abertura Borboleta em Lenta"},
            "fuel_trim_total": {"min": -7.0, "max": 7.0, "unit": "%", "desc": "Ajuste de Combustível Total"},
            "lambda_o2": {"min": 0.10, "max": 0.85, "unit": "V", "desc": "Oscilação Lambda"},
            "battery_voltage": {"min": 13.5, "max": 14.6, "unit": "V", "desc": "Tensão Alternador"}
        },
        "tips": [
            "Motores 1.0 3 cilindros possuem vibração natural em lenta, mas o LTFT não pode fugir de ±7% no combustível padrão.",
            "Atenção à carcaça da válvula termostática dupla típica da família EA211 que costuma trincar."
        ]
    },
    "VW_TSI_EA211_10_14": {
        "name": "Volkswagen Polo / Virtus / T-Cross / Nivus / Taos 1.0 e 1.4 TSI EA211",
        "category": "Turbo Injeção Direta (200 TSI / 250 TSI)",
        "tolerances": {
            "idle_rpm": {"min": 780, "max": 880, "unit": "RPM", "desc": "Marcha Lenta Operacional (3 Cilindros)"},
            "idle_map": {"min": 34, "max": 44, "unit": "kPa", "desc": "Pressão Coletor em Lenta (Injeção Direta com comando duplo)"},
            "coolant_temp": {"min": 88, "max": 105, "unit": "°C", "desc": "Faixa Térmica Ideal (Trabalha quente)"},
            "idle_tps": {"min": 10.0, "max": 16.0, "unit": "%", "desc": "Abertura Borboleta em Lenta"},
            "fuel_trim_total": {"min": -7.0, "max": 7.0, "unit": "%", "desc": "Ajuste de Combustível Total"},
            "lambda_o2": {"min": 0.10, "max": 0.85, "unit": "V", "desc": "Sonda Banda Larga / Linear"},
            "battery_voltage": {"min": 13.6, "max": 14.8, "unit": "V", "desc": "Alternador Inteligente (Start-Stop)"}
        },
        "tips": [
            "Motores TSI possuem Start-Stop e bateria EFB/AGM. Queda de tensão abaixo de 12.0V desativa o Start-Stop.",
            "Atenção à carcaça da bomba d'água com acionamento por correia dentada traseira e vazamento crônico de líquido."
        ]
    },
    "VW_AMAROK_20_30_TDI": {
        "name": "Volkswagen Amarok 2.0 TDI Biturbo e 3.0 V6 TDI Diesel",
        "category": "Turbo Diesel Common Rail 4x4",
        "tolerances": {
            "idle_rpm": {"min": 650, "max": 750, "unit": "RPM", "desc": "Marcha Lenta Diesel"},
            "idle_map": {"min": 96, "max": 104, "unit": "kPa", "desc": "Pressão Coletor Diesel em Lenta (~Barométrica)"},
            "coolant_temp": {"min": 82, "max": 96, "unit": "°C", "desc": "Temperatura Operacional"},
            "idle_tps": {"min": 0.0, "max": 5.0, "unit": "%", "desc": "Pedal do Acelerador em Repouso"},
            "fuel_trim_total": {"min": -4.0, "max": 4.0, "unit": "%", "desc": "Balanço de Débito dos Injetores"},
            "lambda_o2": {"min": 0.0, "max": 1.0, "unit": "V", "desc": "Sensor O2 / NOx Diesel"},
            "battery_voltage": {"min": 13.6, "max": 14.8, "unit": "V", "desc": "Linha Elétrica de Alta Capacidade"}
        },
        "tips": [
            "Amarok 2.0: Troca rigorosa da correia dentada e esticador (risco de quebra com danos graves ao cabeçote).",
            "Bomba de alta pressão Bosch CP4 exige diesel S10 de qualidade para não limalhar e contaminar todo o sistema de injeção."
        ]
    },

    # =========================================================================
    # 3. FIAT / JEEP (STELLANTIS)
    # =========================================================================
    "FIAT_FIRE_8V": {
        "name": "Fiat Uno / Palio / Siena / Strada / Mobi 1.0 e 1.4 8V Fire EVO",
        "category": "8V Flex Aspirado",
        "tolerances": {
            "idle_rpm": {"min": 780, "max": 860, "unit": "RPM", "desc": "Marcha Lenta Operacional"},
            "idle_map": {"min": 32, "max": 42, "unit": "kPa", "desc": "Vácuo no Coletor em Lenta"},
            "coolant_temp": {"min": 86, "max": 99, "unit": "°C", "desc": "Faixa Térmica Normal"},
            "idle_tps": {"min": 11.5, "max": 17.0, "unit": "%", "desc": "Borboleta em Lenta"},
            "fuel_trim_total": {"min": -8.0, "max": 8.0, "unit": "%", "desc": "Ajuste de Combustível Total"},
            "lambda_o2": {"min": 0.10, "max": 0.88, "unit": "V", "desc": "Oscilação Sonda"},
            "battery_voltage": {"min": 13.5, "max": 14.6, "unit": "V", "desc": "Carga Alternador"}
        },
        "tips": [
            "No motor Fire, cabo de vela com alta resistência ou bobina dupla fraca faz o Short Trim flutuar bruscamente tentando compensar queima incompleta.",
            "Aterramento deficiente no câmbio/carroceria causa leitura louca de temperatura no painel."
        ]
    },
    "FIAT_FIREFLY_10_13": {
        "name": "Fiat Argo / Cronos / Strada / Pulse / Mobi 1.0 6V e 1.3 8V Firefly",
        "category": "3/4 Cilindros Corrente de Comando Flex",
        "tolerances": {
            "idle_rpm": {"min": 780, "max": 860, "unit": "RPM", "desc": "Marcha Lenta Operacional"},
            "idle_map": {"min": 28, "max": 38, "unit": "kPa", "desc": "Vácuo Coletor Firefly"},
            "coolant_temp": {"min": 86, "max": 102, "unit": "°C", "desc": "Faixa Térmica Normal"},
            "idle_tps": {"min": 10.0, "max": 16.0, "unit": "%", "desc": "Posição Borboleta Lenta"},
            "fuel_trim_total": {"min": -7.0, "max": 7.0, "unit": "%", "desc": "Ajuste Combustível Total"},
            "lambda_o2": {"min": 0.10, "max": 0.88, "unit": "V", "desc": "Sonda Lambda Linear"},
            "battery_voltage": {"min": 13.5, "max": 14.7, "unit": "V", "desc": "Alternador Inteligente"}
        },
        "tips": [
            "Possui comando variável com variador de fase acionado por pressão de óleo. Óleo errado (0W20 especificado) acende luz de injeção.",
            "Consumo excessivo de óleo nos primeiros lotes: verificar compressão e vedação das hastes de válvulas."
        ]
    },
    "FIAT_ETORQ_16_18": {
        "name": "Fiat Palio / Punto / Bravo / Strada / Toro / Renegade 1.6 e 1.8 16V E.torQ",
        "category": "16V Aspirado Corrente de Comando",
        "tolerances": {
            "idle_rpm": {"min": 780, "max": 860, "unit": "RPM", "desc": "Marcha Lenta Operacional"},
            "idle_map": {"min": 28, "max": 37, "unit": "kPa", "desc": "Vácuo em Lenta"},
            "coolant_temp": {"min": 86, "max": 102, "unit": "°C", "desc": "Temperatura Ideal"},
            "idle_tps": {"min": 11.5, "max": 17.5, "unit": "%", "desc": "Borboleta em Lenta"},
            "fuel_trim_total": {"min": -8.0, "max": 8.0, "unit": "%", "desc": "Ajuste de Combustível Total"},
            "lambda_o2": {"min": 0.09, "max": 0.89, "unit": "V", "desc": "Oscilação Lambda"},
            "battery_voltage": {"min": 13.5, "max": 14.6, "unit": "V", "desc": "Tensão Carga Alternador"}
        },
        "tips": [
            "Atenção ao sensor de temperatura d'água na carcaça plástica e vazamento no trocador de calor do câmbio automático.",
            "Corrente de comando silenciosa, mas óleo carbonizado costuma travar o tensor hidráulico."
        ]
    },
    "FIAT_JEEP_TURBO_T270": {
        "name": "Fiat Pulse / Fastback / Toro / Jeep Renegade / Compass 1.3 Turbo GSE T270",
        "category": "4 Cilindros 16V Turbo MultiAir III Flex",
        "tolerances": {
            "idle_rpm": {"min": 750, "max": 850, "unit": "RPM", "desc": "Marcha Lenta Operacional"},
            "idle_map": {"min": 30, "max": 40, "unit": "kPa", "desc": "Vácuo em Marcha Lenta"},
            "coolant_temp": {"min": 88, "max": 105, "unit": "°C", "desc": "Faixa Térmica Normal"},
            "idle_tps": {"min": 10.0, "max": 16.0, "unit": "%", "desc": "Posição Borboleta Lenta"},
            "fuel_trim_total": {"min": -7.0, "max": 7.0, "unit": "%", "desc": "Ajuste Combustível Total"},
            "lambda_o2": {"min": 0.08, "max": 0.88, "unit": "V", "desc": "Sonda Lambda Linear"},
            "battery_voltage": {"min": 13.6, "max": 14.8, "unit": "V", "desc": "Alternador Inteligente IBS"}
        },
        "tips": [
            "Possui sistema MultiAir hidráulico no comando de admissão. Óleo correto e nível rigoroso são vitais para o atuador eletro-hidráulico.",
            "Possui sensor de corrente de bateria IBS no borne negativo. Testes de bateria devem ser feitos após o sensor para não descalibrar a BCM."
        ]
    },
    "JEEP_TORO_20_DIESEL": {
        "name": "Jeep Renegade / Compass / Commander / Fiat Toro 2.0 16V MultiJet II Turbo Diesel",
        "category": "Turbo Diesel Common Rail 4x4 Intercooler",
        "tolerances": {
            "idle_rpm": {"min": 750, "max": 850, "unit": "RPM", "desc": "Marcha Lenta Diesel"},
            "idle_map": {"min": 96, "max": 103, "unit": "kPa", "desc": "Pressão Coletor Diesel em Lenta (~Atmosférica)"},
            "coolant_temp": {"min": 82, "max": 98, "unit": "°C", "desc": "Temperatura Ideal Operacional"},
            "idle_tps": {"min": 0.0, "max": 5.0, "unit": "%", "desc": "Acelerador Eletrônico em Repouso"},
            "fuel_trim_total": {"min": -5.0, "max": 5.0, "unit": "%", "desc": "Correção Individual de Injeção"},
            "lambda_o2": {"min": 0.0, "max": 1.0, "unit": "V", "desc": "Sensor Banda Larga / Nox"},
            "battery_voltage": {"min": 13.6, "max": 14.7, "unit": "V", "desc": "Alternador Heavy Duty"}
        },
        "tips": [
            "Troca do trocador de calor da transmissão automática preventiva: corrosão interna mistura água com o fluído do câmbio destruindo as embreagens.",
            "Regeneração do DPF: quando o carro faz muitos trajetos curtos na cidade, o DPF satura e eleva o nível de óleo no cárter por injeção tardia."
        ]
    },

    # =========================================================================
    # 4. FORD
    # =========================================================================
    "FORD_ROCAM_10_16": {
        "name": "Ford Fiesta / Ka / Ecosport / Courier 1.0 e 1.6 8V Zetec Rocam",
        "category": "8V Corrente de Comando",
        "tolerances": {
            "idle_rpm": {"min": 800, "max": 900, "unit": "RPM", "desc": "Marcha Lenta Operacional"},
            "idle_map": {"min": 32, "max": 42, "unit": "kPa", "desc": "Vácuo em Lenta"},
            "coolant_temp": {"min": 88, "max": 103, "unit": "°C", "desc": "Faixa Térmica (Termostática com refil plástico)"},
            "idle_tps": {"min": 12.0, "max": 18.0, "unit": "%", "desc": "Posição Borboleta Lenta"},
            "fuel_trim_total": {"min": -8.0, "max": 8.0, "unit": "%", "desc": "Ajuste de Combustível Total"},
            "lambda_o2": {"min": 0.08, "max": 0.88, "unit": "V", "desc": "Oscilação Lambda"},
            "battery_voltage": {"min": 13.5, "max": 14.6, "unit": "V", "desc": "Tensão Alternador"}
        },
        "tips": [
            "Carcaça da válvula termostática plástica é o ponto fraco crônico (recomenda-se carcaça de alumínio).",
            "Válvula de marcha lenta (IAC / atuador passo) suja faz o carro oscilar ou morrer em paradas de semáforo."
        ]
    },
    "FORD_SIGMA_15_16": {
        "name": "Ford New Fiesta / Ka / Focus / Ecosport 1.5 e 1.6 16V Sigma Flex",
        "category": "16V Aspirado Duplo Comando",
        "tolerances": {
            "idle_rpm": {"min": 750, "max": 830, "unit": "RPM", "desc": "Marcha Lenta Operacional"},
            "idle_map": {"min": 26, "max": 35, "unit": "kPa", "desc": "Vácuo no Coletor em Lenta (Motor aquecido > 85°C)"},
            "coolant_temp": {"min": 86, "max": 102, "unit": "°C", "desc": "Faixa Térmica Ideal (Termostática abre aos ~88°C)"},
            "idle_tps": {"min": 12.0, "max": 17.5, "unit": "%", "desc": "Abertura Borboleta em Marcha Lenta"},
            "fuel_trim_total": {"min": -8.0, "max": 8.0, "unit": "%", "desc": "Ajuste de Combustível Total Ideal (LTFT + STFT)"},
            "lambda_o2": {"min": 0.08, "max": 0.88, "unit": "V", "desc": "Oscilação Contínua Pré-Catalisador"},
            "battery_voltage": {"min": 13.5, "max": 14.8, "unit": "V", "desc": "Tensão com Alternador Carregando (Smart Charge Ford)"}
        },
        "tips": [
            "Se o MAP em marcha lenta estiver acima de 38 kPa no motor Sigma, quase sempre é entrada falsa de ar na mangueira do respiro do cárter ou correia dentada 1 dente fora.",
            "O Sigma trabalha aquecido: o eletroventilador 1ª velocidade liga entre 98°C e 102°C."
        ]
    },
    "FORD_KA_10_3CIL": {
        "name": "Ford Ka / Ka+ / Ecosport 1.0 12V 3 Cilindros Ti-VCT Flex",
        "category": "3 Cilindros 12V Ti-VCT Flex",
        "tolerances": {
            "idle_rpm": {"min": 800, "max": 900, "unit": "RPM", "desc": "Marcha Lenta 3 Cilindros"},
            "idle_map": {"min": 28, "max": 37, "unit": "kPa", "desc": "Vácuo Coletor em Lenta"},
            "coolant_temp": {"min": 86, "max": 102, "unit": "°C", "desc": "Faixa Térmica Operacional"},
            "idle_tps": {"min": 10.5, "max": 16.5, "unit": "%", "desc": "Posição Borboleta Lenta"},
            "fuel_trim_total": {"min": -7.0, "max": 7.0, "unit": "%", "desc": "Ajuste Combustível Total"},
            "lambda_o2": {"min": 0.10, "max": 0.88, "unit": "V", "desc": "Oscilação Sonda Lambda"},
            "battery_voltage": {"min": 13.6, "max": 14.8, "unit": "V", "desc": "Sistema de Carga Inteligente"}
        },
        "tips": [
            "Possui correia dentada banhada a óleo. Usar estritamente o óleo Ford WSS-M2C948-B (5W20). Óleo incorreto esfarela a correia e funde o motor.",
            "Vaso de expansão e tampa com válvula ressecam e causam perda de pressão e superaquecimento."
        ]
    },

    # =========================================================================
    # 5. HYUNDAI
    # =========================================================================
    "HYUNDAI_HB20_KAPPA": {
        "name": "Hyundai HB20 / Creta 1.0 12V Kappa e 1.6 16V Gamma Flex",
        "category": "12V / 16V Flex Aspirado",
        "tolerances": {
            "idle_rpm": {"min": 700, "max": 820, "unit": "RPM", "desc": "Marcha Lenta Suave"},
            "idle_map": {"min": 26, "max": 34, "unit": "kPa", "desc": "Vácuo no Coletor em Lenta"},
            "coolant_temp": {"min": 85, "max": 98, "unit": "°C", "desc": "Temperatura Operacional"},
            "idle_tps": {"min": 10.0, "max": 15.0, "unit": "%", "desc": "Posição Borboleta Lenta"},
            "fuel_trim_total": {"min": -7.0, "max": 7.0, "unit": "%", "desc": "Ajuste Combustível Total"},
            "lambda_o2": {"min": 0.09, "max": 0.88, "unit": "V", "desc": "Sonda Lambda"},
            "battery_voltage": {"min": 13.5, "max": 14.6, "unit": "V", "desc": "Alternador"}
        },
        "tips": [
            "Motor Kappa tem vácuo excelente de 26 a 32 kPa quando saudável. Qualquer valor acima de 38 kPa indica perda de vedação de válvulas.",
            "Bobinas de ignição individuais são duráveis, mas velas gastas além de 40.000 km queimam o estágio de acionamento na ECU."
        ]
    },
    "HYUNDAI_HB20_CRETA_TGDI": {
        "name": "Hyundai HB20 / Creta 1.0 12V Turbo TGDI Flex",
        "category": "3 Cilindros 12V Turbo Injeção Direta",
        "tolerances": {
            "idle_rpm": {"min": 750, "max": 850, "unit": "RPM", "desc": "Marcha Lenta Turbo"},
            "idle_map": {"min": 32, "max": 42, "unit": "kPa", "desc": "Pressão Coletor em Lenta"},
            "coolant_temp": {"min": 86, "max": 100, "unit": "°C", "desc": "Temperatura Operacional"},
            "idle_tps": {"min": 10.0, "max": 16.0, "unit": "%", "desc": "Abertura Borboleta em Lenta"},
            "fuel_trim_total": {"min": -6.0, "max": 6.0, "unit": "%", "desc": "Ajuste Combustível Injeção Direta"},
            "lambda_o2": {"min": 0.10, "max": 0.88, "unit": "V", "desc": "Sonda Lambda Linear"},
            "battery_voltage": {"min": 13.6, "max": 14.7, "unit": "V", "desc": "Alternador Inteligente (ISG)"}
        },
        "tips": [
            "Carbonização nas válvulas de admissão é comum em injeção direta: descarbonização com casca de noz ou química a cada 50.000 km.",
            "Velas de ignição são especiais (irídio com rosca longa): torque de aperto incorreto quebra a cerâmica."
        ]
    },

    # =========================================================================
    # 6. HONDA & TOYOTA (JAPONESES)
    # =========================================================================
    "HONDA_FIT_CIVIC_IVTEC": {
        "name": "Honda Civic / Fit / City / HR-V 1.5, 1.8 e 2.0 i-VTEC Flex",
        "category": "16V i-VTEC Corrente de Comando",
        "tolerances": {
            "idle_rpm": {"min": 650, "max": 750, "unit": "RPM", "desc": "Marcha Lenta Baixa e Silenciosa"},
            "idle_map": {"min": 25, "max": 33, "unit": "kPa", "desc": "Vácuo em Lenta"},
            "coolant_temp": {"min": 82, "max": 96, "unit": "°C", "desc": "Temperatura Ideal"},
            "idle_tps": {"min": 10.0, "max": 14.5, "unit": "%", "desc": "Abertura Borboleta Lenta"},
            "fuel_trim_total": {"min": -6.0, "max": 6.0, "unit": "%", "desc": "Ajuste Estequiométrico Estrito"},
            "lambda_o2": {"min": 0.10, "max": 0.85, "unit": "V", "desc": "Oscilação Lambda"},
            "battery_voltage": {"min": 13.5, "max": 14.5, "unit": "V", "desc": "Sistema ELD (Dual Mode Charge)"}
        },
        "tips": [
            "Motores Honda possuem sensor ELD (Electronic Load Detector). É normal o alternador baixar a voltagem para 12.6V em rodagem quando não há consumo elétrico ativo.",
            "Necessitam de regulagem mecânica de folga de válvulas a cada 40.000 km. Válvula enforcada altera o vácuo MAP e faz o motor tremer em D no semáforo."
        ]
    },
    "TOYOTA_COROLLA_ETIOS": {
        "name": "Toyota Corolla / Etios / Yaris 1.3, 1.5, 1.8 e 2.0 Dual VVT-i",
        "category": "16V Dual VVT-i Flex",
        "tolerances": {
            "idle_rpm": {"min": 650, "max": 750, "unit": "RPM", "desc": "Marcha Lenta"},
            "idle_map": {"min": 26, "max": 35, "unit": "kPa", "desc": "Vácuo em Lenta"},
            "coolant_temp": {"min": 85, "max": 97, "unit": "°C", "desc": "Temperatura Operacional"},
            "idle_tps": {"min": 11.0, "max": 15.5, "unit": "%", "desc": "Borboleta em Lenta"},
            "fuel_trim_total": {"min": -6.0, "max": 6.0, "unit": "%", "desc": "Ajuste de Combustível Total"},
            "lambda_o2": {"min": 0.10, "max": 0.88, "unit": "V", "desc": "Oscilação Sonda"},
            "battery_voltage": {"min": 13.5, "max": 14.6, "unit": "V", "desc": "Carga Alternador"}
        },
        "tips": [
            "Linha Toyota opera com trims extremamente estáveis (±4%). Sujeira no sensor MAF/MAP causa enriquecimento falso.",
            "Bomba d'água mecânica externa costuma apresentar resíduo cor-de-rosa de aditivo aos ~90.000 km antes de folgar."
        ]
    },
    "TOYOTA_HILUX_DIESEL_1GD": {
        "name": "Toyota Hilux / SW4 2.8 16V Turbo Diesel 1GD-FTV (Common Rail)",
        "category": "Turbo Diesel Common Rail DPF",
        "tolerances": {
            "idle_rpm": {"min": 700, "max": 800, "unit": "RPM", "desc": "Marcha Lenta Diesel Suave"},
            "idle_map": {"min": 95, "max": 105, "unit": "kPa", "desc": "Pressão Coletor Diesel (Sem borboleta fechada na lenta)"},
            "coolant_temp": {"min": 82, "max": 96, "unit": "°C", "desc": "Temperatura Diesel Normal"},
            "idle_tps": {"min": 0.0, "max": 5.0, "unit": "%", "desc": "Acelerador Eletrônico em Repouso"},
            "fuel_trim_total": {"min": -5.0, "max": 5.0, "unit": "%", "desc": "Compensação de Injeção por Cilindro"},
            "lambda_o2": {"min": 0.0, "max": 1.0, "unit": "V", "desc": "Sensor O2 / NOx Banda Larga"},
            "battery_voltage": {"min": 13.6, "max": 14.6, "unit": "V", "desc": "Alternador Pesado Linha Hilux"}
        },
        "tips": [
            "Veículo Diesel não trabalha com vácuo alto no coletor na lenta (o MAP fica próximo à pressão atmosférica ~100 kPa).",
            "Atenção ao sistema DPF (filtro de partículas): regenerações forçadas frequentes indicam bico gotejando ou sensor de pressão diferencial sujo."
        ]
    },
    "NISSAN_16_HR16DE": {
        "name": "Nissan Kicks / Versa / March 1.6 16V HR16DE Flex",
        "category": "16V Aspirado Japonês",
        "tolerances": {
            "idle_rpm": {"min": 650, "max": 750, "unit": "RPM", "desc": "Marcha Lenta Baixa e Estável"},
            "idle_map": {"min": 25, "max": 34, "unit": "kPa", "desc": "Vácuo no Coletor em Lenta"},
            "coolant_temp": {"min": 84, "max": 98, "unit": "°C", "desc": "Temperatura Ideal"},
            "idle_tps": {"min": 10.0, "max": 15.0, "unit": "%", "desc": "Abertura Borboleta em Lenta"},
            "fuel_trim_total": {"min": -6.0, "max": 6.0, "unit": "%", "desc": "Ajuste de Combustível Total"},
            "lambda_o2": {"min": 0.10, "max": 0.85, "unit": "V", "desc": "Oscilação Sonda"},
            "battery_voltage": {"min": 13.5, "max": 14.6, "unit": "V", "desc": "Alternador com Gerenciamento"}
        },
        "tips": [
            "TBI eletrônico da Nissan é sensível: após limpeza, é obrigatório fazer o aprendizado de volume de ar da marcha lenta via scanner.",
            "Bobinas de ignição individuais costumam apresentar fuga de centelha no cachimbo após 80.000 km."
        ]
    },

    # =========================================================================
    # 7. RENAULT & PEUGEOT / CITROËN
    # =========================================================================
    "RENAULT_SCE_10_16": {
        "name": "Renault Sandero / Logan / Kwid / Stepway 1.0 12V e 1.6 16V SCe Flex",
        "category": "3/4 Cilindros SCe Flex Corrente",
        "tolerances": {
            "idle_rpm": {"min": 780, "max": 880, "unit": "RPM", "desc": "Marcha Lenta"},
            "idle_map": {"min": 28, "max": 37, "unit": "kPa", "desc": "Vácuo no Coletor em Lenta"},
            "coolant_temp": {"min": 84, "max": 99, "unit": "°C", "desc": "Temperatura Ideal"},
            "idle_tps": {"min": 11.0, "max": 16.5, "unit": "%", "desc": "Borboleta em Lenta"},
            "fuel_trim_total": {"min": -8.0, "max": 8.0, "unit": "%", "desc": "Ajuste de Combustível Total"},
            "lambda_o2": {"min": 0.10, "max": 0.88, "unit": "V", "desc": "Oscilação Lambda"},
            "battery_voltage": {"min": 13.5, "max": 14.6, "unit": "V", "desc": "Carga Alternador"}
        },
        "tips": [
            "Nos motores SCe 3 cilindros, o sensor de fase com folga ou atuador do comando variável gera lenta instável e erro de correlação P0016.",
            "No Kwid SCe, vazamento crônico de fluido na carcaça plástica da termostática."
        ]
    },
    "RENAULT_K4M_F4R": {
        "name": "Renault Duster / Oroch / Sandero / Megane 1.6 16V K4M e 2.0 16V F4R",
        "category": "16V Correia Dentada Flex",
        "tolerances": {
            "idle_rpm": {"min": 750, "max": 850, "unit": "RPM", "desc": "Marcha Lenta"},
            "idle_map": {"min": 30, "max": 38, "unit": "kPa", "desc": "Vácuo Coletor em Lenta"},
            "coolant_temp": {"min": 86, "max": 100, "unit": "°C", "desc": "Temperatura Ideal"},
            "idle_tps": {"min": 12.0, "max": 17.5, "unit": "%", "desc": "Abertura Borboleta"},
            "fuel_trim_total": {"min": -8.0, "max": 8.0, "unit": "%", "desc": "Ajuste Total Combustível"},
            "lambda_o2": {"min": 0.08, "max": 0.88, "unit": "V", "desc": "Oscilação Sonda"},
            "battery_voltage": {"min": 13.5, "max": 14.6, "unit": "V", "desc": "Tensão Alternador"}
        },
        "tips": [
            "Vedação do coletor de admissão resseca facilmente nos K4M gerando entrada de ar falsa violenta e lenta acelerada a 1.500 RPM.",
            "Polia do virabrequim (damper com borracha vulcanizada) que descola causa perda de sincronismo de acessórios."
        ]
    },
    "PSA_16_EC5_TU5": {
        "name": "Peugeot 208 / 2008 & Citroën C3 / C4 Cactus / Aircross 1.6 16V EC5 / TU5JP4",
        "category": "16V Flex Aspirado Francês",
        "tolerances": {
            "idle_rpm": {"min": 750, "max": 850, "unit": "RPM", "desc": "Marcha Lenta Operacional"},
            "idle_map": {"min": 28, "max": 38, "unit": "kPa", "desc": "Vácuo no Coletor em Lenta"},
            "coolant_temp": {"min": 88, "max": 104, "unit": "°C", "desc": "Faixa Térmica (Trabalha quente)"},
            "idle_tps": {"min": 10.5, "max": 16.0, "unit": "%", "desc": "Borboleta em Lenta"},
            "fuel_trim_total": {"min": -7.0, "max": 7.0, "unit": "%", "desc": "Ajuste Combustível Total"},
            "lambda_o2": {"min": 0.10, "max": 0.88, "unit": "V", "desc": "Oscilação Sonda"},
            "battery_voltage": {"min": 13.6, "max": 14.6, "unit": "V", "desc": "Alimentação BSI / Alternador"}
        },
        "tips": [
            "Bobina de ignição em bloco inteiriço com módulo integrado: quando uma saída falha, queima o driver interno na ECU se não for trocada rápido.",
            "Carcaça termostática plástica com sensor de temperatura integrado costuma vazar água para dentro do conector elétrico da ECU por capilaridade."
        ]
    },
    "PSA_16_THP_TURBO": {
        "name": "Peugeot 208 / 2008 / 3008 & Citroën C4 Lounge / DS3 1.6 16V THP Turbo",
        "category": "Turbo Injeção Direta (BMW Prince)",
        "tolerances": {
            "idle_rpm": {"min": 700, "max": 800, "unit": "RPM", "desc": "Marcha Lenta Suave"},
            "idle_map": {"min": 32, "max": 42, "unit": "kPa", "desc": "Vácuo em Lenta"},
            "coolant_temp": {"min": 90, "max": 106, "unit": "°C", "desc": "Temperatura THP (Eletroventilador arma ~105°C)"},
            "idle_tps": {"min": 10.0, "max": 15.0, "unit": "%", "desc": "Abertura Borboleta"},
            "fuel_trim_total": {"min": -6.0, "max": 6.0, "unit": "%", "desc": "Ajuste Injeção Direta"},
            "lambda_o2": {"min": 0.10, "max": 0.85, "unit": "V", "desc": "Sonda Linear Banda Larga"},
            "battery_voltage": {"min": 13.6, "max": 14.7, "unit": "V", "desc": "Gerenciamento Elétrico"}
        },
        "tips": [
            "Bomba de alta pressão de combustível (HPFP): sintoma típico de perda de potência em subida e código P0087 (pressão do rail muito baixa).",
            "Tensor hidráulico da corrente de comando: folga gera ruído matinal metálico antes de desregular o sincronismo de válvulas."
        ]
    },

    # =========================================================================
    # 8. CAOA CHERY
    # =========================================================================
    "CHERY_TIGGO_15_16_TURBO": {
        "name": "Caoa Chery Tiggo 5X / Tiggo 7 Pro / Arrizo 6 1.5 e 1.6 Turbo Flex / 48V",
        "category": "Turbo Flex / Híbrido Leve MHEV",
        "tolerances": {
            "idle_rpm": {"min": 750, "max": 850, "unit": "RPM", "desc": "Marcha Lenta Operacional"},
            "idle_map": {"min": 30, "max": 40, "unit": "kPa", "desc": "Vácuo Coletor em Lenta"},
            "coolant_temp": {"min": 86, "max": 102, "unit": "°C", "desc": "Temperatura Ideal"},
            "idle_tps": {"min": 10.0, "max": 15.5, "unit": "%", "desc": "Posição Borboleta Lenta"},
            "fuel_trim_total": {"min": -7.0, "max": 7.0, "unit": "%", "desc": "Ajuste de Combustível"},
            "lambda_o2": {"min": 0.10, "max": 0.88, "unit": "V", "desc": "Oscilação Lambda"},
            "battery_voltage": {"min": 13.6, "max": 14.6, "unit": "V", "desc": "Linha 12V e Conversor 48V (se híbrido)"}
        },
        "tips": [
            "Nos modelos 48V Híbrido Leve, a bateria 48V sob o banco regenera energia de frenagem e alimenta o motor de partida/gerador (BSG).",
            "Atenção ao fluído e trocador de calor do câmbio CVT ou DCT de dupla embreagem banhada a óleo."
        ]
    },

    # =========================================================================
    # 9. VEÍCULOS HÍBRIDOS (HEV / PHEV)
    # =========================================================================
    "BYD_SONG_PLUS_DM_I": {
        "name": "BYD Song Plus DM-i / King DM-i Super Híbrido Plug-in (PHEV)",
        "category": "Híbrido Plug-in (PHEV) Motor 1.5 Atkinson + Motor Elétrico Blade",
        "tolerances": {
            "idle_rpm": {"min": 0, "max": 950, "unit": "RPM", "desc": "0 RPM no modo elétrico puro EV | ~900 RPM no modo gerador HEV"},
            "idle_map": {"min": 35, "max": 45, "unit": "kPa", "desc": "MAP quando motor térmico 1.5 está ligado"},
            "coolant_temp": {"min": 75, "max": 95, "unit": "°C", "desc": "Circuito Arrefecimento Motor 1.5 e Inversor"},
            "idle_tps": {"min": 0.0, "max": 10.0, "unit": "%", "desc": "Posição Borboleta / Acelerador"},
            "fuel_trim_total": {"min": -6.0, "max": 6.0, "unit": "%", "desc": "Ajuste Combustível Motor 1.5"},
            "lambda_o2": {"min": 0.10, "max": 0.85, "unit": "V", "desc": "Sonda Lambda Linear"},
            "battery_voltage": {"min": 13.8, "max": 14.6, "unit": "V", "desc": "Tensão da Rede 12V Mantida pelo Conversor DC-DC Interno"}
        },
        "tips": [
            "Campeão absoluto de vendas entre os híbridos plug-in no Brasil. O motor 1.5 funciona a maior parte do tempo apenas como gerador elétrico para carregar a bateria de tração Blade.",
            "A bateria auxiliar de 12V LFP fica sob o capô: se descarregar por consumo de acessórios com o carro desligado, o veículo não liga o sistema de alta tensão.",
            "Nunca realize testes de continuidade em cabos laranjas (alta tensão até 400V DC). Use sempre EPIs adequados."
        ]
    },
    "TOYOTA_COROLLA_CROSS_HYBRID": {
        "name": "Toyota Corolla e Corolla Cross 1.8 16V Hybrid Flex (Atkinson)",
        "category": "Híbrido Flex Ciclo Atkinson (HEV)",
        "tolerances": {
            "idle_rpm": {"min": 0, "max": 1000, "unit": "RPM", "desc": "0 RPM em EV | ~960 RPM no ciclo Atkinson carregando tração"},
            "idle_map": {"min": 35, "max": 46, "unit": "kPa", "desc": "MAP Ciclo Atkinson (Trabalha com retardo de válvulas e MAP maior)"},
            "coolant_temp": {"min": 82, "max": 95, "unit": "°C", "desc": "Temperatura Ideal Arrefecimento"},
            "idle_tps": {"min": 11.0, "max": 16.5, "unit": "%", "desc": "Posição Borboleta Lenta"},
            "fuel_trim_total": {"min": -6.0, "max": 6.0, "unit": "%", "desc": "Ajuste Combustível Estequiométrico"},
            "lambda_o2": {"min": 0.10, "max": 0.85, "unit": "V", "desc": "Sonda Lambda Linear A/F"},
            "battery_voltage": {"min": 13.8, "max": 14.5, "unit": "V", "desc": "Linha 12V Mantida pelo Inversor DC-DC"}
        },
        "tips": [
            "O motor 1.8 Atkinson tem vácuo no coletor MAP diferente de motores normais (36 a 44 kPa em operação é perfeitamente normal).",
            "Bateria de 12V fica no porta-malas ou sob o capô: se descarregar (<10.5V), o sistema híbrido não arma o relé principal de alta tensão."
        ]
    },
    "GWM_HAVAL_H6_HYBRID": {
        "name": "GWM Haval H6 / ORA 03 Híbrido HEV e PHEV / EV",
        "category": "Híbrido Dedicado (DHT) / 100% Elétrico",
        "tolerances": {
            "idle_rpm": {"min": 0, "max": 850, "unit": "RPM", "desc": "0 RPM no modo elétrico | 800 RPM quando motor a combustão liga"},
            "idle_map": {"min": 30, "max": 42, "unit": "kPa", "desc": "Vácuo Coletor quando motor a combustão está acionado"},
            "coolant_temp": {"min": 75, "max": 96, "unit": "°C", "desc": "Circuito Arrefecimento Motor e Sistema Híbrido"},
            "idle_tps": {"min": 0.0, "max": 12.0, "unit": "%", "desc": "Posição Borboleta / Acelerador"},
            "fuel_trim_total": {"min": -6.0, "max": 6.0, "unit": "%", "desc": "Ajuste de Combustível do Motor 1.5 Turbo"},
            "lambda_o2": {"min": 0.10, "max": 0.85, "unit": "V", "desc": "Sonda Lambda Linear"},
            "battery_voltage": {"min": 13.6, "max": 14.6, "unit": "V", "desc": "Alimentação 12V dos Sistemas Eletrônicos (DC-DC)"}
        },
        "tips": [
            "No trânsito urbano, o motor a combustão desliga com frequência (0 RPM). Não confunda com parada anômala do motor.",
            "Falhas de isolamento elétrico no inversor acendem alerta de perigo no painel e cortam a tração por segurança."
        ]
    },
    "VOLVO_RECHARGE_T8_EV": {
        "name": "Volvo XC40 / XC60 / XC90 Recharge T8 Híbrido Plug-in e Pure Electric",
        "category": "PHEV Híbrido Plug-in / 100% Elétrico Puro",
        "tolerances": {
            "idle_rpm": {"min": 0, "max": 850, "unit": "RPM", "desc": "0 RPM em Pure EV | 800 RPM em Hybrid com motor 2.0 ativo"},
            "idle_map": {"min": 32, "max": 42, "unit": "kPa", "desc": "Vácuo do Coletor quando motor a combustão está ligado"},
            "coolant_temp": {"min": 78, "max": 96, "unit": "°C", "desc": "Arrefecimento dos Módulos Eletrônicos e Motor"},
            "idle_tps": {"min": 0.0, "max": 10.0, "unit": "%", "desc": "Acelerador Eletrônico em Repouso"},
            "fuel_trim_total": {"min": -5.0, "max": 5.0, "unit": "%", "desc": "Ajuste de Combustível Injeção Direta"},
            "lambda_o2": {"min": 0.10, "max": 0.85, "unit": "V", "desc": "Sonda Lambda Linear"},
            "battery_voltage": {"min": 13.8, "max": 14.6, "unit": "V", "desc": "Rede Elétrica 12V / Conversor DC-DC"}
        },
        "tips": [
            "Módulo ERAD (Electric Rear Axle Drive) aciona o eixo traseiro de forma 100% elétrica. Atenção a ruídos de rolamento no motor elétrico traseiro.",
            "Módulo OBC (On-Board Charger) com falha impede recarga em corrente alternada (AC Wallbox). Testar aterramento da tomada residencial."
        ]
    },

    # =========================================================================
    # 10. VEÍCULOS 100% ELÉTRICOS (BEV)
    # =========================================================================
    "BYD_DOLPHIN_MINI_EV": {
        "name": "BYD Dolphin / Dolphin Mini / Yuan Plus / Seal 100% Elétrico (BEV)",
        "category": "100% Elétrico (BEV) Bateria Blade LFP",
        "tolerances": {
            "idle_rpm": {"min": 0, "max": 0, "unit": "RPM", "desc": "Motor Elétrico em Repouso (0 RPM parado)"},
            "idle_map": {"min": 95, "max": 103, "unit": "kPa", "desc": "Pressão Barométrica Atmosférica"},
            "coolant_temp": {"min": 25, "max": 55, "unit": "°C", "desc": "Temperatura Arrefecimento Inversor/Bateria"},
            "idle_tps": {"min": 0.0, "max": 2.0, "unit": "%", "desc": "Pedal do Acelerador em Repouso"},
            "fuel_trim_total": {"min": 0.0, "max": 0.0, "unit": "%", "desc": "Não se aplica a veículo 100% elétrico"},
            "lambda_o2": {"min": 0.0, "max": 0.0, "unit": "V", "desc": "Não se aplica a veículo 100% elétrico"},
            "battery_voltage": {"min": 13.6, "max": 14.5, "unit": "V", "desc": "Tensão da Bateria Auxiliar 12V (Carregada via Conversor DC-DC)"}
        },
        "tips": [
            "⚡ SISTEMA DE ALTA TENSÃO (Cabos Laranjas): Nunca toque ou meça cabos laranjas sem luva classe 0 (1.000V) e procedimento de desativação (Manual Service Disconnect - MSD).",
            "A bateria auxiliar de 12V tradicional (chumbo/ácido ou LFP 12V) alimenta os módulos OBD2 e travas. Se a 12V zerar, o carro 'morre' e não arma a bateria de alta tração.",
            "O conversor DC-DC interno substitui o alternador e deve manter a linha 12V entre 13.8V e 14.4V com o carro no modo 'READY'."
        ]
    },
    "RENAULT_KWID_E_TECH": {
        "name": "Renault Kwid E-Tech / Megane E-Tech 100% Elétrico (BEV)",
        "category": "100% Elétrico Compacto Urbano (BEV)",
        "tolerances": {
            "idle_rpm": {"min": 0, "max": 0, "unit": "RPM", "desc": "Motor Síncrono Elétrico em Repouso"},
            "idle_map": {"min": 95, "max": 102, "unit": "kPa", "desc": "Pressão Barométrica Local"},
            "coolant_temp": {"min": 20, "max": 50, "unit": "°C", "desc": "Faixa Térmica do Pack de Baterias"},
            "idle_tps": {"min": 0.0, "max": 2.0, "unit": "%", "desc": "Pedal do Acelerador em Repouso"},
            "fuel_trim_total": {"min": 0.0, "max": 0.0, "unit": "%", "desc": "Não aplicável a veículos 100% elétricos"},
            "lambda_o2": {"min": 0.0, "max": 0.0, "unit": "V", "desc": "Não aplicável a veículos 100% elétricos"},
            "battery_voltage": {"min": 13.5, "max": 14.5, "unit": "V", "desc": "Alimentação 12V (Conversor DC-DC)"}
        },
        "tips": [
            "Bateria de tração refrigerada a ar ou líquido: verifique sempre se há vazamento no radiador inferior da bateria.",
            "Qualquer intervenção na rede 12V (troca de bateria auxiliar) deve ser feita com a ignição completamente desligada e chave fora do veículo."
        ]
    },
    "NISSAN_LEAF_EV": {
        "name": "Nissan Leaf 100% Elétrico (BEV)",
        "category": "100% Elétrico Puro (BEV)",
        "tolerances": {
            "idle_rpm": {"min": 0, "max": 0, "unit": "RPM", "desc": "Motor Elétrico em Repouso"},
            "idle_map": {"min": 95, "max": 102, "unit": "kPa", "desc": "Pressão Barométrica Atmosférica"},
            "coolant_temp": {"min": 20, "max": 48, "unit": "°C", "desc": "Temperatura Bateria e Inversor"},
            "idle_tps": {"min": 0.0, "max": 2.0, "unit": "%", "desc": "Pedal em Repouso"},
            "fuel_trim_total": {"min": 0.0, "max": 0.0, "unit": "%", "desc": "Não aplicável"},
            "lambda_o2": {"min": 0.0, "max": 0.0, "unit": "V", "desc": "Não aplicável"},
            "battery_voltage": {"min": 13.6, "max": 14.5, "unit": "V", "desc": "Tensão Linha 12V (Conversor DC-DC)"}
        },
        "tips": [
            "Bateria do Leaf possui degradação térmica natural por não ter refrigeração líquida ativa nos primeiros modelos. Monitore o SOH (State of Health).",
            "Bateria de 12V pequena na dianteira: quando perde capacidade, gera erros fantasmas de frenagem e freio de estacionamento elétrico."
        ]
    },

    # =========================================================================
    # 11. GENÉRICO UNIVERSAL
    # =========================================================================
    "GENERIC_OBD2": {
        "name": "Padrão Universal OBD-II (Genérico Multimarcas)",
        "category": "Genérico",
        "tolerances": {
            "idle_rpm": {"min": 700, "max": 900, "unit": "RPM", "desc": "Marcha Lenta Geral"},
            "idle_map": {"min": 27, "max": 42, "unit": "kPa", "desc": "Vácuo Médio no Coletor"},
            "coolant_temp": {"min": 82, "max": 103, "unit": "°C", "desc": "Temperatura Operacional"},
            "idle_tps": {"min": 10.0, "max": 19.0, "unit": "%", "desc": "Abertura em Marcha Lenta"},
            "fuel_trim_total": {"min": -10.0, "max": 10.0, "unit": "%", "desc": "Tolerância Padrão Global"},
            "lambda_o2": {"min": 0.10, "max": 0.85, "unit": "V", "desc": "Chaveamento Lambda"},
            "battery_voltage": {"min": 13.5, "max": 14.8, "unit": "V", "desc": "Tensão Alternador Carregando"}
        },
        "tips": [
            "Use o modo genérico caso o veículo em teste não conste na lista específica de calibração.",
            "Você também pode clicar em '✨ Gerar com IA' para criar uma calibração exata de qualquer modelo e motorização do mundo."
        ]
    }
}

DIAGNOSTIC_HELP_GUIDE = """
========================================================================================
            AUTOSCAN BR — GUIA TÉCNICO DE LEITURA & DIAGNÓSTICO VEICULAR
========================================================================================

1. AJUSTES DE COMBUSTÍVEL (SHORT TERM & LONG TERM FUEL TRIM - STFT / LTFT)
----------------------------------------------------------------------------------------
O que é: O termômetro definitivo da saúde da injeção eletrônica.
• Zero (0.0%): Mistura estequiométrica perfeita calculada pela fábrica.
• Faixa Normal Aceitável: Entre -8% e +8% (a soma de STFT + LTFT não deve passar de ±10%).
• Ajuste Muito Positivo (> +12% até +25%):
  A ECU está detectando excesso de oxigênio na exaustão e adicionando combustível extra.
  -> Causas Comuns: Entrada falsa de ar (vácuo furado, junta do coletor ressecada, servo-freio),
     bicos injetores entupidos/gotejando mal, filtro de combustível obstruído ou baixa pressão na bomba.
• Ajuste Muito Negativo (< -12% até -25%):
  A ECU está cortando combustível porque há excesso de combustível na queima.
  -> Causas Comuns: Bico travado aberto, regulador de pressão travado em alta pressão,
     válvula de purga do canister travada aberta sugando vapores do tanque sem controle.

2. PRESSÃO ABSOLUTA NO COLETOR (SENSOR MAP)
----------------------------------------------------------------------------------------
O que é: Mede o vácuo gerado pelos pistões ao admitir ar.
• Em Marcha Lenta (com motor 100% aquecido > 85°C e sem ar-condicionado):
  - Motores 16V modernos: 26 a 35 kPa.
  - Motores 8V tradicionais: 32 a 42 kPa.
• Com Ignição Ligada e Motor Desligado:
  - Deve marcar ~95 a 101 kPa (a pressão atmosférica local ao nível do mar).
• Sintomas de Problema:
  - MAP marcando acima de 45 kPa em marcha lenta indica perda de vácuo mecânico
    (correia/corrente fora de ponto, válvulas presas/carbonizadas ou entrada falsa de ar).

3. TEMPERATURA DO LÍQUIDO DE ARREFECIMENTO (COOLANT TEMP)
----------------------------------------------------------------------------------------
• Faixa Ideal de Trabalho: 86°C a 98°C.
• Diagnóstico em Rodagem (Test-Drive):
  - Se você acelerar o carro na rodovia e a temperatura cair para 70°C ou menos, a VÁLVULA
    TERMOSTÁTICA está travada aberta ou foi removida. O motor trabalha frio, gasta 15% a mais
    de combustível e carboniza o óleo prematuramente.
  - Se passar de 103°C no trânsito pesado sem que a ventoinha ligue, perigo iminente de junta de cabeçote.

4. SONDA LAMBDA PRÉ-CATALISADOR (O2 B1S1)
----------------------------------------------------------------------------------------
• O que analisar: Chaveamento constante de tensão entre 0.10V (mistura pobre) e 0.90V (mistura rica).
• Frequência: Deve oscilar pelo menos 1 a 2 vezes por segundo em rotação constante.
• Se ficar travada em linha reta (ex: fixa em 0.45V): Sonda fria, desconectada ou queimada.
• Se responder devagar às acelerações: Sonda contaminada por combustível adulterado ou óleo.

5. POSIÇÃO DA BORBOLETA (TPS)
----------------------------------------------------------------------------------------
• Em Marcha Lenta: Normalmente entre 11% e 17%.
• Aceleração Plena (WOT): Deve atingir entre 80% e 100%.
• Sintoma: Se a borboleta estiver acima de 22% em marcha lenta, corpo TBI muito carbonizado
  necessitando de descarbonização química.

6. VEÍCULOS HÍBRIDOS (HEV/PHEV) E 100% ELÉTRICOS (EV)
----------------------------------------------------------------------------------------
• 0 RPM em repouso é NORMAL (motor elétrico não possui marcha lenta de combustão).
• Linha de 12V: Mantida pelo conversor DC-DC interno a partir do banco de alta tensão (deve indicar 13.6V a 14.5V no modo READY).
• Atenção aos cabos laranjas: Alta tensão (200V a 800V DC). Nunca perfure cabos laranjas.
========================================================================================
"""
