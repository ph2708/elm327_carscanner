"""
Auto-detector e gerenciador de portas seriais e conexões ELM327.
Varre portas COM no Windows ou /dev/tty.* no macOS/Linux e faz o handshake.
"""

import sys
import glob
import time
import serial
import serial.tools.list_ports

COMMON_BAUDRATES = [38400, 115200, 9600, 57600]

class ELMConnectionScanner:
    @staticmethod
    def list_available_ports():
        """Lista todas as portas seriais disponíveis no sistema operacional"""
        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append({
                "device": port.device,
                "name": port.name,
                "description": port.description,
                "hwid": port.hwid,
                "manufacturer": port.manufacturer or "Genérico / Desconhecido"
            })
        return ports

    @staticmethod
    def auto_detect_elm327(target_port=None):
        """
        Varre as portas e testa handshake ATZ.
        Retorna (porta, baudrate, versao_elm) ou None
        """
        ports_to_test = [target_port] if target_port else [p["device"] for p in ELMConnectionScanner.list_available_ports()]
        
        print(f"[*] Varrendo portas seriais para identificar ELM327: {ports_to_test}")

        for port in ports_to_test:
            for baud in COMMON_BAUDRATES:
                try:
                    # Timeout curto para detecção rápida
                    with serial.Serial(port, baudrate=baud, timeout=0.8) as ser:
                        # Limpa buffer
                        ser.reset_input_buffer()
                        ser.reset_output_buffer()
                        
                        # Envia comando de reset
                        ser.write(b"ATZ\r\n")
                        time.sleep(0.5)
                        resp = ser.read(128).decode("utf-8", errors="ignore")
                        
                        if "ELM327" in resp or "OBD" in resp:
                            print(f"[✓] Adaptador detectado na porta {port} @ {baud} bps!")
                            return {
                                "port": port,
                                "baudrate": baud,
                                "version": resp.strip().replace(">", "").strip()
                            }
                except (serial.SerialException, OSError):
                    continue
        return None

