"""
================================================================================
DEVICE CENTER - GESTÃO DE ESTOQUE, PDV & DASHBOARD EXECUTIVO
================================================================================
Tema: Ultra-futurista Executivo com Azul Cyan / Elétrico (#00f3ff) Flat & Clean
Tipografia: Orbitron (Títulos & Métricas) + Inter (Corpo & Tabelas)
Categorias Oficiais: Placa de Vídeo, Processador, Memória RAM, SSD, Teclado,
                     Mouse, Cooler, Fonte, Placa Mãe, Console, Monitor,
                     Periféricos, Controle.
Banco de Dados: SQLite Local (device_center.db)
================================================================================
"""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
import os

# 1. Configuração da Página
st.set_page_config(
    page_title="Device Center - Gestão",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Categorias Oficiais
CATEGORIAS = [
    "Placa de Vídeo", "Processador", "Memória RAM", "SSD", "Teclado",
    "Mouse", "Cooler", "Fonte", "Placa Mãe", "Console", "Monitor",
    "Periféricos", "Controle"
]

MESES_NOMES = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

# 3. Banco de Dados Local SQLite (device_center.db)
DB_FILE = "device_center.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            sku TEXT UNIQUE,
            categoria TEXT NOT NULL,
            custo REAL NOT NULL,
            preco_venda REAL NOT NULL,
            estoque INTEGER NOT NULL,
            estoque_minimo INTEGER DEFAULT 3,
            unidade TEXT DEFAULT 'UN',
            descricao TEXT,
            data_cadastro TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_venda TEXT UNIQUE,
            data_hora TEXT NOT NULL,
            ano INTEGER NOT NULL,
            mes INTEGER NOT NULL,
            cliente TEXT DEFAULT 'Consumidor Final',
            forma_pagamento TEXT NOT NULL,
            subtotal REAL NOT NULL,
            desconto REAL DEFAULT 0,
            total REAL NOT NULL,
            custo_total REAL NOT NULL,
            lucro_liquido REAL NOT NULL,
            status TEXT DEFAULT 'CONCLUIDA',
            motivo_estorno TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS itens_venda (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venda_id INTEGER NOT NULL,
            produto_id INTEGER NOT NULL,
            nome_produto TEXT NOT NULL,
            categoria TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            custo_unitario REAL NOT NULL,
            preco_unitario REAL NOT NULL,
            total_item REAL NOT NULL,
            lucro_item REAL NOT NULL,
            FOREIGN KEY (venda_id) REFERENCES vendas (id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

# 4. Sidebar & Toggle de Tema Claro / Escuro (Flat, sem glow)
st.sidebar.markdown("<h3 style='margin-bottom:0px; font-family: Orbitron;'>DEVICE CENTER</h3>", unsafe_allow_html=True)
tema_claro = st.sidebar.toggle("Modo Claro / Escuro", value=False)

if tema_claro:
    CSS_TEMA = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Orbitron:wght@600;700;800;900&display=swap');
        #MainMenu, footer, header, .stDeployButton {visibility: hidden; display:none;}
        .stApp { background-color: #f8f9fa !important; color: #1a1a1a !important; font-family: 'Inter', sans-serif !important; }
        section[data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #e2e8f0 !important; }
        h1, h2, h3, h4, .orbitron-font { font-family: 'Orbitron', sans-serif !important; color: #0f172a !important; }
        .dc-card { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; margin-bottom: 12px; }
        .stButton > button { background-color: #00f3ff !important; color: #000000 !important; font-weight: 800 !important; font-family: 'Orbitron', sans-serif !important; border: none !important; border-radius: 8px !important; }
    </style>
    """
    PLOTLY_TEMPLATE = "plotly_white"
else:
    CSS_TEMA = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Orbitron:wght@600;700;800;900&display=swap');
        #MainMenu, footer, header, .stDeployButton {visibility: hidden; display:none;}
        .stApp { background-color: #07090e !important; color: #f1f5f9 !important; font-family: 'Inter', sans-serif !important; }
        section[data-testid="stSidebar"] { background-color: #0a0f1a !important; border-right: 1px solid #1e293b !important; }
        h1, h2, h3, h4, .orbitron-font { font-family: 'Orbitron', sans-serif !important; color: #ffffff !important; }
        .dc-card { background-color: #0e1626; border: 1px solid #1e293b; border-radius: 12px; padding: 18px; margin-bottom: 12px; }
        .stButton > button { background-color: #00f3ff !important; color: #000000 !important; font-weight: 800 !important; font-family: 'Orbitron', sans-serif !important; border: none !important; border-radius: 8px !important; }
    </style>
    """
    PLOTLY_TEMPLATE = "plotly_dark"

st.markdown(CSS_TEMA, unsafe_allow_html=True)

if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)

# 5. Navegação
modulo = st.sidebar.radio(
    "Módulos do Sistema",
    ["📊 BI & Painel Executivo", "⚡ Ponto de Venda (PDV)", "📦 Gestão de Estoque", "📜 Histórico & Estornos", "💰 Financeiro & DRE"]
)

st.markdown("---")

# ==========================================
# LÓGICA DAS PÁGINAS (Estrutura Adicionada)
# ==========================================

if modulo == "📊 BI & Painel Executivo":
    st.title("Painel Executivo (Dashboard)")
    st.info("Aqui entrarão os gráficos e os lucros mensais.")

elif modulo == "⚡ Ponto de Venda (PDV)":
    st.title("Ponto de Venda (PDV)")
    st.info("Aqui entrará a tela de vendas.")

elif modulo == "📦 Gestão de Estoque":
    st.title("Gestão de Estoque")
    st.info("Aqui entrarão as abas de Cadastrar, Editar e Consultar produtos.")

elif modulo == "📜 Histórico & Estornos":
    st.title("Histórico de Vendas")
    st.info("Aqui você poderá ver as vendas passadas e cancelar/estornar.")

elif modulo == "💰 Financeiro & DRE":
    st.title("Módulo Financeiro")
    st.info("Aqui você verá relatórios mais profundos de fluxo de caixa.")
