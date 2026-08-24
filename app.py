import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÕES E ESTILO EXECUTIVO (INSPIRADO NA IMAGEM)
# ==========================================
st.set_page_config(page_title="Gestão sem Achismo", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    /* Fundo geral super escuro e texto claro */
    .stApp {
        background-color: #050505;
        color: #e0e6ed;
    }
    
    /* Cor de destaque principal: Vermelho */
    div[data-testid="stMetricValue"] {
        color: #ff3333 !important;
        font-weight: 800 !important;
    }
    
    /* Botões com estilo minimalista e borda vermelha */
    .stButton>button {
        background-color: transparent !important;
        border: 1px solid #333333 !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        background-color: #ff3333 !important;
        border: 1px solid #ff3333 !important;
        color: #ffffff !important;
    }

    /* Menu Lateral */
    div[role="radiogroup"] label {
        transition: all 0.2s ease !important;
        padding: 8px !important;
        border-radius: 6px !important;
    }
    div[role="radiogroup"] label:hover {
        background-color: #1a1a1a !important;
        color: #ff3333 !important;
    }

    /* Títulos */
    h1, h2, h3 {
        color: #ffffff !important;
        font-family: 'Arial', sans-serif;
    }
    
    /* Cards de fundo (Métricas) */
    div[data-testid="metric-container"] {
        background-color: #121212;
        border: 1px solid #2a2a2a;
        padding: 15px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. BANCO DE DADOS
# ==========================================
conn = sqlite3.connect('meu_negocio.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS produtos 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, custo REAL, preco_venda REAL, estoque INTEGER, imagem BLOB)''')
c.execute('''CREATE TABLE IF NOT EXISTS vendas 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, produto_id INTEGER, data TEXT, quantidade INTEGER, valor_total REAL, lucro REAL)''')
conn.commit()

# ==========================================
# 3. INTERFACE E NAVEGAÇÃO
# ==========================================
st.sidebar.markdown("## 🔴 LAB Gestão")
menu = st.sidebar.radio("Navegação:", ["📊 Dashboard Executivo", "📦 Gestão de Estoque", "🛒 PDV (Vendas)"])

# ==========================================
# 4. DASHBOARD
# ==========================================
if menu == "📊 Dashboard Executivo":
    st.title("Visão Executiva")
    st.markdown("Dados conectados. Decisões mais claras.")
    st.markdown("---")
    
    df_vendas = pd.read_sql_query("SELECT v.id, p.nome as 'Produto', v.data as 'Data', v.quantidade as 'Qtd', v.valor_total as 'Total', v.lucro as 'Lucro', v.produto_id FROM vendas v JOIN produtos p ON v.produto_id = p.id", conn)
    
    if not df_vendas.empty:
        df_vendas['Data'] = pd.to_datetime(df_vendas['Data'])
        vendas_mes = df_vendas[df_vendas['Data'].dt.month == datetime.now().month]
        
        col1, col2 = st.columns(2)
        col1.metric("Receita do Mês", f"R$ {vendas_mes['Total'].sum():.2f}")
        col2.metric("Lucro do Mês", f"R$ {vendas_mes['Lucro'].sum():.2f}")
        
        st.subheader("Últimas Movimentações")
        st.dataframe(df_vendas[['id', 'Data', 'Produto', 'Qtd', 'Total', 'Lucro']].sort_values(by='Data', ascending=False), hide_index=True, use_container_width=True)
        
        with st.expander("⚠️ Estornar Venda"):
            venda_id_cancelar = st.selectbox("ID da venda para cancelar:", df_vendas['id'].tolist())
            if st.button("Confirmar Estorno"):
                venda_info = df_vendas[df_vendas['id'] == venda_id_cancelar].iloc[0]
                c.execute("UPDATE produtos SET estoque = estoque + ? WHERE id = ?", (int(venda_info['Qtd']), int(venda_info['produto_id'])))
                c.execute("DELETE FROM vendas WHERE id = ?", (venda_id_cancelar,))
                conn.commit()
                st.success("Venda estornada!")
                st.rerun()
    else:
        st.info("Aguardando os primeiros registros de vendas.")

# ==========================================
# 5. GERENCIAR ESTOQUE (INCLUI EXCLUIR)
# ==========================================
elif menu == "📦 Gestão de Estoque":
    st.title("Operação de Estoque")
    
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Cadastrar", "🔍 Consultar", "✏️ Editar", "🗑️ Excluir"])
    df_produtos = pd.read_sql_query("SELECT id, nome, custo, preco_venda, estoque FROM produtos", conn)
    
    # Aba 1: Cadastrar
    with tab1:
        with st.form("form_produto"):
            nome = st.text_input("Nome do Produto")
            c1, c2, c3 = st.columns(3)
            custo = c1.number_input("Custo (R$)", min_value=0.0, format="%.2f")
            preco_venda = c2.number_input("Preço de Venda (R$)", min_value=0.0, format="%.2f")
            estoque = c3.number_input("Estoque Inicial", min_value=0, step=1)
            imagem_up = st.file_uploader("Foto (Opcional)", type=['png', 'jpg', 'jpeg'])
            if st.form_submit_button("Salvar") and nome:
                img_bytes = imagem_up.read() if imagem_up else None
                c.execute("INSERT INTO produtos (nome, custo, preco_venda, estoque, imagem) VALUES (?, ?, ?, ?, ?)", (nome, custo, preco_venda, estoque, img_bytes))
                conn.commit()
                st.success(f"'{nome}' cadastrado!")
                st.rerun()
                
    # Aba 2: Consultar
    with tab2:
        st.dataframe(df_produtos, hide_index=True, use_container_width=True)
        
    # Aba 3: Editar
    with tab3:
        if not df_produtos.empty:
            opcoes_editar = df_produtos.set_index('id')['nome'].to_dict()
            prod_edit_id = st.selectbox("Produto para editar:", options=list(opcoes_editar.keys()), format_func=lambda x: opcoes_editar[x])
            dados_atuais = df_produtos[df_produtos['id'] == prod_edit_id].iloc[0]
            
            with st.form("form_editar"):
                novo_nome = st.text_input("Nome", value=dados_atuais['nome'])
                ca, cb, cc = st.columns(3)
                novo_custo = ca.number_input("Custo (R$)", value=float(dados_atuais['custo']), format="%.2f")
                novo_preco = cb.number_input("Preço (R$)", value=float(dados_atuais['preco_venda']), format="%.2f")
                novo_estoque = cc.number_input("Estoque", value=int(dados_atuais['estoque']), step=1)
                
                if st.form_submit_button("Atualizar"):
                    c.execute("UPDATE produtos SET nome=?, custo=?, preco_venda=?, estoque=? WHERE id=?", (novo_nome, novo_custo, novo_preco, novo_estoque, prod_edit_id))
                    conn.commit()
                    st.success("Atualizado!")
                    st.rerun()
                    
    # Aba 4: EXCLUIR PRODUTO (NOVIDADE)
    with tab4:
        if not df_produtos.empty:
            st.warning("Atenção: A exclusão de um produto é permanente.")
            opcoes_excluir = df_produtos.set_index('id')['nome'].to_dict()
            prod_excluir_id = st.selectbox("Selecione o produto para EXCLUIR:", options=list(opcoes_excluir.keys()), format_func=lambda x: opcoes_excluir[x])
            
            if st.button("🗑️ Excluir Permanentemente"):
                c.execute("DELETE FROM produtos WHERE id=?", (prod_excluir_id,))
                conn.commit()
                st.success("Produto excluído com sucesso!")
                st.rerun()

# ==========================================
# 6. PONTO DE VENDA
# ==========================================
elif menu == "🛒 PDV (Vendas)":
    st.title("Lançamento de Vendas")
    df_pdv = pd.read_sql_query("SELECT * FROM produtos WHERE estoque > 0", conn)
    
    if df_pdv.empty:
        st.warning("Estoque vazio.")
    else:
        opcoes_venda = df_pdv.set_index('id')['nome'].to_dict()
        col1, col2 = st.columns([1, 2])
        
        with col2:
            produto_selecionado = st.selectbox("Produto", options=list(opcoes_venda.keys()), format_func=lambda x: opcoes_venda[x])
            produto_info = df_pdv[df_pdv['id'] == produto_selecionado].iloc[0]
            quantidade = st.number_input("Quantidade", min_value=1, max_value=int(produto_info['estoque']), step=1)
            valor_final = quantidade * produto_info['preco_venda']
            
            st.markdown(f"<h3 style='color:#ff3333;'>Total: R$ {valor_final:.2f}</h3>", unsafe_allow_html=True)
            
            if st.button("Finalizar Venda"):
                lucro = valor_final - (quantidade * produto_info['custo'])
                data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("INSERT INTO vendas (produto_id, data, quantidade, valor_total, lucro) VALUES (?, ?, ?, ?, ?)", (produto_selecionado, data_atual, quantidade, valor_final, lucro))
                c.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (quantidade, produto_selecionado))
                conn.commit()
                st.success("Venda registrada!")
                
        with col1:
            img_pdv = produto_info.get('imagem')
            if pd.notna(img_pdv) and img_pdv is not None:
                st.image(img_pdv, use_container_width=True)