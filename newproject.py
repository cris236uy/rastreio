import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import base64
import io

# --- CONFIGURAÇÃO E BANCO ---
st.set_page_config(page_title="Vero RH - SQLite", layout="wide")

def get_db_connection():
    conn = sqlite3.connect('verorh_data.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS empresas (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS prestadores (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, documento TEXT UNIQUE, empresa_id INTEGER)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS diarias (id INTEGER PRIMARY KEY AUTOINCREMENT, prestador_id INTEGER, data TEXT, valor REAL, foto_url TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- DESIGN ---
st.markdown("""
    <style>
        .stApp { background-color: #0e1117; color: white; }
        .logo-vero { color: #E60000; font-weight: 900; font-size: 40px; }
        .logo-rh { color: #ffffff; font-weight: 200; font-size: 40px; }
        div.stButton > button { background: #E60000; color: white; border-radius: 8px; width: 100%; }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown('<div><span class="logo-vero">vero</span><span class="logo-rh">RH</span></div>', unsafe_allow_html=True)
    perfil = st.selectbox("Acesso", ["Vero Master", "RH Parceiro", "Financeiro"])
    senha = st.text_input("Senha", type="password")

if senha == "vero123":
    # --- MASTER ---
    if perfil == "Vero Master":
        st.title("🏗️ Master - Empresas")
        nome_e = st.text_input("Nova Empresa")
        if st.button("Salvar"):
            conn = get_db_connection()
            conn.execute("INSERT INTO empresas (nome) VALUES (?)", (nome_e,))
            conn.commit()
            conn.close()
            st.success("Salvo!")

    # --- RH ---
    elif perfil == "RH Parceiro":
        st.title("📋 RH - Lançamentos")
        conn = get_db_connection()
        df_e = pd.read_sql("SELECT * FROM empresas", conn)
        
        if not df_e.empty:
            emp_sel = st.selectbox("Sua Empresa", df_e['nome'].tolist())
            emp_id = df_e[df_e['nome'] == emp_sel]['id'].values[0]
            
            tab1, tab2 = st.tabs(["Funcionários", "Diárias"])
            with tab1:
                nf = st.text_input("Nome")
                df = st.text_input("CPF")
                if st.button("Cadastrar Funcionário"):
                    conn.execute("INSERT INTO prestadores (nome, documento, empresa_id) VALUES (?,?,?)", (nf, df, int(emp_id)))
                    conn.commit()
                    st.success("Ok!")
            
            with tab2:
                df_p = pd.read_sql(f"SELECT * FROM prestadores WHERE empresa_id = {emp_id}", conn)
                if not df_p.empty:
                    p_sel = st.selectbox("Funcionário", df_p['nome'].tolist())
                    p_id = df_p[df_p['nome'] == p_sel]['id'].values[0]
                    foto = st.file_uploader("Foto da Folha", type=['jpg','png'])
                    if st.button("Salvar Diária") and foto:
                        img_b64 = base64.b64encode(foto.read()).decode()
                        conn.execute("INSERT INTO diarias (prestador_id, data, valor, foto_url) VALUES (?,?,?,?)", 
                                     (int(p_id), str(date.today()), 150.0, img_b64))
                        conn.commit()
                        st.success("Lançado!")
        conn.close()

    # --- FINANCEIRO (Onde estava o erro de aspas) ---
    elif perfil == "Financeiro":
        st.title("💰 Financeiro")
        conn = get_db_connection()
        
        # AQUI ESTÁ A CORREÇÃO: Três aspas no começo e três no fim.
        query = """
            SELECT d.id, e.nome as Empresa, p.nome as Colaborador, d.data, d.valor, d.foto_url
            FROM diarias d
            JOIN prestadores p ON d.prestador_id = p.id
            JOIN empresas e ON p.empresa_id = e.id
        """
        
        df_fin = pd.read_sql(query, conn)
        conn.close()
        
        if not df_fin.empty:
            st.dataframe(df_fin[['id', 'Empresa', 'Colaborador', 'data', 'valor']], use_container_width=True)
            id_v = st.number_input("Ver foto ID:", min_value=1, step=1)
            if st.button("Visualizar"):
                try:
                    img_data = df_fin[df_fin['id'] == id_v]['foto_url'].values[0]
                    st.image(io.BytesIO(base64.b64decode(img_data)))
                except:
                    st.error("Não encontrado.")
else:
    st.info("Digite a senha correta para continuar.")
