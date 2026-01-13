import streamlit as st
import pandas as pd
import pyodbc
from datetime import date, timedelta
import io
import base64
from PIL import Image

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Vero RH - SQL Server Edition", layout="wide", page_icon="🔴")

# --- DESIGN VERO RH (CSS) ---
st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%); color: #ffffff; }
        .stButton>button { 
            background: linear-gradient(90deg, #E60000 0%, #990000 100%) !important; 
            color: white !important; border-radius: 25px !important; border: none !important; 
        }
        .logo-vero { color: #E60000; font-weight: 900; font-size: 60px; letter-spacing: -3px; }
        .logo-rh { color: #ffffff; font-weight: 200; font-size: 60px; }
        .login-card { 
            background: rgba(255, 255, 255, 0.05); padding: 40px; border-radius: 20px; 
            border: 1px solid rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px); 
            max-width: 500px; margin: auto; 
        }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO COM SQL SERVER ---
def get_connection():
    # As credenciais devem estar no Secrets do Streamlit Cloud
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={st.secrets['sql_server']};"
        f"DATABASE={st.secrets['sql_database']};"
        f"UID={st.secrets['sql_user']};"
        f"PWD={st.secrets['sql_password']}"
    )
    return pyodbc.connect(conn_str)

# --- FUNÇÕES DE BANCO DE DADOS ---
def executar_query(query, params=(), commit=False):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        if commit:
            conn.commit()
            return True
        return cursor.fetchall()
    except Exception as e:
        st.error(f"Erro no banco: {e}")
        return None
    finally:
        conn.close()

# --- LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown('<div style="text-align:center; padding-top: 50px;"><span class="logo-vero">vero</span><span class="logo-rh">RH</span></div>', unsafe_allow_html=True)
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        perfil = st.selectbox("Perfil", ["Vero Master", "RH Empresa Vinculada", "Financeiro", "Colaborador"])
        
        empresa_id = None
        empresa_nome = None
        
        if perfil == "RH Empresa Vinculada":
            empresas = executar_query("SELECT id, nome FROM empresas")
            if empresas:
                lista_e = {e[1]: e[0] for e in empresas}
                empresa_nome = st.selectbox("Selecione sua Empresa", list(lista_e.keys()))
                empresa_id = lista_e[empresa_nome]

        senha = st.text_input("Senha", type="password")
        if st.button("ENTRAR", use_container_width=True):
            if senha == "vero123":
                st.session_state.update({"autenticado": True, "perfil": perfil, "emp_id": empresa_id, "emp_nome": empresa_nome})
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.sidebar.button("🔴 Sair", on_click=lambda: st.session_state.update({"autenticado": False}))

    # --- VERO MASTER: GESTÃO DE EMPRESAS ---
    if st.session_state.perfil == "Vero Master":
        st.title("🏗️ Master - Gestão de Empresas")
        with st.form("add_empresa"):
            nome_e = st.text_input("Nome da Empresa Cliente")
            if st.form_submit_button("Cadastrar Empresa"):
                executar_query("INSERT INTO empresas (nome) VALUES (?)", (nome_e,), commit=True)
                st.success("Empresa cadastrada!")

    # --- RH VINCULADO: GESTÃO DE FUNCIONÁRIOS E DIÁRIAS ---
    elif st.session_state.perfil == "RH Empresa Vinculada":
        st.title(f"📋 Painel RH - {st.session_state.emp_nome}")
        tab1, tab2 = st.tabs(["Funcionários", "Lançar Período"])
        
        with tab1:
            with st.form("cad_func"):
                n_f = st.text_input("Nome do Funcionário")
                c_f = st.text_input("CPF")
                if st.form_submit_button("Salvar Funcionário"):
                    executar_query("INSERT INTO prestadores (nome, documento, empresa_id) VALUES (?,?,?)", 
                                   (n_f, c_f, st.session_state.emp_id), commit=True)
                    st.success("Cadastrado!")

        with tab2:
            funcs = executar_query("SELECT id, nome FROM prestadores WHERE empresa_id = ?", (st.session_state.emp_id,))
            if funcs:
                dict_f = {f[1]: f[0] for f in funcs}
                f_sel = st.selectbox("Funcionário", list(dict_f.keys()))
                d_i = st.date_input("Início")
                d_f = st.date_input("Fim")
                foto = st.file_uploader("Foto da Folha", type=['jpg','png','jpeg'])
                
                if st.button("LANÇAR NO SQL SERVER"):
                    if foto:
                        img_b64 = base64.b64encode(foto.read()).decode()
                        curr = d_i
                        while curr <= d_f:
                            executar_query("INSERT INTO diarias (prestador_id, data_servico, valor, foto_url) VALUES (?,?,?,?)",
                                           (dict_f[f_sel], curr, 150.0, img_b64), commit=True)
                            curr += timedelta(days=1)
                        st.success("Período gravado com sucesso!")

    # --- FINANCEIRO: AUDITORIA ---
    elif st.session_state.perfil == "Financeiro":
        st.title("💰 Auditoria Financeira")
        dados = pd.read_sql("SELECT d.id, e.nome as Empresa, p.nome as Colaborador, d.data_servico, d.valor, d.foto_url FROM diarias d JOIN prestadores p ON d.prestador_id = p.id JOIN empresas e ON p.empresa_id = e.id", get_connection())
        st.dataframe(dados[['Empresa', 'Colaborador', 'data_servico', 'valor']], use_container_width=True)
        
        id_v = st.number_input("Ver foto do ID:", min_value=1)
        if st.button("Abrir Folha"):
            img_data = dados[dados['id'] == id_v]['foto_url'].values[0]
            st.image(io.BytesIO(base64.b64decode(img_data)))
