"""
AutoScan BR - Agente Coletor de Telemetria
Conecta no ELM327 físico (porta serial COM/USB/Bluetooth) OU no Simulador Virtual,
lê os PIDs em tempo real e despacha para a API do Laravel.
"""

import time
import json
import argparse
import urllib.request
import urllib.error
from .simulator.elm_simulator import ELM327Simulator

class AutoScanCollector:
    def __init__(self, api_base="http://127.0.0.1:8000/api/v1/telemetry", mode="simulator", port=None, baudrate=None):
        self.api_base = api_base
        self.mode = mode
        self.port = port
        self.baudrate = baudrate
        self.session_id = None
        self.simulator = ELM327Simulator() if mode == "simulator" else None
        self.real_client = None

    def post_json(self, endpoint, data):
        url = f"{self.api_base}/{endpoint}"
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as e:
            print(f"[-] Erro ao enviar para {url}: {e}")
            return None

    def start_session(self):
        print(f"[*] Iniciando sessão no Laravel ({self.api_base})...")

        port_desc = "Simulador Virtual"
        protocol_desc = "ISO 15765-4 (CAN 11/500)"
        adapter_desc = "ELM327 v1.5 AutoScan BR"
        supported_pids = ["0100", "0101", "0104", "0105", "0106", "0107", "010B", "010C", "010D", "010F", "0111", "0114"]
        readiness_monitors = {
            "Combustão / Falha de Ignição (Misfire)": "COMPLETO",
            "Sistema de Combustível": "COMPLETO",
            "Componentes Abrangentes": "COMPLETO",
            "Eficiência do Catalisador": "COMPLETO",
            "Sistema de Controle Evaporativo (EVAP)": "INCOMPLETO",
            "Sensores de Oxigênio (Sonda Lambda)": "COMPLETO",
            "Aquecedor da Sonda Lambda": "COMPLETO"
        }
        mil_active = True
        dtc_count = 1

        if self.mode == "serial":
            from .connection.native_client import NativeELMClient
            self.real_client = NativeELMClient(port=self.port, baudrate=self.baudrate)
            if not self.real_client.connect():
                print("[-] Abortando: Não foi possível estabelecer conexão segura com a ECU do veículo.")
                return False
            port_desc = self.real_client.port
            protocol_desc = self.real_client.protocol_name
            supported_pids = self.real_client.supported_commands
            monitors, mil, count = self.real_client.read_readiness_status()
            if monitors:
                readiness_monitors = monitors
                mil_active = mil
                dtc_count = count

        payload = {
            "port": str(port_desc),
            "protocol": str(protocol_desc),
            "adapter_version": adapter_desc,
            "supported_pids": supported_pids,
            "readiness_monitors": readiness_monitors,
            "mil_active": mil_active,
            "dtc_count": dtc_count
        }
        res = self.post_json("session/start", payload)
        if res and res.get("status") == "success":
            self.session_id = res["session_id"]
            print(f"[✓] Sessão criada com sucesso no AutoScan BR! ID: {self.session_id}")
            
            # Lê e envia os DTCs (códigos de falha) com Freeze Frame
            if self.mode == "serial":
                real_dtcs = self.real_client.read_dtcs()
                if real_dtcs:
                    self.post_json("dtcs", {
                        "session_id": self.session_id,
                        "dtcs": real_dtcs,
                        "readiness_monitors": readiness_monitors,
                        "mil_active": mil_active
                    })
                    print(f"[!] {len(real_dtcs)} códigos de falha enviados ao laudo.")
            else:
                self.post_json("dtcs", {
                    "session_id": self.session_id,
                    "readiness_monitors": readiness_monitors,
                    "mil_active": mil_active,
                    "dtcs": [
                        {
                            "code": "P0171",
                            "type": "STORED",
                            "description": "Sistema muito pobre (Bancada 1) - Excesso de ar não medido ou falta de injeção",
                            "freeze_frame": {
                                "dtc_causador": "P0171",
                                "rpm": 820,
                                "coolant_temp_c": 89.0,
                                "speed_kmh": 0.0,
                                "map_kpa": 32.5,
                                "ltft_percent": 18.8,
                                "stft_percent": 4.2
                            }
                        }
                    ]
                })
            return True
        return False

    def run_telemetry_loop(self, interval=0.25):
        print("[*] Iniciando loop de telemetria contínua...")
        consecutive_errors = 0
        while True:
            try:
                frame = None
                if self.mode == "simulator":
                    self.simulator.update_dynamic_state()
                    state = self.simulator.state
                    frame = {
                        "rpm": round(state["rpm"], 1),
                        "speed": round(state["speed"], 1),
                        "coolant_temp": round(state["coolant_temp"], 1),
                        "intake_temp": round(state["intake_temp"], 1),
                        "map_kpa": round(state["map_kpa"], 1),
                        "tps": round(state["tps"], 1),
                        "o2_b1s1": round(state["o2_b1s1"], 2),
                        "stft_b1": round(state["stft_b1"], 1),
                        "ltft_b1": round(state["ltft_b1"], 1),
                    }
                elif self.mode == "serial":
                    frame = self.real_client.read_current_telemetry()
                    if not frame:
                        consecutive_errors += 1
                        if consecutive_errors > 5:
                            print("\n[!] Perda de comunicação com o ELM327. Tentando recuperar...")
                            self.real_client.connect()
                            consecutive_errors = 0
                        time.sleep(1)
                        continue
                    consecutive_errors = 0

                payload = {
                    "session_id": self.session_id,
                    "frames": [frame]
                }
                self.post_json("frames", payload)
                print(f"[Telemetria] RPM: {frame['rpm']:<6} | Vel: {frame['speed']:<4} | MAP: {frame['map_kpa']:<4} kPa | Temp: {frame['coolant_temp']:<4}°C | O2: {frame['o2_b1s1']}V", end="\r")
                time.sleep(interval)
            except KeyboardInterrupt:
                print("\n[*] Telemetria encerrada com sucesso.")
                break
        
        if self.real_client:
            self.real_client.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AutoScan BR Collector")
    parser.add_argument("--mode", default="simulator", choices=["simulator", "serial"])
    parser.add_argument("--port", default=None, help="Ex: COM3 no Windows ou /dev/tty.usbserial no Mac")
    parser.add_argument("--baud", type=int, default=None, help="Baudrate ex: 38400 ou 115200")
    parser.add_argument("--api", default="http://127.0.0.1:8000/api/v1/telemetry")
    args = parser.parse_args()

    collector = AutoScanCollector(api_base=args.api, mode=args.mode, port=args.port, baudrate=args.baud)
    if collector.start_session():
        collector.run_telemetry_loop()
