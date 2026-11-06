"""
AutoScan BR - Simulador de ECU / Adaptador ELM327
Emula os comandos AT fundamentais e os PIDs OBD-II (Modo 01, 02, 03, 07 e 09)
com suporte ao perfil Ford New Fiesta 1.5 16V Sigma Flex.
"""

import math
import time
import random

class ELM327Simulator:
    def __init__(self, vehicle_profile="fiesta_1_5"):
        self.profile = vehicle_profile
        self.echo = False
        self.linefeeds = False
        self.protocol = "6"  # ISO 15765-4 (CAN 11/500)
        self.headers_on = False
        self.start_time = time.time()
        
        # Estado dinâmico do motor para simulação
        self.state = {
            "rpm": 820.0,
            "speed": 0.0,
            "coolant_temp": 88.0,  # Graus Celsius
            "intake_temp": 32.0,   # Graus Celsius
            "map_kpa": 32.0,       # kPa típico motor Sigma
            "tps": 13.0,           # Porcentagem borboleta
            "stft_b1": 1.2,        # %
            "ltft_b1": 4.5,        # %
            "o2_b1s1": 0.45,       # Volts (0.1 a 0.9V)
            "battery_voltage": 14.1, # Volts (Alternador carregando)
            "throttle_moving": True,
            "dtcs": ["P0171"]      # Simula falha de mistura pobre
        }

    def update_dynamic_state(self):
        """Atualiza os valores dos sensores simulando a dinâmica real do motor"""
        elapsed = time.time() - self.start_time
        
        # Simula variação sutil de marcha lenta e oscilação de aceleração cíclica
        cycle = math.sin(elapsed * 0.5)
        if cycle > 0:
            # Aceleração leve simulada
            self.state["rpm"] = 820.0 + (cycle * 1800.0)
            self.state["speed"] = max(0.0, cycle * 45.0)
            self.state["map_kpa"] = 32.0 + (cycle * 25.0)
            self.state["tps"] = 13.0 + (cycle * 22.0)
        else:
            # Marcha lenta suave
            jitter = random.uniform(-15.0, 15.0)
            self.state["rpm"] = 820.0 + jitter
            self.state["speed"] = 0.0
            self.state["map_kpa"] = 31.0 + random.uniform(-1.0, 1.0)
            self.state["tps"] = 13.0

        # Temperatura do arrefecimento subindo até ~92C
        self.state["coolant_temp"] = min(92.0, 75.0 + (elapsed * 0.15))
        
        # Sonda Lambda ciclando entre pobre e rica (0.1V a 0.85V)
        self.state["o2_b1s1"] = 0.48 + 0.38 * math.sin(elapsed * 3.0)

        # Parâmetros secundários (carga, avanço, módulo, sonda pós-catalisador, MAF)
        load_factor = max(0.0, cycle)
        self.state["engine_load"] = round(22.0 + load_factor * 45.0 + random.uniform(-1.5, 1.5), 1)
        self.state["timing_advance"] = round(12.0 + load_factor * 18.0 + random.uniform(-1.0, 1.0), 1)
        self.state["battery_voltage"] = round(14.1 + random.uniform(-0.08, 0.08), 2)
        self.state["ecu_voltage"] = round(self.state["battery_voltage"] - 0.25, 2)
        self.state["o2_b1s2"] = round(0.66 + random.uniform(-0.03, 0.03), 3)
        self.state["maf_gs"] = round(3.1 + load_factor * 16.0, 2)
        self.state["fuel_level"] = 62.0
        self.state["baro_kpa"] = 95.0

    def process_command(self, cmd_raw: str) -> str:
        """Processa comando AT ou comando hexadecimal OBD"""
        cmd = cmd_raw.strip().replace(" ", "").upper()
        if not cmd:
            return ""

        self.update_dynamic_state()

        # Comandos AT do ELM327
        if cmd.startswith("AT"):
            return self._handle_at_command(cmd)

        # Comandos OBD-II (Hexadecimal)
        return self._handle_obd_command(cmd)

    def _handle_at_command(self, cmd: str) -> str:
        if cmd == "ATZ" or cmd == "ATWS":
            return "\r\nELM327 v1.5\r\n>"
        elif cmd == "ATE0":
            self.echo = False
            return "OK\r\n>"
        elif cmd == "ATE1":
            self.echo = True
            return "OK\r\n>"
        elif cmd == "ATL0":
            self.linefeeds = False
            return "OK\r\n>"
        elif cmd == "ATH0":
            self.headers_on = False
            return "OK\r\n>"
        elif cmd == "ATH1":
            self.headers_on = True
            return "OK\r\n>"
        elif cmd.startswith("ATSP"):
            self.protocol = cmd[4:] if len(cmd) > 4 else "6"
            return "OK\r\n>"
        elif cmd == "ATDP":
            return "ISO 15765-4 (CAN 11/500)\r\n>"
        elif cmd == "ATDPN":
            return "6\r\n>"
        elif cmd == "ATRV":
            return "14.2V\r\n>"
        elif cmd == "ATI":
            return "ELM327 v1.5 AutoScan BR Edition\r\n>"
        elif cmd == "ATIGN":
            return "ON\r\n>"
        else:
            return "OK\r\n>"

    def _handle_obd_command(self, cmd: str) -> str:
        # Modo 01 - Telemetria em tempo real
        if cmd.startswith("01"):
            pid = cmd[2:4]
            return self._handle_mode_01(pid)

        # Modo 03 - DTCs armazenados
        elif cmd == "03":
            if self.state["dtcs"]:
                # Resposta Modo 03: 43 + qtde/códigos (ex: 43 01 71 00 00 00)
                # P0171 = 01 71
                return "43 01 71 00 00 00 00\r\n>"
            else:
                return "43 00 00 00 00 00 00\r\n>"

        # Modo 07 - DTCs pendentes
        elif cmd == "07":
            return "47 01 71 00 00 00 00\r\n>"

        # Modo 09 - Informações do veículo (VIN)
        elif cmd.startswith("09"):
            if cmd == "0902":
                # Simula VIN de um Ford Fiesta Nacional: 9BFB...
                return "49 02 01 39 42 46 42 02 58 58 58 58 4A 31 32 33 34 35 36\r\n>"
            return "49 00 00 00 00 00\r\n>"

        return "NO DATA\r\n>"

    def _handle_mode_01(self, pid: str) -> str:
        # 0100: PIDs suportados 01-20
        if pid == "00":
            # Retorna máscara binária em hex indicando PIDs comuns suportados
            return "41 00 BE 3F B8 11\r\n>"

        # 0104: Carga calculada do motor (0 a 100%)
        elif pid == "04":
            val = int((self.state["tps"] / 100.0) * 255)
            return f"41 04 {val:02X}\r\n>"

        # 0105: Temperatura do líquido de arrefecimento (Formula: A - 40)
        elif pid == "05":
            val = int(self.state["coolant_temp"] + 40)
            return f"41 05 {val:02X}\r\n>"

        # 0106: STFT Bank 1 (Formula: (A / 1.28) - 100)
        elif pid == "06":
            val = int((self.state["stft_b1"] + 100) * 1.28)
            val = max(0, min(255, val))
            return f"41 06 {val:02X}\r\n>"

        # 0107: LTFT Bank 1
        elif pid == "07":
            val = int((self.state["ltft_b1"] + 100) * 1.28)
            val = max(0, min(255, val))
            return f"41 07 {val:02X}\r\n>"

        # 010B: MAP (Pressão no coletor, kPa: A)
        elif pid == "0B":
            val = int(self.state["map_kpa"])
            return f"41 0B {val:02X}\r\n>"

        # 010C: Rotação do motor RPM (Formula: (256A + B) / 4)
        elif pid == "0C":
            rpm_raw = int(self.state["rpm"] * 4)
            a = (rpm_raw >> 8) & 0xFF
            b = rpm_raw & 0xFF
            return f"41 0C {a:02X} {b:02X}\r\n>"

        # 010D: Velocidade do veículo km/h (Formula: A)
        elif pid == "0D":
            val = int(self.state["speed"])
            return f"41 0D {val:02X}\r\n>"

        # 010F: Temperatura do ar de admissão IAT (Formula: A - 40)
        elif pid == "0F":
            val = int(self.state["intake_temp"] + 40)
            return f"41 0F {val:02X}\r\n>"

        # 0111: Posição da borboleta TPS (Formula: A * 100 / 255)
        elif pid == "11":
            val = int((self.state["tps"] * 255) / 100.0)
            return f"41 11 {val:02X}\r\n>"

        # 0114: Sonda Lambda B1S1 (Volts: A / 200)
        elif pid == "14":
            val_a = int(self.state["o2_b1s1"] * 200)
            val_b = 128  # short term trim associado
            return f"41 14 {val_a:02X} {val_b:02X}\r\n>"

        # 011C: Padrão OBD suportado
        elif pid == "1C":
            return "41 1C 06\r\n>"

        # 0120: PIDs suportados 21-40
        elif pid == "20":
            return "41 20 80 00 00 00\r\n>"

        return "NO DATA\r\n>"

