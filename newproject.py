import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, timedelta
import base64
import io

# --- FUNÇÕES DE BANCO DE DADOS ---
def criar_banco():
    conn = sqlite3.connect('verorh.db', check_same_thread=False)
    c = conn.cursor()
    # Criar tabelas se não existirem
    c.execute('''CREATE TABLE IF NOT EXISTS empresas (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS prestadores (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, documento TEXT UNIQUE, empresa_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS diarias (id INTEGER PRIMARY KEY AUTOINCREMENT, prestador_id INTEGER, data TEXT, valor REAL, foto_url TEXT)''')
    conn.commit()
    return conn

conn = criar_banco()

# --- INTERFACE ---
st.set_page_config(page_title="Vero RH - SQLite Local", layout="wide")

st.markdown("<h1 style='color: #E60000;'>vero<span style='color: white; font-weight: 200;'>RH</span></h1>", unsafe_allow_html=True)

menu = ["Vero Master", "RH Empresa", "Financeiro"]
escolha = st.sidebar.selectbox("Acesso", menu)

# --- VERO MASTER ---
if escolha == "Vero Master":
    st.subheader("🏗️ Cadastro de Empresas")
    nome_e = st.text_input("Nome da Empresa")
    if st.button("Cadastrar"):
        try:
            conn.execute("INSERT INTO empresas (nome) VALUES (?)", (nome_e,))
            conn.commit()
            st.success("Empresa salva com sucesso!")
        except:
            st.error("Empresa já cadastrada.")

# --- RH EMPRESA ---
elif escolha == "RH Empresa":
    st.subheader("📋 Gestão da Empresa")
    
    # Selecionar Empresa
    df_e = pd.read_sql("SELECT * FROM empresas", conn)
    if not df_e.empty:
        emp_sel = st.selectbox("Sua Empresa", df_e['nome'].tolist())
        emp_id = df_e[df_e['nome'] == emp_sel]['id'].values[0]
        
        t1, t2 = st.tabs(["Cadastrar Funcionário", "Lançar Diárias"])
        
        with t1:
            n_f = st.text_input("Nome")
            d_f = st.text_input("CPF")
            if st.button("Salvar Colaborador"):
                conn.execute("INSERT INTO prestadores (nome, documento, empresa_id) VALUES (?,?,?)", (n_f, d_f, int(emp_id)))
                conn.commit()
                st.success("Funcionário Cadastrado!")
        
        with t2:
            df_p = pd.read_sql(f"SELECT * FROM prestadores WHERE empresa_id = {emp_id}", conn)
            if not df_p.empty:
                p_nome = st.selectbox("Funcionário", df_p['nome'].tolist())
                p_id = df_p[df_p['nome'] == p_nome]['id'].values[0]
                data_d = st.date_input("Data")
                foto = st.file_uploader("Foto da Folha", type=['jpg','png'])
                
                if st.button("Lançar Diária"):
                    img_b64 = base64.b64encode(foto.read()).decode() if foto else ""
                    conn.execute("INSERT INTO diarias (prestador_id, data, valor, foto_url) VALUES (?,?,?,?)", 
                                 (int(p_id), str(data_d), 150.0, img_b64))
                    conn.commit()
                    st.success("Diária gravada!")
    else:
        st.warning("Nenhuma empresa cadastrada pelo Master.")

# --- FINANCEIRO ---
elif escolha == "Financeiro":
    st.subheader("💰 Auditoria")
    query = """
    SELECT d.id, e.nome as Empresa, p.nome as Funcionario, d.data, d.valor, d.foto_url 
    FROM diarias d 
    JOIN prestadores p ON d.prestador_id = p.id 
    JOIN empresas e ON p.empresa_id = e.id
    """
    df_f = pd.read_sql(query, conn)
    st.dataframe(df_f[['id', 'Empresa', 'Funcionario', 'data', 'valor']], use_container_width=True)
    
    id_img = st.number_input("Ver foto do ID:", min_value=1, step=1)
    if st.button("Abrir Foto"):
        try:
            b64 = df_f[df_f['id'] == id_img]['foto_url'].values[0]
            st.image(io.BytesIO(base64.b64decode(b64)))
        except:
            st.error("Foto não encontrada.")
