# 🚗 AutoScan BR — Diagnóstico Veicular, Elétrica Automotiva & Telemetria Pro

Plataforma desktop nativa para **Windows** voltada a mecânicos, autoelétricas e entusiastas. Realiza leitura em tempo real via **ELM327 (Bluetooth e USB/COM)**, com banco de dados de tolerâncias de fábrica de mais de 45 motores brasileiros e elétricos, osciloscópio multicanal, histórico de passagens da garagem, comparação **Antes & Depois** para laudos de WhatsApp e suporte ao **Google Gemini AI**.

---

## 📥 Download do Executável (Pronto para Usar)

Não precisa instalar Python ou compilar código. Basta baixar o instalador oficial:

👉 **[⬇️ Baixar AutoScan BR para Windows (.exe)](https://github.com/ph2708/elm327_carscanner/raw/main/releases/AutoScan_BR_Setup.exe)** *(~39 MB)*

> [!NOTE]
> O executável é 100% autônomo e não inclui chaves privadas de API. Cada usuário pode configurar gratuitamente sua própria chave do Gemini pelo botão na barra lateral do app.

---

## ✨ Principais Funcionalidades

### 1. ⚖️ Comparativo Antes & Depois (Comprovação de Serviços)
* **Fotos de Telemetria (Snapshots):** Registre com 1 clique o estado do carro em momentos estratégicos:
  * ⚠️ *Entrada na Oficina (Pré-Manutenção / Com Defeito)*
  * 🧊 *Carro Frio (Chave Ligada / Partida)*
  * 🔥 *Carro Aquecido (Marcha Lenta Operacional)*
  * ✅ *Pós-Manutenção (Após Reparo / Entrega)*
* **Destaques Imediatos no Topo (KPIs):**
  * ⚡ **Elétrica/Alternador:** Identifica se o alternador começou a carregar (ex: `11.9V ➔ 14.2V`).
  * ⛽ **Mistura/Trims (STFT+LTFT):** Mostra correção de mistura rica/pobre (ex: `+19.8% ➔ +1.2%`).
  * ⚙️ **Vácuo no Coletor (MAP):** Comprova resolução de entradas falsas de ar (ex: `55 kPa ➔ 32 kPa`).
  * 🚨 **Códigos de Falha (DTCs):** Comprova eliminação de falhas ativas.
* **📄 Gerador de Laudo para WhatsApp:** Gera um texto resumido e profissional formatado para copiar e colar com 1 clique no WhatsApp do cliente da oficina.

---

### 2. 📈 Osciloscópio & Gráficos de Telemetria Multicanal
* **4 Modos de Exibição com 1 Clique:**
  * **🎛️ Multicanal:** RPM, Velocidade, Temperatura da Água, Trim Total, Tensão e Sonda Lambda.
  * **⚡ Elétrica & Alternador:** Tensão da Bateria (pino 16), Tensão de Alimentação da ECU (PID 42) com **cálculo em tempo real de queda de tensão em chicote/aterramento** e Avanço de Ignição.
  * **🔥 Injeção & Sonda:** Sonda Pré vs Pós-Catalisador, Ajuste de Curto (STFT) vs Longo Prazo (LTFT) e Trim Total vs Vácuo MAP.
  * **🌡️ Térmica & Arrefecimento:** Água, Temperatura do Ar de Admissão (IAT), Temperatura Ambiente e Óleo do Motor.
* **Escala Inteligente Travada em Zero:** Sem escalas negativas em velocidade ou RPM quando o carro está parado.
* **Legenda com Valores ao Vivo:** Exibição numérica exata de cada sensor no topo do gráfico.
* **Faixas de Fábrica:** Áreas sombreadas para tensão ideal do alternador (13.5V a 14.8V) e temperatura operacional da água (82°C a 103°C).
* **Botão `⏸ Congelar / ▶ Retomar`:** Pausa o fluxo gráfico para inspeção minuciosa de oscilações.

---

### 3. 🚗 Garagem da Oficina & Tolerâncias de Fábrica
* **Catálogo Visual com Filtro Rápido:** Busca instantânea por placa, montadora ou modelo.
* **Perfis Prontos para o Mercado Brasileiro e Elétricos:**
  * **Chevrolet:** Onix / Prisma / Tracker / Montana / Corsa (SPE/4, Ecotec, 1.0/1.2 Turbo).
  * **Volkswagen:** Gol / Fox / Polo / Virtus / T-Cross / Nivus (EA111, EA211 TSI e MSI).
  * **Fiat / Jeep:** Uno / Argo / Cronos / Pulse / Toro / Renegade (Fire, Firefly 1.0/1.3, T270 Turbo).
  * **Ford:** Ka / Fiesta / EcoSport (Sigma 1.5/1.6, Fox 1.0 3C, Duratec).
  * **Hyundai / Kia:** HB20 / Creta (Kappa 1.0 12V, 1.0 TGDI, Gamma 1.6).
  * **Renault:** Sandero / Logan / Kwid / Duster (1.0 12V B4D, 1.6 SCe).
  * **Toyota / Honda:** Corolla, Civic, Fit, City, Yaris.
  * **⚡ Elétricos & Híbridos:** BYD Dolphin / Dolphin Mini / Yuan Plus, GWM Ora 03 / Haval H6, Corolla Cross Hybrid.
* **✏️ Editor de Tolerâncias Personalizável:** Permite calibrar limites mínimos e máximos da sua oficina para qualquer parâmetro (todos os campos opcionais).

---

### 4. 🤖 Mecânico Assistente IA (Google Gemini)
* Integrado diretamente com a telemetria ao vivo do veículo conectado.
* Ao fazer uma pergunta técnica (ex: *"Alternador carregando?", "Fuga de corrente?", "Engasga ao acelerar?"*), o app injeta automaticamente a tensão, trims, vácuo e códigos de falha do carro para a IA formular um parecer técnico detalhado.
* **Modelos Gratuitos Suportados:**
  * `Gemini 2.5 Flash`
  * `Gemini 2.0 Flash`
  * `Gemini 1.5 Flash`

---

## 🔌 Como Conectar no Carro

1. Plugue o scanner **ELM327** na porta OBD-II do carro (geralmente sob o volante).
2. Ligue a chave do carro (não precisa ligar o motor se quiser ler apenas em repouso).
3. **Se o adaptador for Bluetooth:**
   * Pareie uma vez nas configurações do Windows (PIN `1234` ou `0000`).
   * No app, selecione `⭐ [OBD] OBDII (00:10:CC:4F:36:03)` e clique em **⚡ Conectar**.
4. **Se o adaptador for USB:**
   * Selecione a porta `🔌 [COM] COMx` correspondente e clique em **⚡ Conectar**.
5. **Sem o carro por perto?**
   * Clique em **🎮 Simulador** para testar todas as telas, gráficos e comparativos em modo virtual!

---

## 🔑 Como Obter e Configurar a Chave do Gemini (100% Gratuito)

1. Acesse o [Google AI Studio](https://aistudio.google.com/app/apikey) com sua conta Google.
2. Clique em **"Create API Key"** e copie sua chave.
3. No AutoScan BR, clique no botão inferior da barra lateral: **⚙️ Configurar Gemini AI**.
4. Cole sua chave e clique em **💾 Salvar Chave**. A chave fica armazenada apenas no seu computador (`~/.autoscan_br_config.json`).

---

## 🛠️ Como Compilar a Partir do Código Fonte (Desenvolvedores)

Se desejar alterar o código Python e compilar seu próprio executável:

```powershell
# 1. Clonar o repositório
git clone https://github.com/ph2708/elm327_carscanner.git
cd elm327_carscanner

# 2. Instalar dependências
pip install customtkinter bleak pyserial matplotlib google-genai

# 3. Executar em modo desenvolvimento
python app_windows.py

# 4. Gerar o executável
python -m PyInstaller --noconfirm --onedir --windowed --name "AutoScanBR" app_windows.py

# 5. Ou utilize o script automático:
.\compilar_nova_versao.bat
```

---

## 📜 Licença

Distribuído sob a licença MIT. Livre para uso comercial e adaptação em oficinas mecânicas.
