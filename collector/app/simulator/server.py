"""
Servidor Virtual TCP/Serial para o Simulador ELM327.
Permite conectar o coletor via porta serial virtual ou socket de rede local (ex: localhost:35000),
possibilitando rodar e testar tudo no macOS ou Windows sem hardware físico.
"""

import socket
import threading
import sys
from .elm_simulator import ELM327Simulator

class VirtualELMServer:
    def __init__(self, host="127.0.0.1", port=35000):
        self.host = host
        self.port = port
        self.simulator = ELM327Simulator()
        self.running = False
        self.server_socket = None

    def start(self):
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        print(f"[*] Simulador ELM327 ativo em {self.host}:{self.port}")
        print("[*] Aguardando conexão do Coletor AutoScan BR...")

        try:
            while self.running:
                client_sock, client_addr = self.server_socket.accept()
                print(f"[+] Conexão recebida de {client_addr}")
                t = threading.Thread(target=self._handle_client, args=(client_sock,))
                t.daemon = True
                t.start()
        except Exception as e:
            if self.running:
                print(f"[-] Erro no servidor: {e}")
        finally:
            self.stop()

    def _handle_client(self, client_sock):
        buffer = ""
        try:
            while self.running:
                data = client_sock.recv(1024)
                if not data:
                    break
                buffer += data.decode("utf-8", errors="ignore")
                
                # Comandos ELM327 são terminados com \r ou \n
                while "\r" in buffer or "\n" in buffer:
                    delimiter = "\r" if "\r" in buffer else "\n"
                    cmd, buffer = buffer.split(delimiter, 1)
                    cmd = cmd.strip()
                    if cmd:
                        resp = self.simulator.process_command(cmd)
                        client_sock.sendall(resp.encode("utf-8"))
        except ConnectionResetError:
            pass
        finally:
            client_sock.close()
            print("[-] Conexão encerrada com o cliente.")

    def stop(self):
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass

if __name__ == "__main__":
    server = VirtualELMServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n[*] Encerrando simulador.")
        server.stop()

