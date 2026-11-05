# AutoScan BR — Diagnóstico & Telemetria Automotiva

Plataforma profissional de diagnóstico veicular OBD-II com análise inteligente e suporte ao **Google Gemini AI**.

---

## 🚀 Como Iniciar no Windows (1 Clique)

1. Conecte seu adaptador **ELM327** na porta USB ou pareie via Bluetooth no Windows (código `1234`).
2. Dê duplo clique no arquivo:
   ```cmd
   iniciar_autoscan_windows.bat
   ```
3. O painel web abrirá automaticamente em `http://127.0.0.1:8000`.
4. Escolha **[1]** para conectar no carro (detecção automática de portas `COM`) ou **[2]** para o **Simulador Virtual**.

---

## 🌐 Como Rodar Manualmente (Linux / macOS / Windows Terminal)

### 1. Iniciar o Painel Web (Laravel):
```bash
cd backend
php -S 127.0.0.1:8000 -t public
```

### 2. Iniciar o Coletor:

- **Modo Simulador (Sem Carro):**
  ```bash
  python3 -m collector.app.main --mode simulator
  ```

- **Modo Real no Veículo (Ford New Fiesta 1.5):**
  ```bash
  python3 -m collector.app.main --mode serial
  ```

---

## 🤖 Configurar Chave do Google Gemini (Gratuito)

1. Abra o navegador em `http://127.0.0.1:8000/settings`.
2. Insira sua chave obtida gratuitamente no [Google AI Studio](https://aistudio.google.com/app/apikey).
3. Clique em **"⚡ Testar Conexão"** e depois em **"Salvar Alterações"**.
4. No Dashboard, clique em **"Análise com Gemini AI"** para gerar laudos técnicos explicativos completos com testes práticos de bancada.

