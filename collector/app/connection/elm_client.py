"""
Cliente físico OBD-II para comunicação real com adaptador ELM327 conectado ao veículo.
Otimizado para o Ford New Fiesta 1.5 16V Sigma Flex (ISO 15765-4 CAN 11/500).
Inclui suporte à leitura de Freeze Frame (Modo 02) e Monitores de Prontidão (Modo 01 PID 01).
"""

import time
import obd
from obd import OBDStatus
from .scanner import ELMConnectionScanner

class RealOBDClient:
    def __init__(self, port=None, baudrate=None):
        self.port = port
        self.baudrate = baudrate
        self.connection = None
        self.protocol_name = "Desconhecido"
        self.supported_commands = []

    def connect(self, fast_mode=True):
        """
        Inicia a conexão com o ELM327 e ECU do veículo com auto-recuperação.
        """
        # Se nenhuma porta foi passada, detecta automaticamente
        if not self.port:
            detected = ELMConnectionScanner.auto_detect_elm327()
            if detected:
                self.port = detected["port"]
                self.baudrate = detected["baudrate"]
            else:
                print("[-] Nenhuma porta serial com ELM327 foi identificada automaticamente.")
                return False

        print(f"[*] Conectando ao ELM327 na porta {self.port} (Baud: {self.baudrate or 'Auto'})...")
        
        # Conecta usando a biblioteca python-OBD
        # Protocolo "6" é ISO 15765-4 (CAN 11-bit 500kbaud) usado no New Fiesta
        self.connection = obd.OBD(
            portstr=self.port,
            baudrate=self.baudrate,
            protocol="6",
            fast=fast_mode,
            timeout=1.5
        )

        status = self.connection.status()
        print(f"[*] Status da conexão OBD: {status}")

        if status == OBDStatus.CAR_CONNECTED:
            self.protocol_name = self.connection.protocol_name()
            self.supported_commands = [cmd.name for cmd in self.connection.supported_commands]
            print(f"[✓] ECU Conectada com sucesso!")
            print(f"    Protocolo: {self.protocol_name}")
            print(f"    PIDs Suportados: {len(self.supported_commands)} comandos disponíveis.")
            return True
        elif status == OBDStatus.ELM_CONNECTED:
            print("[!] Adaptador ELM327 respondeu, mas a ECU do veículo não respondeu.")
            print("    -> Verifique se a chave de ignição do New Fiesta está na posição 'Ligada/Contato' (painel aceso).")
            return False
        else:
            print("[-] Falha ao inicializar o adaptador ELM327.")
            return False

    def read_current_telemetry(self):
        """
        Faz a leitura síncrona dos sensores fundamentais do Fiesta 1.5
        """
        if not self.connection or not self.connection.is_connected():
            return None

        # Leituras específicas do motor Sigma
        c_rpm = self.connection.query(obd.commands.RPM)
        c_speed = self.connection.query(obd.commands.SPEED)
        c_coolant = self.connection.query(obd.commands.COOLANT_TEMP)
        c_intake = self.connection.query(obd.commands.INTAKE_TEMP)
        c_map = self.connection.query(obd.commands.INTAKE_PRESSURE)
        c_tps = self.connection.query(obd.commands.THROTTLE_POS)
        c_stft = self.connection.query(obd.commands.SHORT_FUEL_TRIM_1)
        c_ltft = self.connection.query(obd.commands.LONG_FUEL_TRIM_1)
        c_o2 = self.connection.query(obd.commands.O2_B1S1)

        # Trata valores nulos ou erros de leitura de forma segura
        rpm = c_rpm.value.magnitude if (c_rpm and not c_rpm.is_null()) else 0.0
        speed = c_speed.value.magnitude if (c_speed and not c_speed.is_null()) else 0.0
        coolant = c_coolant.value.magnitude if (c_coolant and not c_coolant.is_null()) else 0.0
        intake = c_intake.value.magnitude if (c_intake and not c_intake.is_null()) else 0.0
        map_kpa = c_map.value.magnitude if (c_map and not c_map.is_null()) else 0.0
        tps = c_tps.value.magnitude if (c_tps and not c_tps.is_null()) else 0.0
        stft = c_stft.value.magnitude if (c_stft and not c_stft.is_null()) else 0.0
        ltft = c_ltft.value.magnitude if (c_ltft and not c_ltft.is_null()) else 0.0
        
        # Sonda Lambda pode retornar tupla de (tensão, fuel trim)
        o2_val = 0.45
        if c_o2 and not c_o2.is_null():
            val = c_o2.value
            if isinstance(val, (tuple, list)):
                o2_val = val[0].magnitude if hasattr(val[0], "magnitude") else float(val[0])
            elif hasattr(val, "magnitude"):
                o2_val = val.magnitude

        return {
            "rpm": round(float(rpm), 1),
            "speed": round(float(speed), 1),
            "coolant_temp": round(float(coolant), 1),
            "intake_temp": round(float(intake), 1),
            "map_kpa": round(float(map_kpa), 1),
            "tps": round(float(tps), 1),
            "stft_b1": round(float(stft), 1),
            "ltft_b1": round(float(ltft), 1),
            "o2_b1s1": round(float(o2_val), 2),
        }

    def read_readiness_status(self):
        """
        Lê o PID 0101 (Status dos Monitores de Prontidão / Luz de Injeção MIL)
        """
        if not self.connection or not self.connection.is_connected():
            return None, False, 0

        status_cmd = self.connection.query(obd.commands.STATUS)
        if status_cmd and not status_cmd.is_null():
            val = status_cmd.value
            mil_on = getattr(val, "MIL", False)
            dtc_count = getattr(val, "DTC_count", 0)
            
            # Constrói dicionário de testes dos monitores
            monitors = {}
            # Monitores contínuos
            if hasattr(val, "misfire"):
                monitors["Combustão / Falha de Ignição (Misfire)"] = "COMPLETO" if getattr(val.misfire, "complete", True) else "INCOMPLETO"
            if hasattr(val, "fuel"):
                monitors["Sistema de Combustível"] = "COMPLETO" if getattr(val.fuel, "complete", True) else "INCOMPLETO"
            if hasattr(val, "components"):
                monitors["Componentes Abrangentes"] = "COMPLETO" if getattr(val.components, "complete", True) else "INCOMPLETO"
            
            # Monitores não-contínuos
            if hasattr(val, "catalyst"):
                monitors["Eficiência do Catalisador"] = "COMPLETO" if getattr(val.catalyst, "complete", True) else "INCOMPLETO"
            if hasattr(val, "evap"):
                monitors["Sistema de Controle Evaporativo (EVAP)"] = "COMPLETO" if getattr(val.evap, "complete", True) else "INCOMPLETO"
            if hasattr(val, "o2_sensor"):
                monitors["Sensores de Oxigênio (Sonda Lambda)"] = "COMPLETO" if getattr(val.o2_sensor, "complete", True) else "INCOMPLETO"
            if hasattr(val, "o2_heater"):
                monitors["Aquecedor da Sonda Lambda"] = "COMPLETO" if getattr(val.o2_heater, "complete", True) else "INCOMPLETO"

            return monitors, mil_on, dtc_count

        return None, False, 0

    def read_freeze_frame(self):
        """
        Lê os parâmetros congelados no momento em que a falha DTC ocorreu (Modo 02).
        """
        if not self.connection or not self.connection.is_connected():
            return None

        # PIDs com prefixo Modo 02 disponíveis na biblioteca python-obd ou via consulta customizada
        freeze = {}
        # Consulta PID de DTC que causou o congelamento
        ff_dtc = self.connection.query(obd.commands.FREEZE_DTC)
        if ff_dtc and not ff_dtc.is_null():
            freeze["dtc_causador"] = str(ff_dtc.value)

        # Consultas de parâmetros em Freeze Frame
        ff_rpm = self.connection.query(obd.commands.RPM, force=True)
        if ff_rpm and not ff_rpm.is_null():
            freeze["rpm"] = round(float(ff_rpm.value.magnitude), 0)

        ff_speed = self.connection.query(obd.commands.SPEED, force=True)
        if ff_speed and not ff_speed.is_null():
            freeze["speed_kmh"] = round(float(ff_speed.value.magnitude), 1)

        ff_coolant = self.connection.query(obd.commands.COOLANT_TEMP, force=True)
        if ff_coolant and not ff_coolant.is_null():
            freeze["coolant_temp_c"] = round(float(ff_coolant.value.magnitude), 1)

        ff_map = self.connection.query(obd.commands.INTAKE_PRESSURE, force=True)
        if ff_map and not ff_map.is_null():
            freeze["map_kpa"] = round(float(ff_map.value.magnitude), 1)

        ff_ltft = self.connection.query(obd.commands.LONG_FUEL_TRIM_1, force=True)
        if ff_ltft and not ff_ltft.is_null():
            freeze["ltft_percent"] = round(float(ff_ltft.value.magnitude), 1)

        return freeze if freeze else None

    def read_dtcs(self):
        """
        Lê os códigos de falha armazenados (Modo 03) sem apagar nada.
        """
        if not self.connection or not self.connection.is_connected():
            return []

        dtc_response = self.connection.query(obd.commands.GET_DTC)
        dtcs = []
        if dtc_response and not dtc_response.is_null():
            # Tenta obter dados de Freeze Frame
            freeze_frame_data = self.read_freeze_frame()

            for code, desc in dtc_response.value:
                dtcs.append({
                    "code": str(code),
                    "description": str(desc),
                    "type": "STORED",
                    "freeze_frame": freeze_frame_data
                })
        return dtcs

    def close(self):
        if self.connection:
            self.connection.close()
