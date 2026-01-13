import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, timedelta
import base64
import io
from PIL import Image

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Vero RH - Gestão de Diárias", layout="wide", page_icon="🔴")

# --- BANCO DE DADOS SQLITE ---
def get_db_connection():
    conn = sqlite3.connect('verorh_data.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Tabela de Empresas
    conn.execute('''CREATE TABLE IF NOT EXISTS empresas 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE)''')
    # Tabela de Prestadores
    conn.execute('''CREATE TABLE IF NOT EXISTS prestadores 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, documento TEXT UNIQUE, empresa_id INTEGER,
                    FOREIGN KEY (empresa_id) REFERENCES empresas (id))''')
    # Tabela de Diárias
    conn.execute('''CREATE TABLE IF NOT EXISTS diarias 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, prestador_id INTEGER, data TEXT, valor REAL, foto_url TEXT,
                    FOREIGN KEY (prestador_id) REFERENCES prestadores (id))''')
    conn.commit()
    conn.close()

init_db()

# --- DESIGN VERO RH (CSS Customizado) ---
st.markdown("""
    <style>
        .stApp { background-color: #0e1117; color: #ffffff; }
        [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
        .logo-vero { color: #E60000; font-weight: 900; font-size: 50px; letter-spacing: -2px; }
        .logo-rh { color: #ffffff; font-weight: 200; font-size: 50px; }
        div.stButton > button {
            background: linear-gradient(90deg, #E60000 0%, #990000 100%);
            color: white; border: none; padding: 10px 24px; border-radius: 8px; font-weight: bold; width: 100%;
        }
        .card {
            background-color: #1d2127; padding: 20px; border-radius: 15px;
            border: 1px solid #30363d; margin-bottom: 20px;
        }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR / LOGIN ---
with st.sidebar:
    st.markdown('<div style="margin-bottom: 20px;"><span class="logo-vero">vero</span><span class="logo-rh">RH</span></div>', unsafe_allow_html=True)
    st.divider()
    perfil = st.selectbox("Selecione seu Acesso", ["Vero Master", "RH Parceiro", "Financeiro"])
    senha = st.text_input("Senha de Acesso", type="password")
    acesso_liberado = (senha == "vero123")

# --- CONTEÚDO PRINCIPAL ---
if not acesso_liberado:
    st.warning("Por favor, insira a senha na barra lateral para acessar o sistema.")
else:
    # --- 1. VERO MASTER (Gestão de Empresas) ---
    if perfil == "Vero Master":
        st.title("🏗️ Gestão de Empresas Parceiras")
        
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            nome_empresa = st.text_input("Nome da Nova Empresa Cliente")
            if st.button("Cadastrar Empresa"):
                if nome_empresa:
                    conn = get_db_connection()
                    try:
                        conn.execute("INSERT INTO empresas (nome) VALUES (?)", (nome_empresa,))
                        conn.commit()
                        st.success(f"Empresa '{nome_empresa}' cadastrada!")
                    except:
                        st.error("Erro: Esta empresa já existe ou houve um problema no banco.")
                    finally:
                        conn.close()
            st.markdown('</div>', unsafe_allow_html=True)

        st.subheader("Empresas Ativas")
        df_e = pd.read_sql("SELECT * FROM empresas", get_db_connection())
        st.dataframe(df_e, use_container_width=True, hide_index=True)

    # --- 2. RH PARCEIRO (Cadastrar Funcionario e Diaria) ---
    elif perfil == "RH Parceiro":
        st.title("📋 Painel de Lançamentos")
        
        conn = get_db_connection()
        empresas = pd.read_sql("SELECT * FROM empresas", conn)
        
        if empresas.empty:
            st.error("Nenhuma empresa cadastrada pelo Master.")
        else:
            emp_opcoes = {row['nome']: row['id'] for _, row in empresas.iterrows()}
            emp_sel_nome = st.selectbox("Sua Empresa", list(emp_opcoes.keys()))
            emp_id = emp_opcoes[emp_sel_nome]

            tab1, tab2 = st.tabs(["👥 Funcionários", "📅 Lançar Diárias"])

            with tab1:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                with st.form("form_func"):
                    nome_f = st.text_input("Nome Completo do Colaborador")
                    doc_f = st.text_input("CPF / Documento")
                    if st.form_submit_button("Cadastrar Colaborador"):
                        try:
                            conn.execute("INSERT INTO prestadores (nome, documento, empresa_id) VALUES (?,?,?)", 
                                         (nome_f, doc_f, emp_id))
                            conn.commit()
                            st.success("Colaborador cadastrado!")
                        except: st.error("Erro ao cadastrar.")
                st.markdown('</div>', unsafe_allow_html=True)

            with tab2:
                prestadores = pd.read_sql(f"SELECT * FROM prestadores WHERE empresa_id = {emp_id}", conn)
                if prestadores.empty:
                    st.info("Cadastre um funcionário primeiro.")
                else:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    p_opcoes = {row['nome']: row['id'] for _, row in prestadores.iterrows()}
                    p_sel = st.selectbox("Selecione o Funcionário", list(p_opcoes.keys()))
                    data_diaria = st.date_input("Data da Folha de Ponto", date.today())
                    foto = st.file_uploader("Upload da Foto da Folha", type=['jpg', 'jpeg', 'png'])
                    
                    if st.button("Salvar Diária"):
                        if foto:
                            img_b64 = base64.b64encode(foto.read()).decode()
                            conn.execute("INSERT INTO diarias (prestador_id, data, valor, foto_url) VALUES (?,?,?,?)",
                                         (p_opcoes[p_sel], str(data_diaria), 150.0, img_b64))
                            conn.commit()
                            st.success("Diária e comprovante salvos com sucesso!")
                        else:
                            st.error("A foto do comprovante é obrigatória.")
                    st.markdown('</div>', unsafe_allow_html=True)
        conn.close()

    # --- 3. FINANCEIRO (Auditoria e Visualização) ---
    elif perfil == "Financeiro":
        st.title("💰 Auditoria e Pagamentos")
        
        query = """
            SELECT d.id, e.nome as Empresa, p.nome as Colaborador, d.data, d.valor, d.foto_url
            FROM diarias d
            JOIN prestadores p ON d.prestador_id = p.id
            JOIN empresas e ON p.empresa_id = e.id
        """
        df_fin = pd.read_sql(query, get_db_connection())
        
        if df_fin.empty:
            st.info("Nenhum dado lançado no sistema ainda.")
        else:
            st.dataframe(df_fin[['id', 'Empresa', 'Colaborador', 'data', 'valor']], use_container_width=True)
            
            st.divider()
            st.subheader("Visualizar Comprovante")
            id_busca = st.number_input("Digite o ID da diária para ver a foto", min_value=1, step=1)
            
            if st.button("Visualizar Foto"):
                try:
                    foto_b64 = df_fin[df_fin['id'] == id_busca]['foto_url'].values[0]
                    st.image(io.BytesIO(base64.b64decode(foto_b64)), caption=f"ID: {id_busca}")
                except:
                    st.error("ID não encontrado ou sem imagem.")
