"""
AutoScan BR - Aplicativo Nativo Windows (Desktop Pro - Oficina Elétrica & Injeção)

Layout:
- Menu lateral fixo (navegação por páginas, não corta em telas pequenas)
- Barra superior de conexão (adaptador, simulador, status, test-drive, DTC)
- Páginas:
    1. Garagem (busca + seleção do veículo ANTES de conectar)
    2. Painel (visão geral com faixas de fábrica e alertas)
    3. Dados ao Vivo (lista completa de parâmetros/tensões com mín/máx e status)
    4. Assistente IA (elétrica automotiva com telemetria injetada)
    5. Gráficos (ao vivo dos últimos 60 s ou do último test-drive)
    6. Laudo do Test-Drive
    7. Histórico do veículo
    8. Manual de Tolerâncias (somente leitura)
"""

import os
import csv
import time
import json
import threading
import asyncio
from collections import deque

import customtkinter as ctk
import tkinter.messagebox as msgbox
import tkinter.filedialog as filedialog
from bleak import BleakScanner
import serial.tools.list_ports

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from collector.app.connection.native_client import NativeELMClient
from collector.app.simulator.elm_simulator import ELM327Simulator
from collector.app.diagnostic.test_drive_analyzer import TestDriveDiagnosticAnalyzer
from collector.app.diagnostic.vehicle_specs import (
    VEHICLE_PROFILES_DATABASE, DIAGNOSTIC_HELP_GUIDE,
    load_all_vehicle_profiles, save_custom_profile, delete_custom_profile
)
from collector.app.diagnostic.garage_manager import GarageProfileManager
from collector.app.diagnostic.ai_electric_assistant import ElectricalAIAssistant

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".autoscan_br_config.json")
DEFAULT_MAC = "00:10:CC:4F:36:03"

# Paleta
BG = "#0b1120"
PANEL = "#111827"
CARD = "#162033"
BORDER = "#1f2a3d"
ACCENT = "#38bdf8"
GREEN = "#22c55e"
RED = "#ef4444"
AMBER = "#f59e0b"
MUTED = "#94a3b8"
SIDEBAR = "#0f172a"


def F(size=12, bold=False, mono=False):
    return ctk.CTkFont(family="Consolas" if mono else None, size=size, weight="bold" if bold else "normal")


# Definição de todos os parâmetros exibidos (chave, rótulo, unidade, formato, seção, escala da barra)
PARAMS = [
    # Elétrica
    ("battery_voltage", "Tensão Bateria / Alternador (pino 16)", "V", "{:.1f}", "⚡ ELÉTRICA & SENSORES", (10, 16)),
    ("ecu_voltage", "Tensão de Alimentação do Módulo (PID 42)", "V", "{:.2f}", "⚡ ELÉTRICA & SENSORES", (10, 16)),
    ("o2_b1s1", "Sonda Lambda Pré-Cat (B1S1)", "V", "{:.2f}", "⚡ ELÉTRICA & SENSORES", (0, 1)),
    ("o2_b1s2", "Sonda Lambda Pós-Cat (B1S2)", "V", "{:.3f}", "⚡ ELÉTRICA & SENSORES", (0, 1)),
    ("tps", "Posição da Borboleta (TPS)", "%", "{:.1f}", "⚡ ELÉTRICA & SENSORES", (0, 100)),
    # Motor
    ("rpm", "Rotação do Motor", "RPM", "{:.0f}", "⚙️ MOTOR", (0, 7000)),
    ("engine_load", "Carga Calculada do Motor", "%", "{:.0f}", "⚙️ MOTOR", (0, 100)),
    ("map_kpa", "Pressão do Coletor (MAP)", "kPa", "{:.0f}", "⚙️ MOTOR", (10, 105)),
    ("maf_gs", "Fluxo de Ar (MAF)", "g/s", "{:.2f}", "⚙️ MOTOR", (0, 60)),
    ("timing_advance", "Avanço de Ignição", "°", "{:.1f}", "⚙️ MOTOR", (-10, 45)),
    ("speed", "Velocidade", "km/h", "{:.0f}", "⚙️ MOTOR", (0, 200)),
    # Temperaturas
    ("coolant_temp", "Temperatura do Líquido de Arrefecimento", "°C", "{:.0f}", "🌡️ TEMPERATURAS & AMBIENTE", (0, 120)),
    ("intake_temp", "Temperatura do Ar de Admissão (IAT)", "°C", "{:.0f}", "🌡️ TEMPERATURAS & AMBIENTE", (-10, 80)),
    ("baro_kpa", "Pressão Barométrica", "kPa", "{:.0f}", "🌡️ TEMPERATURAS & AMBIENTE", (60, 105)),
    ("fuel_level", "Nível de Combustível", "%", "{:.0f}", "🌡️ TEMPERATURAS & AMBIENTE", (0, 100)),
    # Mistura
    ("stft_b1", "Ajuste Curto Prazo (STFT B1)", "%", "{:+.1f}", "🔥 MISTURA AR/COMBUSTÍVEL", (-25, 25)),
    ("ltft_b1", "Ajuste Longo Prazo (LTFT B1)", "%", "{:+.1f}", "🔥 MISTURA AR/COMBUSTÍVEL", (-25, 25)),
    ("trim_total", "Ajuste Total (STFT + LTFT)", "%", "{:+.1f}", "🔥 MISTURA AR/COMBUSTÍVEL", (-25, 25)),
]
PARAM_BY_KEY = {p[0]: p for p in PARAMS}

PAGES = [
    ("garage", "🚗  Garagem"),
    ("dashboard", "📊  Painel"),
    ("live", "📋  Dados ao Vivo"),
    ("ai", "🤖  Assistente IA"),
    ("charts", "📈  Gráficos"),
    ("report", "📑  Laudo Test-Drive"),
    ("history", "🗂️  Histórico"),
    ("manual", "📖  Manual"),
]


class AutoScanWindowsApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AutoScan BR — Diagnóstico Veicular, Elétrica Automotiva & Telemetria")
        self.geometry("1280x780")
        self.minsize(980, 600)
        self.configure(fg_color=BG)

        # Conexão
        self.client = None
        self.client_lock = threading.Lock()
        self.simulator = None
        self.is_connected = False
        self.is_running = False
        self.connection_aborted = False
        self.connecting_client = None

        # Pré-inicializa dispositivos para disponibilidade imediata (sem esperar scan)
        self.discovered_devices = {
            f"⭐ [OBD] OBDII ({DEFAULT_MAC})": {"type": "BT", "address": DEFAULT_MAC, "name": "OBDII"}
        }
        try:
            for p in serial.tools.list_ports.comports():
                label = f"🔌 [COM] {p.device} - {p.description}"
                self.discovered_devices[label] = {"type": "COM", "address": p.device, "name": p.description}
        except Exception:
            pass

        self.latest_telemetry = {}
        self.session_frames = deque(maxlen=3000)
        self.minmax = {}

        # Test-drive
        self.is_recording = False
        self.recorded_frames = []
        self.record_start_time = None
        self.last_analysis_result = None

        # Gráficos
        self.chart_mode_live = True

        # Garagem
        self.garage_db = GarageProfileManager.load_database()
        vehicles = self.garage_db.get("vehicles", {})
        self.active_plate = self.garage_db.get("selected_plate", "")
        self.active_vehicle = GarageProfileManager.get_vehicle(self.active_plate) if self.active_plate else None
        if not self.active_vehicle and vehicles:
            self.active_vehicle = list(vehicles.values())[0]
            self.active_plate = self.active_vehicle["plate"]
        if not self.active_vehicle:
            self.active_vehicle = GarageProfileManager.save_or_update_vehicle(
                "SEM-PLACA", "GENERIC_OBD2", VEHICLE_PROFILES_DATABASE["GENERIC_OBD2"]["name"], "", "0", "")
            self.active_plate = "SEM-PLACA"
        self.active_model_key = self.active_vehicle.get("model_key", "GENERIC_OBD2")
        self._load_tolerances()

        self.gemini_api_key = self._load_config().get("gemini_api_key", "")
        self.current_page = None

        self._build_ui()
        self._show_page("garage")
        self._start_device_discovery(initial=True)
        self.after(1000, self._live_chart_tick)
        self.after(100, lambda: self.state("zoomed"))

    # ==========================================================
    # CONFIG
    # ==========================================================
    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_config(self):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump({"gemini_api_key": self.gemini_api_key}, f)
        except Exception:
            pass

    def _load_tolerances(self):
        all_specs = load_all_vehicle_profiles()
        spec = all_specs.get(self.active_model_key, VEHICLE_PROFILES_DATABASE.get("GENERIC_OBD2"))
        self.active_spec = spec
        self.active_tolerances = spec["tolerances"]

    # ==========================================================
    # ESTRUTURA PRINCIPAL
    # ==========================================================
    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()

        main = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        self._build_topbar(main)

        self.content = ctk.CTkFrame(main, fg_color=BG, corner_radius=0)
        self.content.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self.pages = {}
        for key, _ in PAGES:
            page = ctk.CTkFrame(self.content, fg_color="transparent", corner_radius=0)
            page.grid(row=0, column=0, sticky="nsew")
            self.pages[key] = page

        self._build_garage_page(self.pages["garage"])
        self._build_dashboard_page(self.pages["dashboard"])
        self._build_live_page(self.pages["live"])
        self._build_ai_page(self.pages["ai"])
        self._build_charts_page(self.pages["charts"])
        self._build_report_page(self.pages["report"])
        self._build_history_page(self.pages["history"])
        self._build_manual_page(self.pages["manual"])

    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, width=210, corner_radius=0, fg_color=SIDEBAR)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)
        sb.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(sb, text="🚗 AutoScan BR", font=F(19, True)).grid(row=0, column=0, padx=16, pady=(14, 0), sticky="w")
        ctk.CTkLabel(sb, text="Oficina Pro • Elétrica & Injeção", font=F(10), text_color=ACCENT).grid(row=1, column=0, padx=16, pady=(0, 10), sticky="w")

        # Cartão do veículo ativo
        vcard = ctk.CTkFrame(sb, fg_color=CARD, corner_radius=10, border_width=1, border_color=BORDER)
        vcard.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        vcard.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(vcard, text="VEÍCULO ATIVO", font=F(9, True), text_color=AMBER).grid(row=0, column=0, padx=10, pady=(8, 0), sticky="w")
        self.sb_plate = ctk.CTkLabel(vcard, text="", font=F(16, True))
        self.sb_plate.grid(row=1, column=0, padx=10, sticky="w")
        self.sb_model = ctk.CTkLabel(vcard, text="", font=F(10), text_color=MUTED, wraplength=170, justify="left")
        self.sb_model.grid(row=2, column=0, padx=10, sticky="w")
        ctk.CTkButton(vcard, text="Trocar veículo", height=24, font=F(11), fg_color="#1e293b", hover_color="#334155",
                      command=lambda: self._show_page("garage")).grid(row=3, column=0, padx=10, pady=(6, 10), sticky="ew")

        # Navegação
        self.nav_buttons = {}
        for i, (key, label) in enumerate(PAGES):
            btn = ctk.CTkButton(sb, text=label, anchor="w", height=34, corner_radius=8, font=F(13),
                                fg_color="transparent", hover_color="#1e293b", text_color="#e2e8f0",
                                command=lambda k=key: self._show_page(k))
            btn.grid(row=3 + i, column=0, padx=10, pady=1, sticky="ew")
            self.nav_buttons[key] = btn

        sb.grid_rowconfigure(3 + len(PAGES), weight=1)
        ctk.CTkButton(sb, text="⚙️  Configurar Gemini AI", anchor="w", height=30, font=F(12),
                      fg_color="#1e293b", hover_color="#334155",
                      command=self._open_ai_config_dialog).grid(row=4 + len(PAGES), column=0, padx=10, pady=(4, 12), sticky="ew")

        self._update_sidebar_vehicle()

    def _build_topbar(self, parent):
        bar = ctk.CTkFrame(parent, fg_color=PANEL, corner_radius=10, border_width=1, border_color=BORDER)
        bar.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        bar.grid_columnconfigure(5, weight=1)

        init_values = list(self.discovered_devices.keys())
        self.combo_devices = ctk.CTkComboBox(bar, values=init_values, width=250, height=32, font=F(12))
        self.combo_devices.grid(row=0, column=0, padx=(10, 4), pady=10)
        if init_values:
            self.combo_devices.set(init_values[0])

        self.btn_scan = ctk.CTkButton(bar, text="🔍", width=34, height=32, fg_color="#334155", hover_color="#475569",
                                      command=self._start_device_discovery)
        self.btn_scan.grid(row=0, column=1, padx=2)

        self.btn_connect = ctk.CTkButton(bar, text="⚡ Conectar", width=110, height=32, font=F(12, True),
                                         fg_color="#2563eb", hover_color="#1d4ed8", command=self._toggle_connection)
        self.btn_connect.grid(row=0, column=2, padx=(6, 2))

        self.btn_cancel_connect = ctk.CTkButton(bar, text="✖ Abortar", width=95, height=32, font=F(12, True),
                                               fg_color="#dc2626", hover_color="#b91c1c", state="disabled",
                                               command=self._cancel_connection)
        self.btn_cancel_connect.grid(row=0, column=3, padx=2)

        self.btn_sim = ctk.CTkButton(bar, text="🎮 Simulador", width=105, height=32, font=F(12),
                                     fg_color="#0f766e", hover_color="#115e59", command=self._toggle_simulator)
        self.btn_sim.grid(row=0, column=4, padx=2)

        st = ctk.CTkFrame(bar, fg_color="transparent")
        st.grid(row=0, column=5, sticky="w", padx=12)
        self.lbl_status = ctk.CTkLabel(st, text="● Desconectado", font=F(12, True), text_color=RED)
        self.lbl_status.grid(row=0, column=0, sticky="w")
        self.lbl_protocol = ctk.CTkLabel(st, text="Protocolo: --", font=F(10), text_color=MUTED)
        self.lbl_protocol.grid(row=1, column=0, sticky="w")

        self.lbl_record_status = ctk.CTkLabel(bar, text="", font=F(11), text_color=MUTED)
        self.lbl_record_status.grid(row=0, column=6, padx=6)

        self.btn_record = ctk.CTkButton(bar, text="▶ Test-Drive", width=115, height=32, font=F(12, True),
                                        fg_color="#16a34a", hover_color="#15803d", state="disabled",
                                        command=self._toggle_test_drive)
        self.btn_record.grid(row=0, column=7, padx=2)

        self.btn_read_dtc = ctk.CTkButton(bar, text="⚠️ Falhas", width=90, height=32, font=F(12),
                                          fg_color="#d97706", hover_color="#b45309", state="disabled",
                                          command=self._read_dtcs_dialog)
        self.btn_read_dtc.grid(row=0, column=8, padx=(2, 10))

    def _show_page(self, key):
        self.current_page = key
        self.pages[key].tkraise()
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(fg_color="#1e3a5f", text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color="#cbd5e1")
        if key == "charts":
            self._redraw_charts_now()
        if key == "live" and self.latest_telemetry:
            self._update_live_table(self.latest_telemetry)

    def _page_header(self, parent, title, subtitle=""):
        hdr = ctk.CTkFrame(parent, fg_color="transparent")
        hdr.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 8))
        lbl = ctk.CTkLabel(hdr, text=title, font=F(16, True))
        lbl.pack(anchor="w")
        sub = None
        if subtitle:
            sub = ctk.CTkLabel(hdr, text=subtitle, font=F(11), text_color=MUTED)
            sub.pack(anchor="w")
        return hdr, lbl, sub

    @staticmethod
    def _set_readonly_text(textbox, text):
        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        textbox.insert("1.0", text)
        textbox.configure(state="disabled")

    # ==========================================================
    # PÁGINA 1: GARAGEM
    # ==========================================================
    def _build_garage_page(self, page):
        page.grid_columnconfigure(0, weight=0, minsize=300)
        page.grid_columnconfigure(1, weight=1)
        page.grid_rowconfigure(1, weight=1)

        self._page_header(page, "Garagem da Oficina", "1) Pesquise e clique no veículo   2) Confira o perfil de fábrica   3) Conecte o scanner")

        # ---- Lista
        left = ctk.CTkFrame(page, fg_color=PANEL, corner_radius=10, border_width=1, border_color=BORDER, width=300)
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        left.grid_propagate(False)
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(2, weight=1)

        sfr = ctk.CTkFrame(left, fg_color="transparent")
        sfr.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))
        sfr.grid_columnconfigure(0, weight=1)
        self.entry_search_vehicle = ctk.CTkEntry(sfr, placeholder_text="🔍 Placa, modelo ou cliente...", height=34)
        self.entry_search_vehicle.grid(row=0, column=0, sticky="ew")
        self.entry_search_vehicle.bind("<KeyRelease>", lambda e: self._populate_vehicle_cards())
        ctk.CTkButton(sfr, text="✖", width=34, height=34, fg_color="#334155", hover_color="#475569",
                      command=self._clear_vehicle_search).grid(row=0, column=1, padx=(6, 0))

        self.lbl_vehicle_count = ctk.CTkLabel(left, text="", font=F(11), text_color=MUTED)
        self.lbl_vehicle_count.grid(row=1, column=0, sticky="w", padx=12)

        self.scroll_vehicles = ctk.CTkScrollableFrame(left, fg_color="transparent")
        self.scroll_vehicles.grid(row=2, column=0, sticky="nsew", padx=6, pady=(2, 6))

        ctk.CTkButton(left, text="➕ Cadastrar novo veículo", height=34, font=F(12, True),
                      fg_color="#0f766e", hover_color="#115e59",
                      command=self._new_vehicle_form).grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))

        # ---- Detalhe
        right = ctk.CTkScrollableFrame(page, fg_color=PANEL, corner_radius=10, border_width=1, border_color=BORDER)
        right.grid(row=1, column=1, sticky="nsew")
        right.grid_columnconfigure((0, 1), weight=1)

        head = ctk.CTkFrame(right, fg_color="transparent")
        head.grid(row=0, column=0, columnspan=2, sticky="ew", padx=14, pady=(12, 4))
        head.grid_columnconfigure(0, weight=1)
        self.lbl_detail_plate = ctk.CTkLabel(head, text="", font=F(24, True), text_color="#facc15")
        self.lbl_detail_plate.grid(row=0, column=0, sticky="w")
        self.lbl_detail_badge = ctk.CTkLabel(head, text="", font=F(10, True), corner_radius=6, fg_color="#14532d",
                                             text_color="#bbf7d0", width=110, height=24)
        self.lbl_detail_badge.grid(row=0, column=1, sticky="e")
        self.lbl_detail_model = ctk.CTkLabel(head, text="", font=F(12), text_color=MUTED)
        self.lbl_detail_model.grid(row=1, column=0, columnspan=2, sticky="w")

        def field(row, col, label, widget_factory, span=1):
            box = ctk.CTkFrame(right, fg_color="transparent")
            box.grid(row=row, column=col, columnspan=span, sticky="ew", padx=14, pady=4)
            box.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(box, text=label, font=F(11, True), text_color=MUTED).grid(row=0, column=0, sticky="w")
            w = widget_factory(box)
            w.grid(row=1, column=0, sticky="ew")
            return w

        self.model_options = {v["name"]: k for k, v in load_all_vehicle_profiles().items()}
        self.f_plate = field(1, 0, "Placa", lambda p: ctk.CTkEntry(p, height=32, placeholder_text="ABC1D23"))
        self.f_year = field(1, 1, "Ano", lambda p: ctk.CTkEntry(p, height=32, placeholder_text="2018"))

        # Seleção de Motorização com botões de IA e Ajuste Manual
        model_box = ctk.CTkFrame(right, fg_color="transparent")
        model_box.grid(row=2, column=0, columnspan=2, sticky="ew", padx=14, pady=4)
        model_box.grid_columnconfigure(0, weight=1)

        m_top = ctk.CTkFrame(model_box, fg_color="transparent")
        m_top.grid(row=0, column=0, sticky="ew")
        m_top.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(m_top, text="Motorização / Perfil de calibração", font=F(11, True), text_color=MUTED).grid(row=0, column=0, sticky="w")

        btn_ai_model = ctk.CTkButton(
            m_top, text="✨ Gerar Perfil com IA", width=145, height=22, font=F(11, True),
            fg_color="#8b5cf6", hover_color="#7c3aed",
            command=self._open_ai_profile_generator_dialog
        )
        btn_ai_model.grid(row=0, column=1, padx=(0, 4))

        btn_edit_tol = ctk.CTkButton(
            m_top, text="✏️ Ajustar Tolerâncias", width=140, height=22, font=F(11),
            fg_color="#334155", hover_color="#475569",
            command=self._open_edit_tolerances_dialog
        )
        btn_edit_tol.grid(row=0, column=2)

        self.f_model = ctk.CTkComboBox(
            model_box, height=32, values=list(self.model_options.keys()),
            command=self._update_model_preview
        )
        self.f_model.grid(row=1, column=0, sticky="ew", pady=(3, 0))

        self.f_km = field(3, 0, "Quilometragem", lambda p: ctk.CTkEntry(p, height=32, placeholder_text="75000"))
        self.f_customer = field(3, 1, "Cliente / Proprietário", lambda p: ctk.CTkEntry(p, height=32, placeholder_text="Nome do cliente"))

        # Tolerâncias de fábrica do perfil
        ctk.CTkLabel(right, text="TOLERÂNCIAS DE FÁBRICA DESTE PERFIL", font=F(11, True), text_color=AMBER).grid(
            row=4, column=0, columnspan=2, sticky="w", padx=14, pady=(12, 2))
        chips = ctk.CTkFrame(right, fg_color="transparent")
        chips.grid(row=5, column=0, columnspan=2, sticky="ew", padx=10)
        chips.grid_columnconfigure((0, 1, 2), weight=1)
        self.tol_chips = {}
        chip_defs = [("idle_rpm", "Marcha lenta"), ("idle_map", "MAP em lenta"), ("coolant_temp", "Temperatura"),
                     ("idle_tps", "TPS em lenta"), ("fuel_trim_total", "Trim total"), ("battery_voltage", "Carga alternador")]
        for i, (k, title) in enumerate(chip_defs):
            c = ctk.CTkFrame(chips, fg_color=CARD, corner_radius=8, border_width=1, border_color=BORDER)
            c.grid(row=i // 3, column=i % 3, sticky="ew", padx=4, pady=4)
            ctk.CTkLabel(c, text=title, font=F(10), text_color=MUTED).pack(anchor="w", padx=10, pady=(6, 0))
            v = ctk.CTkLabel(c, text="--", font=F(14, True))
            v.pack(anchor="w", padx=10, pady=(0, 6))
            self.tol_chips[k] = v

        self.lbl_profile_tip = ctk.CTkLabel(right, text="", font=F(11), text_color="#cbd5e1", wraplength=560, justify="left")
        self.lbl_profile_tip.grid(row=6, column=0, columnspan=2, sticky="w", padx=14, pady=(8, 4))

        # Ações
        ctk.CTkButton(right, text="⚡ USAR ESTE VEÍCULO E CONECTAR", height=44, font=F(14, True),
                      fg_color="#16a34a", hover_color="#15803d",
                      command=self._apply_and_go_connect).grid(row=7, column=0, columnspan=2, sticky="ew", padx=14, pady=(12, 6))
        acts = ctk.CTkFrame(right, fg_color="transparent")
        acts.grid(row=8, column=0, columnspan=2, sticky="ew", padx=14, pady=(0, 14))
        acts.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(acts, text="💾 Salvar alterações", height=34, fg_color="#2563eb", hover_color="#1d4ed8",
                      command=self._save_vehicle_from_form).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ctk.CTkButton(acts, text="🗑️ Excluir veículo", height=34, fg_color="#7f1d1d", hover_color="#991b1b",
                      command=self._delete_vehicle_from_form).grid(row=0, column=1, sticky="ew", padx=(4, 0))

        self._populate_vehicle_cards()
        self._load_vehicle_into_form(self.active_vehicle)

    def _clear_vehicle_search(self):
        self.entry_search_vehicle.delete(0, "end")
        self._populate_vehicle_cards()

    @staticmethod
    def _fmt_km(km):
        try:
            return f"{int(float(str(km).replace('.', '').replace(',', ''))):,}".replace(",", ".") + " km"
        except (ValueError, TypeError):
            return "-- km"

    def _bind_click_recursive(self, widget, callback):
        try:
            widget.bind("<Button-1>", callback)
        except Exception:
            pass
        for child in widget.winfo_children():
            self._bind_click_recursive(child, callback)

    def _populate_vehicle_cards(self):
        for w in self.scroll_vehicles.winfo_children():
            w.destroy()

        vehicles = GarageProfileManager.get_all_vehicles()
        term = self.entry_search_vehicle.get().strip().lower() if hasattr(self, "entry_search_vehicle") else ""
        shown = 0

        for plate, v in vehicles.items():
            model = v.get("model_name", "")
            cust = v.get("customer_name", "")
            if term and term not in f"{plate} {model} {cust}".lower():
                continue
            shown += 1
            active = plate.upper() == self.active_plate.upper()

            card = ctk.CTkFrame(self.scroll_vehicles, corner_radius=8, border_width=2,
                                fg_color="#1e293b" if active else CARD,
                                border_color=ACCENT if active else BORDER)
            card.pack(fill="x", pady=3, padx=2)
            card.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(card, text=plate, font=F(15, True), text_color="#facc15" if active else "white").grid(
                row=0, column=0, sticky="w", padx=10, pady=(6, 0))
            if active:
                ctk.CTkLabel(card, text="● ATIVO", font=F(10, True), text_color=ACCENT).grid(row=0, column=1, sticky="e", padx=10)
            short_model = model if len(model) <= 38 else model[:36] + "…"
            ctk.CTkLabel(card, text=short_model, font=F(11), text_color="#cbd5e1").grid(
                row=1, column=0, columnspan=2, sticky="w", padx=10)
            info = f"{cust or 'Sem cliente'}  •  {v.get('year') or '----'}  •  {self._fmt_km(v.get('km'))}"
            ctk.CTkLabel(card, text=info, font=F(10), text_color=MUTED).grid(
                row=2, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 6))

            self._bind_click_recursive(card, lambda e, p=plate: self.after(10, lambda: self._select_vehicle_by_plate(p)))

        total = len(vehicles)
        self.lbl_vehicle_count.configure(text=f"{shown} de {total} veículo(s) • clique para ativar")
        if shown == 0:
            ctk.CTkLabel(self.scroll_vehicles, text="Nenhum veículo encontrado.", text_color="gray50").pack(pady=20)

    def _load_vehicle_into_form(self, veh):
        if not veh:
            return
        for e in (self.f_plate, self.f_year, self.f_km, self.f_customer):
            e.delete(0, "end")
        self.f_plate.insert(0, veh.get("plate", ""))
        self.f_year.insert(0, str(veh.get("year", "") or ""))
        self.f_km.insert(0, str(veh.get("km", "") or ""))
        self.f_customer.insert(0, str(veh.get("customer_name", "") or ""))
        m_key = veh.get("model_key", "GENERIC_OBD2")
        m_name = VEHICLE_PROFILES_DATABASE.get(m_key, VEHICLE_PROFILES_DATABASE["GENERIC_OBD2"])["name"]
        self.f_model.set(m_name)
        self._update_model_preview(m_name)

        is_active = veh.get("plate", "").upper() == self.active_plate.upper()
        self.lbl_detail_plate.configure(text=veh.get("plate", ""))
        self.lbl_detail_model.configure(text=veh.get("model_name", ""))
        self.lbl_detail_badge.configure(text="✔ PERFIL ATIVO" if is_active else "",
                                        fg_color="#14532d" if is_active else "transparent")

    def _new_vehicle_form(self):
        for e in (self.f_plate, self.f_year, self.f_km, self.f_customer):
            e.delete(0, "end")
        gen = VEHICLE_PROFILES_DATABASE["GENERIC_OBD2"]["name"]
        self.f_model.set(gen)
        self._update_model_preview(gen)
        self.lbl_detail_plate.configure(text="NOVO VEÍCULO")
        self.lbl_detail_model.configure(text="Preencha os dados e clique em Salvar")
        self.lbl_detail_badge.configure(text="", fg_color="transparent")
        self.f_plate.focus_set()

    def _update_model_preview(self, model_display_name):
        all_specs = load_all_vehicle_profiles()
        key = self.model_options.get(model_display_name, "GENERIC_OBD2")
        spec = all_specs.get(key, VEHICLE_PROFILES_DATABASE.get("GENERIC_OBD2"))
        tols = spec["tolerances"]
        for k, lbl in self.tol_chips.items():
            t = tols.get(k)
            if k == "battery_voltage" and not t:
                t = {"min": 13.5, "max": 14.8, "unit": "V"}
            if t:
                lbl.configure(text=f"{t['min']} – {t['max']} {t['unit']}")
            else:
                lbl.configure(text="--")
        tip = spec.get("tips", [""])[0] if spec.get("tips") else ""
        self.lbl_profile_tip.configure(text=f"💡 {tip}" if tip else "")

    def _open_ai_profile_generator_dialog(self):
        win = ctk.CTkToplevel(self)
        win.title("Gerar Perfil Técnico com IA (Google Gemini)")
        win.geometry("520x330")
        win.resizable(False, False)
        win.transient(self)
        win.after(100, win.grab_set)

        ctk.CTkLabel(win, text="✨ Gerar Calibração de Fábrica com IA", font=F(16, True)).pack(pady=(16, 4))
        ctk.CTkLabel(win, text="Digite a marca, modelo, ano e motorização do veículo.\nA IA pesquisará os parâmetros e limites nominais de injeção e elétrica.",
                     font=F(11), text_color=MUTED, justify="center").pack(pady=(0, 14))

        box = ctk.CTkFrame(win, fg_color="transparent")
        box.pack(fill="x", padx=25)
        box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(box, text="Nome do Modelo / Motor:", font=F(11, True), text_color=MUTED).grid(row=0, column=0, sticky="w")
        entry_car = ctk.CTkEntry(box, placeholder_text="Ex: Jeep Compass 1.3 Turbo T270 Flex 2022", height=38, font=F(13))
        entry_car.grid(row=1, column=0, sticky="ew", pady=(4, 12))

        lbl_status = ctk.CTkLabel(win, text="", font=F(11), text_color=AMBER)
        lbl_status.pack(pady=4)

        btn_run = ctk.CTkButton(win, text="🚀 Pesquisar Tolerâncias com IA", height=42, font=F(13, True),
                                fg_color="#8b5cf6", hover_color="#7c3aed")
        btn_run.pack(pady=10, fill="x", padx=25)

        def run_ai():
            query = entry_car.get().strip()
            if not query:
                msgbox.showwarning("Aviso", "Informe o modelo do veículo.")
                return

            btn_run.configure(state="disabled", text="⏳ Consultando IA...")
            lbl_status.configure(text="Acessando especificações nominais de fábrica...")

            def worker():
                data, msg = ElectricalAIAssistant.generate_vehicle_tolerances(query, gemini_key=self.gemini_api_key)

                def update_done():
                    btn_run.configure(state="normal", text="🚀 Pesquisar Tolerâncias com IA")
                    if data and "tolerances" in data:
                        # Salva o novo perfil no JSON local de customizações
                        clean_key = "USER_" + "".join(c for c in data.get("name", query) if c.isalnum()).upper()[:24]
                        save_custom_profile(clean_key, data)

                        # Atualiza a lista da combobox
                        all_profiles = load_all_vehicle_profiles()
                        self.model_options = {v["name"]: k for k, v in all_profiles.items()}
                        self.f_model.configure(values=list(self.model_options.keys()))
                        self.f_model.set(data["name"])
                        self._update_model_preview(data["name"])

                        win.destroy()
                        msgbox.showinfo("Perfil Criado", f"Perfil '{data['name']}' gerado e salvo com sucesso na biblioteca da oficina!")
                    else:
                        lbl_status.configure(text="Erro ao gerar perfil.")
                        msgbox.showerror("Erro Gemini AI", f"Não foi possível obter dados técnicos:\n{msg}")

                self.after(0, update_done)

            threading.Thread(target=worker, daemon=True).start()

        btn_run.configure(command=run_ai)
        entry_car.bind("<Return>", lambda e: run_ai())
        entry_car.focus_set()

    def _open_edit_tolerances_dialog(self):
        curr_name = self.f_model.get()
        all_specs = load_all_vehicle_profiles()
        key = self.model_options.get(curr_name, "GENERIC_OBD2")
        spec = all_specs.get(key, VEHICLE_PROFILES_DATABASE.get("GENERIC_OBD2"))
        tols = spec.get("tolerances", {})

        win = ctk.CTkToplevel(self)
        win.title(f"Ajustar Tolerâncias — {curr_name[:30]}")
        win.geometry("560x540")
        win.resizable(False, False)
        win.transient(self)
        win.after(100, win.grab_set)

        ctk.CTkLabel(win, text="✏️ Ajustar Tolerâncias de Fábrica da Oficina", font=F(15, True)).pack(pady=(14, 2))
        ctk.CTkLabel(win, text=f"Perfil: {curr_name}\nAltere os valores nominais de alerta conforme a calibração desejada.",
                     font=F(11), text_color=MUTED, justify="center").pack(pady=(0, 10))

        scroll = ctk.CTkScrollableFrame(win, height=320, fg_color=PANEL, corner_radius=10, border_width=1, border_color=BORDER)
        scroll.pack(fill="both", expand=True, padx=20, pady=5)
        scroll.grid_columnconfigure(0, weight=2)
        scroll.grid_columnconfigure((1, 2), weight=1)

        ctk.CTkLabel(scroll, text="Parâmetro", font=F(11, True), text_color=MUTED).grid(row=0, column=0, sticky="w", padx=6, pady=4)
        ctk.CTkLabel(scroll, text="Mínimo", font=F(11, True), text_color=MUTED).grid(row=0, column=1, padx=6, pady=4)
        ctk.CTkLabel(scroll, text="Máximo", font=F(11, True), text_color=MUTED).grid(row=0, column=2, padx=6, pady=4)

        edit_entries = {}
        row = 1
        fields_to_edit = [
            ("idle_rpm", "Marcha Lenta (RPM)"),
            ("idle_map", "Vácuo MAP Lenta (kPa)"),
            ("coolant_temp", "Temperatura Água (°C)"),
            ("idle_tps", "Abertura Borboleta TPS (%)"),
            ("fuel_trim_total", "Trim Combustível Total (±%)"),
            ("battery_voltage", "Tensão Alternador Carga (V)"),
        ]

        for k, lbl in fields_to_edit:
            t = tols.get(k, {"min": 0, "max": 0})
            ctk.CTkLabel(scroll, text=lbl, font=F(12), anchor="w").grid(row=row, column=0, sticky="w", padx=6, pady=6)

            e_min = ctk.CTkEntry(scroll, width=80, height=30)
            e_min.insert(0, str(t.get("min", "")))
            e_min.grid(row=row, column=1, padx=6, pady=6)

            e_max = ctk.CTkEntry(scroll, width=80, height=30)
            e_max.insert(0, str(t.get("max", "")))
            e_max.grid(row=row, column=2, padx=6, pady=6)

            edit_entries[k] = (e_min, e_max)
            row += 1

        bottom = ctk.CTkFrame(win, fg_color="transparent")
        bottom.pack(fill="x", padx=20, pady=12)
        bottom.grid_columnconfigure((0, 1), weight=1)

        def save_adjustments():
            try:
                new_spec = dict(spec)
                new_tols = dict(new_spec.get("tolerances", {}))
                for k, (e_min, e_max) in edit_entries.items():
                    val_min = float(e_min.get().strip().replace(",", "."))
                    val_max = float(e_max.get().strip().replace(",", "."))
                    if k not in new_tols:
                        new_tols[k] = {"desc": k, "unit": ""}
                    new_tols[k]["min"] = val_min
                    new_tols[k]["max"] = val_max
                new_spec["tolerances"] = new_tols

                save_custom_profile(key, new_spec)
                self._load_tolerances()
                self._update_model_preview(curr_name)
                win.destroy()
                msgbox.showinfo("Sucesso", f"Calibrações do perfil '{curr_name}' salvas com sucesso!")
            except ValueError:
                msgbox.showwarning("Aviso", "Por favor, digite números válidos em todos os campos.")

        def restore_defaults():
            if msgbox.askyesno("Restaurar", f"Deseja restaurar as tolerâncias originais de fábrica para '{curr_name}'?"):
                delete_custom_profile(key)
                self._load_tolerances()
                self._update_model_preview(curr_name)
                win.destroy()
                msgbox.showinfo("Restaurado", "Tolerâncias restauradas para o padrão de fábrica.")

        ctk.CTkButton(bottom, text="💾 Salvar Calibração", height=38, font=F(12, True),
                      fg_color="#16a34a", hover_color="#15803d",
                      command=save_adjustments).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        ctk.CTkButton(bottom, text="↺ Padrão de Fábrica", height=38, font=F(12),
                      fg_color="#334155", hover_color="#475569",
                      command=restore_defaults).grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def _form_values(self):
        plate = self.f_plate.get().upper().strip()
        name = self.f_model.get()
        key = self.model_options.get(name, "GENERIC_OBD2")
        return plate, key, name, self.f_year.get().strip(), self.f_km.get().strip(), self.f_customer.get().strip()

    def _activate_vehicle(self, vehicle):
        self.active_vehicle = vehicle
        self.active_plate = vehicle["plate"]
        self.active_model_key = vehicle.get("model_key", "GENERIC_OBD2")
        self._load_tolerances()
        db = GarageProfileManager.load_database()
        db["selected_plate"] = self.active_plate
        GarageProfileManager.save_database(db)
        self._update_ui_for_active_vehicle()

    def _save_vehicle_from_form(self, silent=False):
        plate, key, name, year, km, cust = self._form_values()
        if not plate:
            msgbox.showwarning("Aviso", "Informe a placa do veículo.")
            return None
        v = GarageProfileManager.save_or_update_vehicle(plate, key, name, year, km, cust)
        self._activate_vehicle(v)
        self._populate_vehicle_cards()
        self._load_vehicle_into_form(v)
        if not silent:
            msgbox.showinfo("Salvo", f"Veículo {plate} salvo e ativado.")
        return v

    def _select_vehicle_by_plate(self, plate):
        v = GarageProfileManager.get_vehicle(plate)
        if not v:
            return
        self._activate_vehicle(v)
        self._load_vehicle_into_form(v)
        self._populate_vehicle_cards()

    def _apply_and_go_connect(self):
        if not self._save_vehicle_from_form(silent=True):
            return
        self._show_page("dashboard")
        if not self.is_connected:
            self._connect()

    def _delete_vehicle_from_form(self):
        plate = self.f_plate.get().upper().strip()
        if not plate or not GarageProfileManager.get_vehicle(plate):
            return
        if not msgbox.askyesno("Confirmar exclusão", f"Remover o veículo {plate} e todo o histórico dele?"):
            return
        GarageProfileManager.delete_vehicle(plate)
        remaining = GarageProfileManager.get_all_vehicles()
        if remaining:
            self._select_vehicle_by_plate(list(remaining.keys())[0])
        else:
            v = GarageProfileManager.save_or_update_vehicle(
                "SEM-PLACA", "GENERIC_OBD2", VEHICLE_PROFILES_DATABASE["GENERIC_OBD2"]["name"], "", "0", "")
            self._activate_vehicle(v)
            self._load_vehicle_into_form(v)
        self._populate_vehicle_cards()

    def _update_sidebar_vehicle(self):
        self.sb_plate.configure(text=self.active_plate)
        self.sb_model.configure(text=self.active_vehicle.get("model_name", ""))

    def _update_ui_for_active_vehicle(self):
        self._update_sidebar_vehicle()
        if hasattr(self, "lbl_dash_sub"):
            self.lbl_dash_sub.configure(text=f"{self.active_plate} • Calibração: {self.active_vehicle.get('model_name')}")
        if hasattr(self, "lbl_hist_title"):
            self.lbl_hist_title.configure(text=f"Histórico de diagnósticos — {self.active_plate}")
            self._refresh_history_view()
        self.minmax.clear()

    # ==========================================================
    # AVALIAÇÃO DE PARÂMETROS vs FÁBRICA
    # ==========================================================
    @staticmethod
    def _is_idle_hot(f):
        return f.get("speed", 0) < 3 and 550 < f.get("rpm", 0) < 1150 and f.get("coolant_temp", 0) >= 80

    def _param_range(self, key, f):
        """Retorna (min, max) aplicável ao contexto atual ou None se não houver referência."""
        tol = self.active_tolerances
        running = f.get("rpm", 0) > 500
        idle = self._is_idle_hot(f)

        def t(k, dmin, dmax):
            d = tol.get(k)
            return (d["min"], d["max"]) if d else (dmin, dmax)

        if key == "battery_voltage":
            return t("battery_voltage", 13.5, 14.8) if running else (12.2, 12.9)
        if key == "ecu_voltage":
            return (13.0, 14.8) if running else (11.8, 12.9)
        if key == "o2_b1s1":
            return t("lambda_o2", 0.1, 0.9) if running else None
        if key == "o2_b1s2":
            return (0.45, 0.90) if running and f.get("coolant_temp", 0) >= 80 else None
        if key == "tps":
            return t("idle_tps", 10, 19) if idle else None
        if key == "rpm":
            return t("idle_rpm", 700, 900) if idle else None
        if key == "engine_load":
            return (15, 40) if idle else None
        if key == "map_kpa":
            return t("idle_map", 27, 42) if idle else None
        if key == "maf_gs":
            return (1.5, 6.0) if idle else None
        if key == "timing_advance":
            return (4, 22) if idle else None
        if key == "coolant_temp":
            return t("coolant_temp", 82, 103) if running else None
        if key == "intake_temp":
            return (-10, 70)
        if key in ("stft_b1", "ltft_b1"):
            return (-10, 10) if running else None
        if key == "trim_total":
            return t("fuel_trim_total", -10, 10) if running else None
        return None

    def _evaluate(self, key, f):
        """(texto_status, cor, faixa)"""
        if key not in f:
            return "N/D", "gray45", None
        r = self._param_range(key, f)
        if r is None:
            return "—", "gray45", None
        v = f[key]
        lo, hi = r
        if v < lo:
            if key == "coolant_temp":
                return "AQUECENDO", AMBER, r
            return "BAIXO", RED, r
        if v > hi:
            return "ALTO", RED, r
        return "OK", GREEN, r

    @staticmethod
    def _fmt_value(key, f):
        if key not in f:
            return "N/D"
        try:
            return PARAM_BY_KEY[key][3].format(f[key])
        except (ValueError, TypeError):
            return str(f[key])

    # ==========================================================
    # PÁGINA 2: PAINEL (VISÃO GERAL)
    # ==========================================================
    def _build_dashboard_page(self, page):
        page.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="dash")
        page.grid_rowconfigure((1, 2), weight=1)

        _, _, self.lbl_dash_sub = self._page_header(
            page, "Painel de Instrumentos",
            f"{self.active_plate} • Calibração: {self.active_vehicle.get('model_name')}")

        cards = [
            ("rpm", "RPM DO MOTOR", "#38bdf8"),
            ("speed", "VELOCIDADE", "#4ade80"),
            ("battery_voltage", "⚡ BATERIA / ALTERNADOR", "#facc15"),
            ("coolant_temp", "TEMP. ARREFECIMENTO", "#f87171"),
            ("map_kpa", "PRESSÃO COLETOR (MAP)", "#a78bfa"),
            ("o2_b1s1", "SONDA LAMBDA B1S1", "#2dd4bf"),
            ("tps", "BORBOLETA (TPS)", "#fb923c"),
            ("trim_total", "TRIM TOTAL (STFT+LTFT)", "#f472b6"),
        ]
        self.dash_cards = {}
        for i, (key, title, color) in enumerate(cards):
            self.dash_cards[key] = self._create_gauge_card(page, 1 + i // 4, i % 4, key, title, color)

        # Faixa inferior
        strip = ctk.CTkFrame(page, fg_color=PANEL, corner_radius=10, border_width=1, border_color=BORDER)
        strip.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(8, 0))
        strip.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
        self.strip_labels = {}
        for i, key in enumerate(["stft_b1", "ltft_b1", "intake_temp", "engine_load", "timing_advance"]):
            box = ctk.CTkFrame(strip, fg_color="transparent")
            box.grid(row=0, column=i, pady=8)
            ctk.CTkLabel(box, text=PARAM_BY_KEY[key][1].split("(")[0].strip(), font=F(10), text_color=MUTED).pack()
            v = ctk.CTkLabel(box, text="--", font=F(15, True))
            v.pack()
            self.strip_labels[key] = v

        # Alertas
        self.lbl_alerts = ctk.CTkLabel(page, text="Conecte o veículo para iniciar a análise em tempo real.",
                                       font=F(12, True), text_color=MUTED, fg_color=PANEL, corner_radius=8,
                                       anchor="w", justify="left", height=34)
        self.lbl_alerts.grid(row=4, column=0, columnspan=4, sticky="ew", pady=(8, 0), ipadx=10)

    def _create_gauge_card(self, parent, row, col, key, title, color):
        card = ctk.CTkFrame(parent, fg_color=PANEL, corner_radius=12, border_width=1, border_color=BORDER)
        card.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 0))
        top.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(top, text=title, font=F(10, True), text_color=MUTED).grid(row=0, column=0, sticky="w")
        status = ctk.CTkLabel(top, text="—", font=F(9, True), corner_radius=6, fg_color="gray25", width=60, height=18)
        status.grid(row=0, column=1, sticky="e")

        valbox = ctk.CTkFrame(card, fg_color="transparent")
        valbox.grid(row=1, column=0)
        value = ctk.CTkLabel(valbox, text="--", font=F(34, True), text_color=color)
        value.grid(row=0, column=0)
        ctk.CTkLabel(valbox, text=" " + PARAM_BY_KEY[key][2], font=F(12, True), text_color="gray55").grid(row=0, column=1, sticky="s", pady=(0, 8))

        bar = ctk.CTkProgressBar(card, height=6, progress_color=color, fg_color="#1e293b")
        bar.grid(row=2, column=0, sticky="ew", padx=12)
        bar.set(0)
        rng = ctk.CTkLabel(card, text="Fábrica: --", font=F(10), text_color="gray55")
        rng.grid(row=3, column=0, sticky="w", padx=12, pady=(2, 8))

        return {"card": card, "value": value, "status": status, "bar": bar, "range": rng}

    def _update_dashboard(self, f):
        for key, w in self.dash_cards.items():
            status, color, r = self._evaluate(key, f)
            w["value"].configure(text=self._fmt_value(key, f))
            w["status"].configure(text=status, fg_color=color if status not in ("—", "N/D") else "gray25")
            w["card"].configure(border_color=color if status in ("ALTO", "BAIXO") else BORDER,
                                border_width=2 if status in ("ALTO", "BAIXO") else 1)
            lo_s, hi_s = PARAM_BY_KEY[key][5]
            if key in f:
                w["bar"].set(max(0.0, min(1.0, (f[key] - lo_s) / float(hi_s - lo_s))))
            w["range"].configure(text=f"Fábrica: {r[0]} – {r[1]}" if r else "Fábrica: sem referência neste regime")

        for key, lbl in self.strip_labels.items():
            unit = PARAM_BY_KEY[key][2]
            lbl.configure(text=f"{self._fmt_value(key, f)} {unit}" if key in f else "N/D")

        alerts = []
        for key in ("battery_voltage", "coolant_temp", "map_kpa", "trim_total", "rpm", "tps", "ecu_voltage", "o2_b1s2"):
            status, _, r = self._evaluate(key, f)
            if status in ("ALTO", "BAIXO"):
                p = PARAM_BY_KEY[key]
                alerts.append(f"{p[1]}: {self._fmt_value(key, f)} {p[2]} ({status.lower()}, fábrica {r[0]}–{r[1]})")
        if alerts:
            self.lbl_alerts.configure(text="⚠️  " + "   |   ".join(alerts[:3]), text_color="#fecaca", fg_color="#3f1d1d")
        else:
            self.lbl_alerts.configure(text="✅  Todos os parâmetros com referência estão dentro da faixa de fábrica.",
                                      text_color="#bbf7d0", fg_color="#12301f")

    # ==========================================================
    # PÁGINA 3: DADOS AO VIVO (LISTA COMPLETA)
    # ==========================================================
    def _build_live_page(self, page):
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(2, weight=1)

        hdr, _, _ = self._page_header(page, "Dados ao Vivo — Tensões, Sensores e Mistura",
                                      "Valor atual, mínimo/máximo da sessão e comparação com a faixa de fábrica do perfil ativo")
        btns = ctk.CTkFrame(page, fg_color="transparent")
        btns.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        ctk.CTkButton(btns, text="↺ Zerar mín/máx", width=130, height=30, fg_color="#334155", hover_color="#475569",
                      command=self._reset_minmax).pack(side="left")
        ctk.CTkButton(btns, text="💾 Exportar sessão (CSV)", width=180, height=30, fg_color="#2563eb", hover_color="#1d4ed8",
                      command=self._export_session_csv).pack(side="left", padx=6)
        self.lbl_live_rate = ctk.CTkLabel(btns, text="", font=F(11), text_color=MUTED)
        self.lbl_live_rate.pack(side="right")

        table = ctk.CTkScrollableFrame(page, fg_color=PANEL, corner_radius=10, border_width=1, border_color=BORDER)
        table.grid(row=2, column=0, sticky="nsew")
        widths = [330, 90, 50, 80, 80, 130, 100]
        for c, w in enumerate(widths):
            table.grid_columnconfigure(c, minsize=w, weight=1 if c == 0 else 0)

        headers = ["Parâmetro", "Valor", "Un.", "Mín", "Máx", "Faixa fábrica", "Status"]
        for c, h in enumerate(headers):
            ctk.CTkLabel(table, text=h, font=F(11, True), text_color=MUTED, anchor="w" if c == 0 else "center").grid(
                row=0, column=c, sticky="ew", padx=6, pady=(6, 4))

        self.live_rows = {}
        row = 1
        current_section = None
        for key, label, unit, fmt, section, _ in PARAMS:
            if section != current_section:
                current_section = section
                ctk.CTkLabel(table, text=section, font=F(11, True), text_color=AMBER, anchor="w").grid(
                    row=row, column=0, columnspan=7, sticky="ew", padx=6, pady=(10, 2))
                row += 1
            cells = {}
            ctk.CTkLabel(table, text=label, font=F(12), anchor="w").grid(row=row, column=0, sticky="ew", padx=6, pady=1)
            cells["value"] = ctk.CTkLabel(table, text="--", font=F(13, True, mono=True))
            cells["value"].grid(row=row, column=1, padx=6)
            ctk.CTkLabel(table, text=unit, font=F(11), text_color=MUTED).grid(row=row, column=2, padx=6)
            cells["min"] = ctk.CTkLabel(table, text="--", font=F(11, mono=True), text_color=MUTED)
            cells["min"].grid(row=row, column=3, padx=6)
            cells["max"] = ctk.CTkLabel(table, text="--", font=F(11, mono=True), text_color=MUTED)
            cells["max"].grid(row=row, column=4, padx=6)
            cells["range"] = ctk.CTkLabel(table, text="—", font=F(11), text_color=MUTED)
            cells["range"].grid(row=row, column=5, padx=6)
            cells["status"] = ctk.CTkLabel(table, text="—", font=F(10, True), corner_radius=6, fg_color="gray25", width=84, height=20)
            cells["status"].grid(row=row, column=6, padx=6, pady=1)
            self.live_rows[key] = cells
            row += 1

        ctk.CTkLabel(table, text="N/D = a ECU deste veículo não informa este PID   •   — = sem referência de fábrica no regime atual "
                                 "(ex.: MAP/TPS só são avaliados em marcha lenta com motor quente)",
                     font=F(10), text_color="gray50", anchor="w", wraplength=800, justify="left").grid(
            row=row, column=0, columnspan=7, sticky="ew", padx=6, pady=(12, 8))

    def _track_minmax(self, f):
        for key in PARAM_BY_KEY:
            if key in f:
                v = f[key]
                mm = self.minmax.get(key)
                if mm is None:
                    self.minmax[key] = [v, v]
                else:
                    mm[0] = min(mm[0], v)
                    mm[1] = max(mm[1], v)

    def _reset_minmax(self):
        self.minmax.clear()
        for cells in self.live_rows.values():
            cells["min"].configure(text="--")
            cells["max"].configure(text="--")

    def _update_live_table(self, f):
        for key, cells in self.live_rows.items():
            status, color, r = self._evaluate(key, f)
            cells["value"].configure(text=self._fmt_value(key, f), text_color=color if status in ("ALTO", "BAIXO") else "white")
            mm = self.minmax.get(key)
            if mm:
                fmt = PARAM_BY_KEY[key][3]
                cells["min"].configure(text=fmt.format(mm[0]))
                cells["max"].configure(text=fmt.format(mm[1]))
            cells["range"].configure(text=f"{r[0]} – {r[1]}" if r else "—")
            cells["status"].configure(text=status, fg_color=color if status not in ("—", "N/D") else "gray25")
        self.lbl_live_rate.configure(text=f"Amostras na sessão: {len(self.session_frames)}")

    def _export_session_csv(self):
        if not self.session_frames:
            msgbox.showinfo("Exportar", "Nenhum dado coletado ainda nesta sessão.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("Planilha CSV", "*.csv")],
            initialfile=f"autoscan_{self.active_plate}_{time.strftime('%Y%m%d_%H%M%S')}.csv")
        if not path:
            return
        keys = ["t"] + [p[0] for p in PARAMS]
        t0 = self.session_frames[0].get("t", 0)
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as fh:
                w = csv.writer(fh, delimiter=";")
                w.writerow(["tempo_s"] + [f"{PARAM_BY_KEY[k][1]} ({PARAM_BY_KEY[k][2]})" for k in keys[1:]])
                for fr in self.session_frames:
                    w.writerow([f"{fr.get('t', 0) - t0:.2f}"] +
                               [str(fr.get(k, "")).replace(".", ",") for k in keys[1:]])
            msgbox.showinfo("Exportar", f"Sessão exportada ({len(self.session_frames)} amostras):\n{path}")
        except Exception as e:
            msgbox.showerror("Erro", f"Não foi possível salvar o arquivo:\n{e}")

    # ==========================================================
    # PÁGINA 4: ASSISTENTE IA
    # ==========================================================
    def _build_ai_page(self, page):
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(2, weight=1)

        self._page_header(page, "Assistente IA — Elétrica & Injeção",
                          "A IA recebe automaticamente tensão, sensores, trims e falhas ativas do veículo conectado")

        # Seletor de Modelo Gratuito do Gemini
        chips = ctk.CTkFrame(page, fg_color="transparent")
        chips.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        chips.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(chips, text="Modelo IA:", font=F(11, True), text_color=MUTED).pack(side="left", padx=(0, 6))
        
        self.combo_ai_model = ctk.CTkComboBox(
            chips,
            values=list(ElectricalAIAssistant.FREE_MODELS.values()),
            width=360,
            height=28,
            font=F(11)
        )
        self.combo_ai_model.set(ElectricalAIAssistant.FREE_MODELS["gemini-3.1-flash-lite"])
        self.combo_ai_model.pack(side="left", padx=(0, 10))

        quick = [
            "Alternador carregando?",
            "Fuga de corrente na bateria?",
            "Ventoinha não liga?",
            "Engasga acelerando?",
        ]
        for q in quick:
            ctk.CTkButton(chips, text=q, height=26, font=F(11), fg_color="#1e293b", hover_color="#334155",
                          command=lambda qq=q: self._send_question_to_ai(qq)).pack(side="left", padx=(0, 4))

        self.txt_ai_chat = ctk.CTkTextbox(page, font=F(13, mono=True), corner_radius=10, fg_color=PANEL,
                                          border_width=1, border_color=BORDER, wrap="word")
        self.txt_ai_chat.grid(row=2, column=0, sticky="nsew")
        self.txt_ai_chat.insert("1.0", "🤖 Assistente pronto. Clique numa pergunta rápida acima ou digite o sintoma abaixo.\n")
        self.txt_ai_chat.configure(state="disabled")

        bottom = ctk.CTkFrame(page, fg_color="transparent")
        bottom.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        bottom.grid_columnconfigure(0, weight=1)
        self.entry_ai_question = ctk.CTkEntry(bottom, height=40, font=F(13),
                                              placeholder_text="Descreva o sintoma ou a dúvida elétrica...")
        self.entry_ai_question.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.entry_ai_question.bind("<Return>", lambda e: self._send_question_to_ai())
        
        self.btn_send_ai = ctk.CTkButton(bottom, text="🚀 Perguntar", width=130, height=40, font=F(13, True),
                                         fg_color="#8b5cf6", hover_color="#7c3aed", command=self._send_question_to_ai)
        self.btn_send_ai.grid(row=0, column=1, padx=(0, 6))

        self.btn_cancel_ai = ctk.CTkButton(bottom, text="✖ Cancelar", width=100, height=40, font=F(12),
                                           fg_color="#dc2626", hover_color="#b91c1c", state="disabled",
                                           command=self._cancel_ai_request)
        self.btn_cancel_ai.grid(row=0, column=2)

    def _chat_append(self, text):
        self.txt_ai_chat.configure(state="normal")
        self.txt_ai_chat.insert("end", text)
        self.txt_ai_chat.see("end")
        self.txt_ai_chat.configure(state="disabled")

    def _read_dtcs_safe(self):
        if self.client:
            try:
                with self.client_lock:
                    return self.client.read_dtcs()
            except Exception:
                return []
        if self.simulator:
            return [{"code": "P0171", "description": "Sistema Muito Pobre (Bancada 1)"}]
        return []

    def _cancel_ai_request(self):
        self.ai_request_cancelled = True
        self.btn_send_ai.configure(state="normal", text="🚀 Perguntar")
        self.btn_cancel_ai.configure(state="disabled")
        self._chat_append("\n[✖ Consulta cancelada pelo usuário]\n")

    def _send_question_to_ai(self, preset=None):
        question = (preset or self.entry_ai_question.get()).strip()
        if not question:
            return
        self.entry_ai_question.delete(0, "end")
        self.ai_request_cancelled = False
        self.btn_send_ai.configure(state="disabled", text="⏳ Analisando...")
        self.btn_cancel_ai.configure(state="normal")
        volt = self.latest_telemetry.get("battery_voltage", "--")
        self._chat_append(f"\n{'=' * 60}\n👤 VOCÊ: {question}\n⏳ Consultando IA ({self.active_vehicle.get('model_name')}, bateria {volt} V)...\n")

        chosen_label = self.combo_ai_model.get()
        chosen_id = next((k for k, v in ElectricalAIAssistant.FREE_MODELS.items() if v == chosen_label), "gemini-3.1-flash-lite")

        def worker():
            dtcs = self._read_dtcs_safe()
            reply = ElectricalAIAssistant.ask_ai_mechanic(
                question, dict(self.latest_telemetry), self.active_vehicle,
                dtcs=dtcs, gemini_key=self.gemini_api_key, preferred_model=chosen_id)

            def update():
                if not getattr(self, "ai_request_cancelled", False):
                    self._chat_append(f"\n🤖 PARECER TÉCNICO:\n\n{reply}\n")
                self.btn_send_ai.configure(state="normal", text="🚀 Perguntar")
                self.btn_cancel_ai.configure(state="disabled")
            self.after(0, update)

        threading.Thread(target=worker, daemon=True).start()

    # ==========================================================
    # PÁGINA 5: GRÁFICOS
    # ==========================================================
    def _build_charts_page(self, page):
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(2, weight=1)
        self._page_header(page, "Gráficos", "Ao vivo: últimos 60 segundos  •  Test-Drive: sessão gravada completa")

        bar = ctk.CTkFrame(page, fg_color="transparent")
        bar.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        self.seg_chart = ctk.CTkSegmentedButton(bar, values=["Ao vivo (60 s)", "Último Test-Drive"],
                                                command=self._on_chart_mode)
        self.seg_chart.set("Ao vivo (60 s)")
        self.seg_chart.pack(side="left")

        holder = ctk.CTkFrame(page, fg_color=PANEL, corner_radius=10, border_width=1, border_color=BORDER)
        holder.grid(row=2, column=0, sticky="nsew")
        holder.grid_columnconfigure(0, weight=1)
        holder.grid_rowconfigure(0, weight=1)

        self.fig = Figure(figsize=(9, 6), dpi=90, facecolor=PANEL)
        self.canvas = FigureCanvasTkAgg(self.fig, master=holder)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        self._draw_charts([], "Aguardando dados...")

    def _on_chart_mode(self, value):
        self.chart_mode_live = value.startswith("Ao vivo")
        self._redraw_charts_now()

    def _redraw_charts_now(self):
        if self.chart_mode_live:
            now = time.time()
            frames = [fr for fr in self.session_frames if now - fr.get("t", 0) <= 60]
            self._draw_charts(frames, "Ao vivo — últimos 60 s" if frames else "Aguardando dados ao vivo...")
        else:
            self._draw_charts(self.recorded_frames, "Último Test-Drive" if self.recorded_frames else "Nenhum test-drive gravado")

    def _live_chart_tick(self):
        try:
            if self.current_page == "charts" and self.chart_mode_live and self.is_connected:
                self._redraw_charts_now()
        finally:
            self.after(1000, self._live_chart_tick)

    def _draw_charts(self, frames, title):
        fig = self.fig
        fig.clf()
        axes = fig.subplots(3, 1, sharex=True)
        for ax in axes:
            ax.set_facecolor("#0f172a")
            ax.grid(True, color="#1f2937", linestyle="--")
            ax.tick_params(colors="#94a3b8", labelsize=8)
            for s in ax.spines.values():
                s.set_color("#1f2937")
        fig.suptitle(f"{title} — {self.active_plate}", color="#e2e8f0", fontsize=10)

        if frames:
            t0 = frames[0].get("t", 0)
            ts = [fr.get("t", t0 + i * 0.2) - t0 for i, fr in enumerate(frames)]

            def series(k):
                return [fr.get(k, float("nan")) for fr in frames]

            ax = axes[0]
            ax.plot(ts, series("rpm"), color="#38bdf8", lw=1.4)
            ax.set_ylabel("RPM", color="#38bdf8", fontsize=8)
            tw = ax.twinx()
            tw.plot(ts, series("speed"), color="#4ade80", lw=1.2)
            tw.set_ylabel("km/h", color="#4ade80", fontsize=8)
            tw.tick_params(colors="#94a3b8", labelsize=8)

            ax = axes[1]
            ax.plot(ts, series("coolant_temp"), color="#f87171", lw=1.4)
            ax.set_ylabel("Água °C", color="#f87171", fontsize=8)
            tw = ax.twinx()
            tw.plot(ts, series("trim_total"), color="#facc15", lw=1.1, ls=":")
            lim = self.active_tolerances.get("fuel_trim_total", {"max": 10})["max"]
            tw.axhline(lim, color=RED, ls="--", alpha=0.5)
            tw.axhline(-lim, color=RED, ls="--", alpha=0.5)
            tw.set_ylabel("Trim %", color="#facc15", fontsize=8)
            tw.tick_params(colors="#94a3b8", labelsize=8)

            ax = axes[2]
            ax.plot(ts, series("battery_voltage"), color="#facc15", lw=1.4)
            ax.axhspan(13.5, 14.8, color="#22c55e", alpha=0.08)
            ax.set_ylabel("Bateria V", color="#facc15", fontsize=8)
            tw = ax.twinx()
            tw.plot(ts, series("o2_b1s1"), color="#2dd4bf", lw=1.0)
            tw.set_ylim(0, 1.0)
            tw.set_ylabel("Sonda V", color="#2dd4bf", fontsize=8)
            tw.tick_params(colors="#94a3b8", labelsize=8)
            ax.set_xlabel("segundos", color="#94a3b8", fontsize=8)

        fig.tight_layout()
        self.canvas.draw_idle()

    # ==========================================================
    # PÁGINA 6: LAUDO
    # ==========================================================
    def _build_report_page(self, page):
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(3, weight=1)
        self._page_header(page, "Laudo do Test-Drive", "Inicie o Test-Drive na barra superior, rode com o carro e conclua para gerar o laudo")

        summary = ctk.CTkFrame(page, fg_color=PANEL, corner_radius=10, border_width=1, border_color=BORDER)
        summary.grid(row=1, column=0, sticky="ew")
        summary.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.lbl_rep_score = ctk.CTkLabel(summary, text="Saúde: --/100", font=F(16, True), text_color=ACCENT)
        self.lbl_rep_score.grid(row=0, column=0, pady=12)
        self.lbl_rep_fuel = ctk.CTkLabel(summary, text="Injeção: --", font=F(12, True))
        self.lbl_rep_fuel.grid(row=0, column=1)
        self.lbl_rep_coolant = ctk.CTkLabel(summary, text="Arrefecimento: --", font=F(12, True))
        self.lbl_rep_coolant.grid(row=0, column=2)
        self.lbl_rep_lambda = ctk.CTkLabel(summary, text="Sonda: --", font=F(12, True))
        self.lbl_rep_lambda.grid(row=0, column=3)

        acts = ctk.CTkFrame(page, fg_color="transparent")
        acts.grid(row=2, column=0, sticky="ew", pady=8)
        self.btn_run_ai = ctk.CTkButton(acts, text="✨ Gerar parecer com Gemini AI", height=34, font=F(12, True),
                                        fg_color="#8b5cf6", hover_color="#7c3aed", command=self._generate_ai_analysis)
        self.btn_run_ai.pack(side="left")
        ctk.CTkButton(acts, text="💾 Salvar no histórico do veículo", height=34, fg_color="#2563eb", hover_color="#1d4ed8",
                      command=self._save_current_analysis_to_garage).pack(side="left", padx=6)

        self.txt_report = ctk.CTkTextbox(page, font=F(13, mono=True), corner_radius=10, fg_color=PANEL,
                                         border_width=1, border_color=BORDER, wrap="word")
        self.txt_report.grid(row=3, column=0, sticky="nsew")
        self._set_readonly_text(self.txt_report, "Nenhum test-drive concluído ainda.\n")

    # ==========================================================
    # PÁGINA 7: HISTÓRICO
    # ==========================================================
    def _build_history_page(self, page):
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(1, weight=1)
        hdr, self.lbl_hist_title, _ = self._page_header(page, f"Histórico de diagnósticos — {self.active_plate}")
        ctk.CTkButton(hdr, text="🔄 Atualizar", width=110, height=28, fg_color="#334155", hover_color="#475569",
                      command=self._refresh_history_view).pack(anchor="e")
        self.txt_history = ctk.CTkTextbox(page, font=F(13, mono=True), corner_radius=10, fg_color=PANEL,
                                          border_width=1, border_color=BORDER, wrap="word")
        self.txt_history.grid(row=1, column=0, sticky="nsew")
        self._refresh_history_view()

    def _refresh_history_view(self):
        veh = GarageProfileManager.get_vehicle(self.active_plate)
        if not veh or not veh.get("history"):
            self._set_readonly_text(self.txt_history,
                                    f"Nenhum diagnóstico registrado para {self.active_plate}.\n"
                                    "Faça um Test-Drive e clique em 'Salvar no histórico do veículo'.\n")
            return
        txt = f"{veh['plate']} — {veh.get('model_name')}\n{'=' * 70}\n\n"
        for idx, e in enumerate(reversed(veh["history"]), 1):
            m = e.get("metrics", {})
            txt += f"[{idx}] {e['date']}  |  Saúde {e['score']}/100  |  {e['duration_sec']} s\n"
            txt += (f"    Vel. máx {m.get('max_speed', 0):.0f} km/h  •  Temp. máx {m.get('max_coolant', 0):.0f} °C  •  "
                    f"Trim {m.get('total_fuel_trim', 0):+.1f}%\n")
            for an in e.get("anomalies", []):
                txt += f"    ⚠️ {an['titulo']} ({an['sistema']})\n"
            if e.get("ai_report"):
                txt += f"\n    🤖 {e['ai_report'][:350]}...\n"
            txt += "-" * 70 + "\n\n"
        self._set_readonly_text(self.txt_history, txt)

    def _save_current_analysis_to_garage(self):
        if not self.last_analysis_result:
            msgbox.showinfo("Aviso", "Realize e conclua um Test-Drive primeiro.")
            return
        full = self.txt_report.get("1.0", "end")
        ai_txt = full.split("PARECER TÉCNICO GEMINI AI")[-1].strip() if "PARECER TÉCNICO GEMINI AI" in full else ""
        if GarageProfileManager.add_history_entry(self.active_plate, self.last_analysis_result, ai_report=ai_txt):
            msgbox.showinfo("Salvo", f"Diagnóstico salvo no histórico de {self.active_plate}.")
            self._refresh_history_view()
        else:
            msgbox.showerror("Erro", "Não foi possível salvar.")

    # ==========================================================
    # PÁGINA 8: MANUAL (SOMENTE LEITURA)
    # ==========================================================
    def _build_manual_page(self, page):
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(1, weight=1)
        self._page_header(page, "Manual de Tolerâncias & Guia de Diagnóstico", "Somente leitura • valores de referência por motor")
        tb = ctk.CTkTextbox(page, font=F(13, mono=True), corner_radius=10, fg_color=PANEL,
                            border_width=1, border_color=BORDER, wrap="word")
        tb.grid(row=1, column=0, sticky="nsew")

        txt = "TABELA DE TOLERÂNCIAS POR MOTOR\n" + "=" * 88 + "\n\n"
        for spec in VEHICLE_PROFILES_DATABASE.values():
            txt += f"■ {spec['name']}  ({spec.get('category', '')})\n"
            for t in spec["tolerances"].values():
                txt += f"    • {t['desc']:<58} {t['min']} a {t['max']} {t['unit']}\n"
            for tip in spec.get("tips", []):
                txt += f"    💡 {tip}\n"
            txt += "\n"
        txt += "\n" + DIAGNOSTIC_HELP_GUIDE
        self._set_readonly_text(tb, txt)

    # ==========================================================
    # TEST-DRIVE
    # ==========================================================
    def _toggle_test_drive(self):
        if not self.is_recording:
            self.is_recording = True
            self.recorded_frames = []
            self.record_start_time = time.time()
            self.btn_record.configure(text="⏹ Concluir", fg_color=RED, hover_color="#dc2626")
            self.lbl_record_status.configure(text="● Gravando", text_color=GREEN)
        else:
            self.is_recording = False
            self.btn_record.configure(text="▶ Test-Drive", fg_color="#16a34a", hover_color="#15803d")
            self.lbl_record_status.configure(text=f"{len(self.recorded_frames)} amostras", text_color=MUTED)
            self._process_test_drive_data()

    def _process_test_drive_data(self):
        if len(self.recorded_frames) < 5:
            msgbox.showinfo("Aviso", "Test-drive muito curto. Rode pelo menos 10 segundos.")
            return
        result = TestDriveDiagnosticAnalyzer.analyze_session(self.recorded_frames)
        self.last_analysis_result = result

        score = result["health_score"]
        color = GREEN if score >= 80 else AMBER if score >= 60 else RED
        self.lbl_rep_score.configure(text=f"Saúde: {score}/100", text_color=color)
        self.lbl_rep_fuel.configure(text=f"Injeção: {result['subsystems']['combustivel']}")
        self.lbl_rep_coolant.configure(text=f"Arrefecimento: {result['subsystems']['arrefecimento']}")
        self.lbl_rep_lambda.configure(text=f"Sonda: {result['subsystems']['sonda_lambda']}")

        m = result["metrics"]
        r = f"LAUDO DE TEST-DRIVE — {self.active_plate}\n"
        r += f"Modelo: {self.active_vehicle.get('model_name')}  |  KM: {self.active_vehicle.get('km')}\n" + "=" * 70 + "\n\n"
        r += f"• Duração: {result['duration_sec']} s ({result['samples_count']} amostras)\n"
        r += f"• Velocidade máx {m['max_speed']:.0f} km/h  |  média {m['avg_speed']:.0f} km/h\n"
        r += f"• RPM máx {m['max_rpm']:.0f}  |  médio {m['avg_rpm']:.0f}\n"
        r += f"• Temperatura água: mín {m['min_coolant']:.0f} °C  |  máx {m['max_coolant']:.0f} °C\n"
        r += f"• Trim total médio (STFT+LTFT): {m['total_fuel_trim']:+.1f}%  |  LTFT médio {m['avg_ltft']:+.1f}%\n"
        volts = [fr["battery_voltage"] for fr in self.recorded_frames if "battery_voltage" in fr]
        if volts:
            r += f"• Tensão bateria/alternador: mín {min(volts):.1f} V  |  máx {max(volts):.1f} V\n"
        r += "\n"
        if result["anomalies"]:
            r += "⚠️ ANOMALIAS IDENTIFICADAS\n" + "-" * 70 + "\n"
            for i, an in enumerate(result["anomalies"], 1):
                r += f"[{i}] {an['titulo']} ({an['sistema']} — {an['gravidade']})\n    {an['descricao']}\n\n"
        else:
            r += "✅ Nenhuma anomalia grave: o veículo operou dentro das faixas de fábrica.\n\n"
        r += "Clique em 'Gerar parecer com Gemini AI' para o parecer técnico detalhado.\n"
        self._set_readonly_text(self.txt_report, r)
        self._show_page("report")

    def _generate_ai_analysis(self):
        if not self.last_analysis_result:
            msgbox.showinfo("Aviso", "Execute e conclua um Test-Drive primeiro.")
            return
        self.btn_run_ai.configure(state="disabled", text="⏳ Consultando Gemini...")

        def worker():
            ai_text = TestDriveDiagnosticAnalyzer.generate_ai_report(self.last_analysis_result, api_key=self.gemini_api_key)

            def update():
                current = self.txt_report.get("1.0", "end")
                combined = current + "\n" + "=" * 70 + "\n                 PARECER TÉCNICO GEMINI AI\n" + "=" * 70 + "\n\n" + ai_text
                self._set_readonly_text(self.txt_report, combined)
                self.btn_run_ai.configure(state="normal", text="✨ Gerar parecer com Gemini AI")
            self.after(0, update)

        threading.Thread(target=worker, daemon=True).start()

    # ==========================================================
    # CHAVE GEMINI
    # ==========================================================
    def _open_ai_config_dialog(self):
        win = ctk.CTkToplevel(self)
        win.title("Configurar Chave do Google Gemini AI")
        win.geometry("540x250")
        win.resizable(False, False)
        win.transient(self)
        win.after(100, win.grab_set)

        ctk.CTkLabel(win, text="⚙️ Chave de API — Google Gemini", font=F(16, True)).pack(pady=(18, 4))
        ctk.CTkLabel(win, text="Cole a chave (Ctrl+V ou botão Colar). Gratuita em aistudio.google.com",
                     font=F(12), text_color=MUTED).pack(pady=(0, 12))

        row = ctk.CTkFrame(win, fg_color="transparent")
        row.pack(fill="x", padx=25)
        row.grid_columnconfigure(0, weight=1)
        entry = ctk.CTkEntry(row, placeholder_text="AIzaSy...", height=38)
        entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        if self.gemini_api_key:
            entry.insert(0, self.gemini_api_key)

        def paste(event=None):
            try:
                clip = win.clipboard_get()
                if clip:
                    entry.delete(0, "end")
                    entry.insert(0, clip.strip())
            except Exception:
                pass
            return "break"

        ctk.CTkButton(row, text="📋 Colar", width=80, height=38, fg_color="#334155", hover_color="#475569",
                      command=paste).grid(row=0, column=1)
        entry.bind("<Control-v>", paste)
        entry.bind("<Control-V>", paste)

        def save():
            self.gemini_api_key = entry.get().strip()
            self._save_config()
            win.destroy()
            msgbox.showinfo("Gemini", "Chave salva!" if self.gemini_api_key else "Chave removida.")

        ctk.CTkButton(win, text="💾 Salvar chave", height=38, font=F(13, True), fg_color="#16a34a",
                      hover_color="#15803d", command=save).pack(pady=18)

    # ==========================================================
    # DESCOBERTA DE ADAPTADORES & CONEXÃO
    # ==========================================================
    def _start_device_discovery(self, initial=False):
        if not initial:
            self.btn_scan.configure(state="disabled", text="⏳")
        threading.Thread(target=self._scan_devices_worker, daemon=True).start()

    def _scan_devices_worker(self):
        devices = {}
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            scanned = loop.run_until_complete(BleakScanner.discover(timeout=3.5))
            loop.close()
            for d in scanned:
                name = d.name or "Dispositivo Bluetooth"
                is_obd = "OBD" in name.upper() or "ELM" in name.upper() or d.address.upper() == DEFAULT_MAC
                label = f"{'⭐ [OBD]' if is_obd else '📶 [BT]'} {name} ({d.address})"
                devices[label] = {"type": "BT", "address": d.address, "name": name}
        except Exception:
            pass
        try:
            for p in serial.tools.list_ports.comports():
                devices[f"🔌 [COM] {p.device} - {p.description}"] = {"type": "COM", "address": p.device, "name": p.description}
        except Exception:
            pass
        if not any(v["address"] == DEFAULT_MAC for v in devices.values()):
            devices[f"⭐ [OBD] OBDII ({DEFAULT_MAC})"] = {"type": "BT", "address": DEFAULT_MAC, "name": "OBDII"}

        self.discovered_devices.update(devices)
        labels = sorted(self.discovered_devices.keys(), key=lambda k: (not k.startswith("⭐"), k))

        def update():
            curr = self.combo_devices.get()
            self.combo_devices.configure(values=labels)
            if curr in labels:
                self.combo_devices.set(curr)
            elif labels:
                self.combo_devices.set(labels[0])
            self.btn_scan.configure(state="normal", text="🔍")
        self.after(0, update)

    def _toggle_connection(self):
        if self.is_connected:
            self._disconnect()
        else:
            self._connect()

    def _set_connected_ui(self, status_text, color, protocol):
        self.is_connected = True
        self.is_running = True
        self.lbl_status.configure(text=status_text, text_color=color)
        self.lbl_protocol.configure(text=f"Protocolo: {protocol}")
        self.btn_read_dtc.configure(state="normal")
        self.btn_record.configure(state="normal")
        self.lbl_record_status.configure(text="Pronto", text_color=color)
        self.session_frames.clear()
        self.minmax.clear()

    def _cancel_connection(self):
        self.connection_aborted = True
        if self.connecting_client:
            try:
                self.connecting_client.close()
            except Exception:
                pass
            self.connecting_client = None
        self.btn_connect.configure(state="normal", text="⚡ Conectar", fg_color="#2563eb", hover_color="#1d4ed8")
        self.btn_cancel_connect.configure(state="disabled")
        self.btn_sim.configure(state="normal")
        self.lbl_status.configure(text="● Conexão abortada", text_color=MUTED)

    def _connect(self):
        dev = self.discovered_devices.get(self.combo_devices.get())
        if not dev:
            msgbox.showwarning("Aviso", "Selecione um adaptador válido na lista.")
            return
        self.connection_aborted = False
        self.btn_connect.configure(state="disabled", text="⏳ Conectando...")
        self.btn_cancel_connect.configure(state="normal")
        self.btn_sim.configure(state="disabled")
        self.lbl_status.configure(text="● Conectando ao OBD...", text_color=AMBER)

        def worker():
            mac = dev["address"] if dev["type"] == "BT" else None
            port = dev["address"] if dev["type"] == "COM" else None
            client = NativeELMClient(port=port, bt_mac=mac)
            self.connecting_client = client
            ok = client.connect()

            def done():
                self.connecting_client = None
                self.btn_cancel_connect.configure(state="disabled")
                if getattr(self, "connection_aborted", False):
                    client.close()
                    return
                if ok:
                    self.client = client
                    self._set_connected_ui("● Conectado (ECU online)", GREEN, client.protocol_name)
                    self.btn_connect.configure(state="normal", text="⏹ Desconectar", fg_color=RED, hover_color="#dc2626")
                    threading.Thread(target=self._telemetry_worker, daemon=True).start()
                else:
                    client.close()
                    self.btn_connect.configure(state="normal", text="⚡ Conectar", fg_color="#2563eb", hover_color="#1d4ed8")
                    self.btn_sim.configure(state="normal")
                    self.lbl_status.configure(text="● Falha na conexão", text_color=RED)
                    msgbox.showerror("Erro de conexão",
                                     "Não foi possível falar com o adaptador/ECU.\n\n"
                                     "• Ignição ligada?\n• Outro programa (ex.: OBD Auto Doctor) usando o adaptador?\n"
                                     "• Adaptador correto selecionado na lista?")
            self.after(0, done)

        threading.Thread(target=worker, daemon=True).start()

    def _toggle_simulator(self):
        if self.is_connected:
            self._disconnect()
            return
        self.simulator = ELM327Simulator()
        self._set_connected_ui("● Simulador ativo", "#14b8a6", "Virtual CAN 11/500")
        self.btn_sim.configure(text="⏹ Parar", fg_color=RED, hover_color="#dc2626")
        self.btn_connect.configure(state="disabled")
        threading.Thread(target=self._simulator_worker, daemon=True).start()

    def _disconnect(self):
        if self.is_recording:
            self._toggle_test_drive()
        self.is_running = False
        self.is_connected = False
        if self.client:
            with self.client_lock:
                self.client.close()
            self.client = None
        self.simulator = None
        self.latest_telemetry = {}

        self.lbl_status.configure(text="● Desconectado", text_color=RED)
        self.lbl_protocol.configure(text="Protocolo: --")
        self.btn_connect.configure(state="normal", text="⚡ Conectar", fg_color="#2563eb", hover_color="#1d4ed8")
        self.btn_sim.configure(state="normal", text="🎮 Simulador", fg_color="#0f766e", hover_color="#115e59")
        self.btn_read_dtc.configure(state="disabled")
        self.btn_record.configure(state="disabled")
        self.lbl_record_status.configure(text="")
        self.lbl_alerts.configure(text="Conecte o veículo para iniciar a análise em tempo real.", text_color=MUTED, fg_color=PANEL)

    # ==========================================================
    # TELEMETRIA
    # ==========================================================
    def _ingest_frame(self, raw):
        frame = {k: v for k, v in raw.items() if isinstance(v, (int, float)) and not isinstance(v, bool)}
        if "stft_b1" in frame and "ltft_b1" in frame:
            frame["trim_total"] = round(frame["stft_b1"] + frame["ltft_b1"], 1)
        frame["t"] = time.time()
        self.latest_telemetry = frame
        self.session_frames.append(frame)
        if self.is_recording:
            self.recorded_frames.append(frame)
        self.after(0, lambda f=frame: self._update_telemetry_ui(f))

    def _telemetry_worker(self):
        while self.is_running and self.client:
            try:
                with self.client_lock:
                    if not self.client:
                        break
                    raw = self.client.read_current_telemetry()
                if raw:
                    self._ingest_frame(raw)
                time.sleep(0.05)
            except Exception:
                break

    def _simulator_worker(self):
        while self.is_running and self.simulator:
            try:
                self.simulator.update_dynamic_state()
                self._ingest_frame(dict(self.simulator.state))
                time.sleep(0.2)
            except Exception:
                break

    def _update_telemetry_ui(self, f):
        if not self.is_connected:
            return
        self._track_minmax(f)
        if self.current_page == "dashboard":
            self._update_dashboard(f)
        elif self.current_page == "live":
            self._update_live_table(f)
        if self.is_recording:
            elapsed = int(time.time() - self.record_start_time)
            self.lbl_record_status.configure(text=f"● {elapsed}s • {len(self.recorded_frames)} pts")

    def _read_dtcs_dialog(self):
        dtcs = self._read_dtcs_safe()
        if not dtcs:
            msgbox.showinfo("Códigos de falha", "Nenhum código de falha armazenado na ECU.")
            return
        text = "\n".join(f"• {d['code']}: {d.get('description', 'Código OBD')}" for d in dtcs)
        msgbox.showwarning("Códigos de falha", f"Falhas armazenadas:\n\n{text}\n\nDica: pergunte ao Assistente IA como testar cada uma.")


if __name__ == "__main__":
    app = AutoScanWindowsApp()
    app.mainloop()
