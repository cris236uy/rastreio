import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, timedelta
import base64
import io

# --- CONFIGURAÇÃO E BANCO ---
st.set_page_config(page_title="Vero RH - Sistema de Diárias", layout="wide")

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
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] { background-color: #1d2127; border-radius: 5px; color: white; padding: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown('<div><span class="logo-vero">vero</span><span class="logo-rh">RH</span></div>', unsafe_allow_html=True)
    st.divider()
    perfil = st.selectbox("Selecione seu Perfil", ["Colaborador", "RH Parceiro", "Vero Master", "Financeiro"])
    
    if perfil != "Colaborador":
        senha = st.text_input("Senha de Acesso", type="password")
    else:
        doc_login = st.text_input("Digite seu CPF (apenas números)")
        senha = "ok" if doc_login else ""

# --- LÓGICA DE ACESSO ---
if (perfil != "Colaborador" and senha == "vero123") or (perfil == "Colaborador" and doc_login):

    # --- 1. COLABORADOR (VISUALIZAÇÃO) ---
    if perfil == "Colaborador":
        st.title(f"👋 Olá, Colaborador")
        conn = get_db_connection()
        # Busca os dados do colaborador pelo documento
        user = pd.read_sql(f"SELECT * FROM prestadores WHERE documento = '{doc_login}'", conn)
        
        if not user.empty:
            u_id = user['id'].values[0]
            st.subheader(f"Histórico de Diárias: {user['nome'].values[0]}")
            
            # Busca todas as diárias desse ID
            diarias_user = pd.read_sql(f"SELECT id, data, valor, foto_url FROM diarias WHERE prestador_id = {u_id} ORDER BY data DESC", conn)
            
            if not diarias_user.empty:
                col1, col2 = st.columns(2)
                col1.metric("Total de Diárias", len(diarias_user))
                col2.metric("Total a Receber", f"R$ {diarias_user['valor'].sum():,.2f}")
                
                st.dataframe(diarias_user[['data', 'valor']], use_container_width=True)
                
                # Ver Foto
                st.divider()
                id_foto = st.selectbox("Selecione o ID da diária para ver a folha", diarias_user['id'].tolist())
                if st.button("Ver Folha de Ponto"):
                    img_data = diarias_user[diarias_user['id'] == id_foto]['foto_url'].values[0]
                    st.image(io.BytesIO(base64.b64decode(img_data)))
            else:
                st.info("Nenhuma diária lançada para o seu perfil ainda.")
        else:
            st.error("Colaborador não encontrado. Verifique o CPF ou contate o RH.")
        conn.close()

    # --- 2. MASTER ---
    elif perfil == "Vero Master":
        st.title("🏗️ Master - Gestão de Empresas")
        nome_e = st.text_input("Nome da Nova Empresa")
        if st.button("Cadastrar Empresa"):
            conn = get_db_connection()
            try:
                conn.execute("INSERT INTO empresas (nome) VALUES (?)", (nome_e,))
                conn.commit()
                st.success("Empresa cadastrada!")
            except: st.error("Erro ou empresa já existente.")
            conn.close()

    # --- 3. RH PARCEIRO (LANÇAMENTO EM MASSA) ---
    elif perfil == "RH Parceiro":
        st.title("📋 RH - Lançamento por Intervalo")
        conn = get_db_connection()
        df_e = pd.read_sql("SELECT * FROM empresas", conn)
        
        if not df_e.empty:
            emp_sel = st.selectbox("Selecione sua Empresa", df_e['nome'].tolist())
            emp_id = df_e[df_e['nome'] == emp_sel]['id'].values[0]
            
            tab1, tab2 = st.tabs(["Cadastrar Colaborador", "Lançar Período de Trabalho"])
            
            with tab1:
                nf = st.text_input("Nome Completo")
                df = st.text_input("CPF (Login do Colaborador)")
                if st.button("Salvar Funcionário"):
                    conn.execute("INSERT INTO prestadores (nome, documento, empresa_id) VALUES (?,?,?)", (nf, df, int(emp_id)))
                    conn.commit()
                    st.success("Cadastrado!")
            
            with tab2:
                df_p = pd.read_sql(f"SELECT * FROM prestadores WHERE empresa_id = {emp_id}", conn)
                if not df_p.empty:
                    p_sel = st.selectbox("Selecione o Colaborador", df_p['nome'].tolist())
                    p_id = df_p[df_p['nome'] == p_sel]['id'].values[0]
                    
                    col_data1, col_data2 = st.columns(2)
                    data_inicio = col_data1.date_input("Data de Início", date.today())
                    data_fim = col_data2.date_input("Data de Fim", date.today())
                    
                    valor_diaria = st.number_input("Valor da Diária (R$)", value=150.0)
                    foto = st.file_uploader("Foto da Folha de Ponto (Intervalo)", type=['jpg','png','jpeg'])
                    
                    if st.button("🚀 Lançar Período Completo"):
                        if foto and data_fim >= data_inicio:
                            img_b64 = base64.b64encode(foto.read()).decode()
                            
                            # Lógica para percorrer os dias
                            dias_lancados = 0
                            data_atual = data_inicio
                            while data_atual <= data_fim:
                                conn.execute("INSERT INTO diarias (prestador_id, data, valor, foto_url) VALUES (?,?,?,?)", 
                                             (int(p_id), str(data_atual), valor_diaria, img_b64))
                                data_atual += timedelta(days=1)
                                dias_lancados += 1
                            
                            conn.commit()
                            st.success(f"Sucesso! Foram lançadas {dias_lancados} diárias para este colaborador.")
                        else:
                            st.error("Verifique a foto e se a data final é maior que a inicial.")
        conn.close()

    # --- 4. FINANCEIRO ---
    elif perfil == "Financeiro":
        st.title("💰 Financeiro - Auditoria")
        conn = get_db_connection()
        query = """
            SELECT d.id, e.nome as Empresa, p.nome as Colaborador, d.data, d.valor, d.foto_url
            FROM diarias d
            JOIN prestadores p ON d.prestador_id = p.id
            JOIN empresas e ON p.empresa_id = e.id
            ORDER BY d.data DESC
        """
        df_fin = pd.read_sql(query, conn)
        conn.close()
        
        if not df_fin.empty:
            st.dataframe(df_fin[['id', 'Empresa', 'Colaborador', 'data', 'valor']], use_container_width=True)
            id_v = st.number_input("Ver foto pelo ID:", min_value=1, step=1)
            if st.button("Abrir Comprovante"):
                try:
                    img_data = df_fin[df_fin['id'] == id_v]['foto_url'].values[0]
                    st.image(io.BytesIO(base64.b64decode(img_data)))
                except: st.error("Não encontrado.")
else:
    st.info("Aguardando login correto na barra lateral.")
