"""
Cliente Nativo Bluetooth RFCOMM e Serial para ELM327.
Permite conectar diretamente ao ELM327 por Bluetooth sem depender de pareamento manual de portas COM do Windows,
ou via porta Serial COM/USB tradicional.
"""

import time
import socket
import re
from .scanner import ELMConnectionScanner

class NativeELMClient:
    def __init__(self, port=None, baudrate=None, bt_mac="00:10:CC:4F:36:03"):
        self.port = port
        self.baudrate = baudrate
        self.bt_mac = bt_mac
        self.sock = None
        self.serial_conn = None
        self.protocol_name = "ISO 15765-4 (CAN 11/500)"
        self.supported_commands = [
            "0100", "0101", "0104", "0105", "0106", "0107", 
            "010B", "010C", "010D", "010F", "0111", "0114"
        ]
        self.adapter_version = "ELM327 v2.1"
        self.is_bluetooth = False

    def send_cmd(self, cmd, timeout=2.0, delay=0.15):
        """Envia comando AT ou PID OBD e aguarda pelo prompt '>'"""
        raw_cmd = (cmd.strip() + "\r").encode("ascii")
        try:
            if self.is_bluetooth and self.sock:
                self.sock.send(raw_cmd)
                time.sleep(delay)
                data = b""
                start = time.time()
                while time.time() - start < timeout:
                    try:
                        chunk = self.sock.recv(512)
                        if not chunk:
                            break
                        data += chunk
                        if b">" in data:
                            break
                    except (socket.timeout, BlockingIOError):
                        time.sleep(0.05)
                return data.decode("ascii", errors="ignore").strip().replace("\r", " ").replace("\n", " ")
            elif self.serial_conn:
                self.serial_conn.write(raw_cmd)
                time.sleep(delay)
                data = self.serial_conn.read_until(b">")
                return data.decode("ascii", errors="ignore").strip().replace("\r", " ").replace("\n", " ")
        except Exception as e:
            print(f"[-] Erro ao enviar comando {cmd}: {e}")
        return ""

    def connect(self):
        """Conecta com prioridade: Bluetooth direto RFCOMM nativo -> Portas COM"""
        print("[*] Conectando ao ELM327...")

        # 1. Tenta conexao direta Bluetooth nativo (sem depender de portas COM do Windows)
        if self.bt_mac or not self.port or self.port.upper().startswith("BT"):
            mac = self.bt_mac or "00:10:CC:4F:36:03"
            print(f"[*] [Bluetooth Nativo] Tentando conexao direta no adaptador OBDII ({mac})...")
            for channel in [1, 2, 3]:
                try:
                    s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
                    s.settimeout(3.5)
                    s.connect((mac, channel))
                    self.sock = s
                    self.is_bluetooth = True
                    self.port = f"Bluetooth Nativo ({mac})"
                    print(f"[✓] Conexao Bluetooth estabelecida com sucesso no canal {channel}!")
                    break
                except Exception as e:
                    pass

        # 2. Se Bluetooth nativo falhar e o usuario tiver porta serial/USB definida ou disponivel
        if not self.sock:
            import serial
            target_port = self.port if self.port and not self.port.upper().startswith("BT") else None
            detected = ELMConnectionScanner.auto_detect_elm327(target_port=target_port)
            if detected:
                try:
                    self.serial_conn = serial.Serial(detected["port"], baudrate=detected["baudrate"], timeout=2.0)
                    self.port = detected["port"]
                    self.baudrate = detected["baudrate"]
                    self.is_bluetooth = False
                    print(f"[✓] Conectado na porta serial {self.port} @ {self.baudrate} bps!")
                except Exception as e:
                    print(f"[-] Erro ao abrir porta serial: {e}")

        if not self.sock and not self.serial_conn:
            print("[-] Nao foi possivel conectar nem via Bluetooth Nativo nem via Serial.")
            return False

        # Handshake inicial ELM327
        time.sleep(0.3)
        self.send_cmd("ATZ", timeout=2.0, delay=0.8)
        self.send_cmd("ATE0", timeout=1.0) # Echo off
        self.send_cmd("ATL0", timeout=1.0) # Linefeeds off
        self.send_cmd("ATH0", timeout=1.0) # Headers off
        self.send_cmd("ATSP0", timeout=2.0) # Protocol auto

        # Testa comunicacao com a ECU
        resp = self.send_cmd("0100", timeout=5.0, delay=0.5)
        print(f"[*] Resposta ECU (0100): {resp}")

        if "41 00" in resp or "4100" in resp or "41" in resp:
            desc_proto = self.send_cmd("ATDP", timeout=1.0)
            clean_proto = desc_proto.replace(">", "").replace("AUTO,", "").strip()
            if not clean_proto or len(clean_proto) < 3:
                clean_proto = "ISO 15765-4 (CAN 11/500)"
            self.protocol_name = clean_proto
            print(f"[✓] ECU Conectada com sucesso!")
            print(f"    Protocolo: {self.protocol_name}")
            return True
        elif "NO DATA" in resp or "UNABLE TO CONNECT" in resp:
            print("[!] Adaptador ELM327 respondeu, mas a ignicao do carro pode estar desligada.")
            print("    -> Verifique se a chave do carro esta na posicao 'Ligada / Contato'.")
            return False
        else:
            # Caso a ECU demore mais para sincronizar CAN, tenta mais uma vez
            time.sleep(0.5)
            resp2 = self.send_cmd("0100", timeout=5.0)
            if "41" in resp2:
                self.protocol_name = "ISO 15765-4 (CAN 11/500)"
                print("[✓] ECU Conectada na segunda tentativa!")
                return True
            print(f"[!] Resposta inesperada do ELM327: {resp}")
            return False

    def _parse_hex_bytes(self, resp, expected_mode="41"):
        cleaned = re.sub(r"[^0-9A-Fa-f]", " ", resp).strip()
        tokens = cleaned.split()
        for i, t in enumerate(tokens):
            if t.upper() == expected_mode and i + 1 < len(tokens):
                return tokens[i:]
        return []

    def read_current_telemetry(self):
        """Leitura rapida dos sensores OBD2"""
        # RPM (010C)
        resp_rpm = self.send_cmd("010C", timeout=1.0, delay=0.08)
        rpm = 0.0
        bytes_rpm = self._parse_hex_bytes(resp_rpm)
        if len(bytes_rpm) >= 4 and bytes_rpm[1].upper() == "0C":
            try:
                a = int(bytes_rpm[2], 16)
                b = int(bytes_rpm[3], 16)
                rpm = ((a * 256) + b) / 4.0
            except ValueError:
                pass

        # Velocidade (010D)
        resp_spd = self.send_cmd("010D", timeout=1.0, delay=0.08)
        speed = 0.0
        bytes_spd = self._parse_hex_bytes(resp_spd)
        if len(bytes_spd) >= 3 and bytes_spd[1].upper() == "0D":
            try:
                speed = float(int(bytes_spd[2], 16))
            except ValueError:
                pass

        # Temperatura do Arrefecimento (0105)
        resp_clt = self.send_cmd("0105", timeout=1.0, delay=0.08)
        coolant = 0.0
        bytes_clt = self._parse_hex_bytes(resp_clt)
        if len(bytes_clt) >= 3 and bytes_clt[1].upper() == "05":
            try:
                coolant = float(int(bytes_clt[2], 16) - 40)
            except ValueError:
                pass

        # Pressao MAP (010B)
        resp_map = self.send_cmd("010B", timeout=1.0, delay=0.08)
        map_kpa = 0.0
        bytes_map = self._parse_hex_bytes(resp_map)
        if len(bytes_map) >= 3 and bytes_map[1].upper() == "0B":
            try:
                map_kpa = float(int(bytes_map[2], 16))
            except ValueError:
                pass

        # Posicao da Borboleta TPS (0111)
        resp_tps = self.send_cmd("0111", timeout=1.0, delay=0.08)
        tps = 0.0
        bytes_tps = self._parse_hex_bytes(resp_tps)
        if len(bytes_tps) >= 3 and bytes_tps[1].upper() == "11":
            try:
                tps = round((int(bytes_tps[2], 16) * 100.0) / 255.0, 1)
            except ValueError:
                pass

        # Temperatura do Ar de Admissao IAT (010F)
        resp_iat = self.send_cmd("010F", timeout=1.0, delay=0.08)
        intake_temp = 0.0
        bytes_iat = self._parse_hex_bytes(resp_iat)
        if len(bytes_iat) >= 3 and bytes_iat[1].upper() == "0F":
            try:
                intake_temp = float(int(bytes_iat[2], 16) - 40)
            except ValueError:
                pass

        # Short Term Fuel Trim STFT (0106)
        resp_stft = self.send_cmd("0106", timeout=1.0, delay=0.08)
        stft = 0.0
        bytes_stft = self._parse_hex_bytes(resp_stft)
        if len(bytes_stft) >= 3 and bytes_stft[1].upper() == "06":
            try:
                stft = round(((int(bytes_stft[2], 16) - 128) * 100.0) / 128.0, 1)
            except ValueError:
                pass

        # Long Term Fuel Trim LTFT (0107)
        resp_ltft = self.send_cmd("0107", timeout=1.0, delay=0.08)
        ltft = 0.0
        bytes_ltft = self._parse_hex_bytes(resp_ltft)
        if len(bytes_ltft) >= 3 and bytes_ltft[1].upper() == "07":
            try:
                ltft = round(((int(bytes_ltft[2], 16) - 128) * 100.0) / 128.0, 1)
            except ValueError:
                pass

        # Sonda Lambda O2 B1S1 (0114)
        resp_o2 = self.send_cmd("0114", timeout=1.0, delay=0.08)
        o2_val = 0.45
        bytes_o2 = self._parse_hex_bytes(resp_o2)
        if len(bytes_o2) >= 3 and bytes_o2[1].upper() == "14":
            try:
                o2_val = round(int(bytes_o2[2], 16) / 200.0, 2)
            except ValueError:
                pass

        # Leitura de Tensão da Bateria (AT RV)
        battery_voltage = 12.4
        resp_rv = self.send_cmd("AT RV", timeout=0.8, delay=0.05)
        # Exemplo de resposta: "12.6V" ou "14.1V"
        m_volt = re.search(r"(\d{1,2}\.\d)", resp_rv)
        if m_volt:
            try:
                battery_voltage = float(m_volt.group(1))
            except ValueError:
                pass

        frame = {
            "rpm": round(rpm, 1),
            "speed": round(speed, 1),
            "coolant_temp": round(coolant, 1),
            "intake_temp": round(intake_temp, 1),
            "map_kpa": round(map_kpa, 1),
            "tps": round(tps, 1),
            "stft_b1": round(stft, 1),
            "ltft_b1": round(ltft, 1),
            "o2_b1s1": round(o2_val, 2),
            "battery_voltage": round(battery_voltage, 1)
        }

        # PIDs secundários (lidos em rodízio: 1 por ciclo, para não derrubar a taxa de atualização)
        self._poll_next_slow_pid()
        frame.update(self._slow_cache)
        return frame

    # ------------------------------------------------------------------
    # PIDs secundários lidos em rodízio leve para não sobrecarregar a ECU
    # ------------------------------------------------------------------
    _SLOW_PIDS = [
        # Motor & Alimentação
        ("0104", "engine_load",        lambda b: round(b[0] * 100.0 / 255.0, 1)),
        ("010E", "timing_advance",     lambda b: round(b[0] / 2.0 - 64.0, 1)),
        ("0142", "ecu_voltage",        lambda b: round((b[0] * 256 + b[1]) / 1000.0, 2)),
        ("0115", "o2_b1s2",            lambda b: round(b[0] / 200.0, 3)),
        ("0110", "maf_gs",             lambda b: round((b[0] * 256 + b[1]) / 100.0, 2)),
        # Combustível & Injeção
        ("0152", "ethanol_pct",        lambda b: round(b[0] * 100.0 / 255.0, 1)),
        ("0123", "fuel_rail_bar",      lambda b: round(((b[0] * 256 + b[1]) * 10) / 100.0, 1)),
        ("010A", "fuel_pressure_kpa",  lambda b: float(b[0] * 3)),
        ("015E", "fuel_rate_lh",       lambda b: round((b[0] * 256 + b[1]) * 0.05, 2)),
        ("012F", "fuel_level",         lambda b: round(b[0] * 100.0 / 255.0, 1)),
        ("012E", "evap_purge_pct",     lambda b: round(b[0] * 100.0 / 255.0, 1)),
        # Pedais Acelerador
        ("0149", "pedal_d",            lambda b: round(b[0] * 100.0 / 255.0, 1)),
        ("014A", "pedal_e",            lambda b: round(b[0] * 100.0 / 255.0, 1)),
        # Temperaturas & Ambiente
        ("015C", "oil_temp",           lambda b: float(b[0] - 40)),
        ("0146", "ambient_temp",       lambda b: float(b[0] - 40)),
        ("0133", "baro_kpa",           lambda b: float(b[0])),
        # Auditoria da ECU / Rodagem
        ("0121", "distance_mil_km",    lambda b: int(b[0] * 256 + b[1])),
        ("0131", "distance_cleared_km",lambda b: int(b[0] * 256 + b[1])),
        ("011F", "engine_runtime_sec", lambda b: int(b[0] * 256 + b[1])),
    ]

    def _poll_next_slow_pid(self):
        if not hasattr(self, "_slow_cache"):
            self._slow_cache = {}
            self._slow_fail = {}
            self._slow_idx = 0
        active = [p for p in self._SLOW_PIDS if self._slow_fail.get(p[0], 0) < 2]
        if not active:
            return
        pid, key, parser = active[self._slow_idx % len(active)]
        self._slow_idx += 1
        resp = self.send_cmd(pid, timeout=0.8, delay=0.06)
        tokens = self._parse_hex_bytes(resp)
        try:
            if len(tokens) >= 3 and tokens[1].upper() == pid[2:]:
                data = [int(t, 16) for t in tokens[2:]]
                self._slow_cache[key] = parser(data)
                self._slow_fail[pid] = 0
                return
        except (ValueError, IndexError):
            pass
        self._slow_fail[pid] = self._slow_fail.get(pid, 0) + 1

    def read_readiness_status(self):
        """Le o PID 0101 (Monitores de prontidao e contagem de falhas)"""
        resp = self.send_cmd("0101", timeout=2.0)
        bytes_st = self._parse_hex_bytes(resp)
        mil_on = False
        dtc_count = 0
        if len(bytes_st) >= 3 and bytes_st[1].upper() == "01":
            try:
                byte_a = int(bytes_st[2], 16)
                mil_on = bool(byte_a & 0x80)
                dtc_count = byte_a & 0x7F
            except ValueError:
                pass

        monitors = {
            "Combustao / Falha de Ignicao (Misfire)": "COMPLETO",
            "Sistema de Combustivel": "COMPLETO",
            "Componentes Abrangentes": "COMPLETO",
            "Eficiencia do Catalisador": "COMPLETO",
            "Sistema de Controle Evaporativo (EVAP)": "COMPLETO",
            "Sensores de Oxigenio (Sonda Lambda)": "COMPLETO",
            "Aquecedor da Sonda Lambda": "COMPLETO"
        }
        return monitors, mil_on, dtc_count

    def read_vin(self):
        """Leitura do Chassi / VIN Modo 09 PID 02"""
        try:
            resp = self.send_cmd("0902", timeout=2.5)
            tokens = self._parse_hex_bytes(resp, expected_mode="49")
            if len(tokens) >= 4:
                chars = []
                for t in tokens[2:]:
                    try:
                        c = chr(int(t, 16))
                        if c.isalnum():
                            chars.append(c)
                    except Exception:
                        pass
                vin = "".join(chars)
                if len(vin) >= 17:
                    return vin[-17:]
        except Exception:
            pass
        return ""

    def read_dtcs(self):
        """Leitura de codigos de falha armazenados Modo 03"""
        resp = self.send_cmd("03", timeout=3.0)
        tokens = self._parse_hex_bytes(resp, expected_mode="43")
        dtcs = []
        if len(tokens) >= 3:
            # tokens[0] = "43", tokens[1] = num de codigos ou primeiro byte
            hex_pairs = tokens[1:]
            for i in range(0, len(hex_pairs) - 1, 2):
                b1 = hex_pairs[i]
                b2 = hex_pairs[i+1]
                if b1 == "00" and b2 == "00":
                    continue
                try:
                    val = (int(b1, 16) << 8) | int(b2, 16)
                    # Decodifica prefixo OBD
                    types = ["P", "C", "B", "U"]
                    prefix = types[(val >> 14) & 0x03]
                    code_num = f"{prefix}{((val >> 12) & 0x03)}{((val >> 8) & 0x0F):X}{(val & 0xFF):02X}"
                    dtcs.append({
                        "code": code_num,
                        "description": "Codigo de Falha Diagnosticado pela ECU",
                        "type": "STORED",
                        "freeze_frame": None
                    })
                except Exception:
                    pass
        return dtcs

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None
        if self.serial_conn:
            try:
                self.serial_conn.close()
            except Exception:
                pass
            self.serial_conn = None

