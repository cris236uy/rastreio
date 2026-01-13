import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, timedelta
import base64
import io

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
    # Tabela de Colaboradores
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

# --- DESIGN VERO RH (CSS) ---
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
    perfil = st.selectbox("Selecione seu Acesso", ["Vero Master", "RH Parceiro", "Colaborador", "Financeiro"])
    
    if perfil == "Colaborador":
        usuario_doc = st.text_input("Digite seu CPF (apenas números)")
        acesso_liberado = (len(usuario_doc) > 0)
    else:
        senha = st.text_input("Senha de Acesso", type="password")
        acesso_liberado = (senha == "vero123")

# --- CONTEÚDO PRINCIPAL ---
if not acesso_liberado:
    st.warning("Por favor, realize o login na barra lateral.")
else:
    # --- 1. VERO MASTER ---
    if perfil == "Vero Master":
        st.title("🏗️ Master - Gestão de Empresas")
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
                    except: st.error("Empresa já existe.")
                    finally: conn.close()
            st.markdown('</div>', unsafe_allow_html=True)
        
        df_e = pd.read_sql("SELECT * FROM empresas", get_db_connection())
        st.dataframe(df_e, use_container_width=True, hide_index=True)

    # --- 2. RH PARCEIRO ---
    elif perfil == "RH Parceiro":
        st.title("📋 Painel do RH")
        conn = get_db_connection()
        empresas = pd.read_sql("SELECT * FROM empresas", conn)
        
        if empresas.empty:
            st.error("Nenhuma empresa cadastrada.")
        else:
            emp_opcoes = {row['nome']: row['id'] for _, row in empresas.iterrows()}
            emp_sel_nome = st.selectbox("Selecione a Empresa", list(emp_opcoes.keys()))
            emp_id = emp_opcoes[emp_sel_nome]

            t1, t2 = st.tabs(["👥 Cadastrar Colaborador", "📅 Lançar Intervalo de Diárias"])

            with t1:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                with st.form("f_colab"):
                    n_f = st.text_input("Nome do Colaborador")
                    d_f = st.text_input("CPF (será o login)")
                    if st.form_submit_button("Salvar"):
                        try:
                            conn.execute("INSERT INTO prestadores (nome, documento, empresa_id) VALUES (?,?,?)", (n_f, d_f, emp_id))
                            conn.commit()
                            st.success("Cadastrado!")
                        except: st.error("CPF já existe.")
                st.markdown('</div>', unsafe_allow_html=True)

            with t2:
                prestadores = pd.read_sql(f"SELECT * FROM prestadores WHERE empresa_id = {emp_id}", conn)
                if not prestadores.empty:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    p_dict = {row['nome']: row['id'] for _, row in prestadores.iterrows()}
                    p_sel = st.selectbox("Funcionário", list(p_dict.keys()))
                    
                    col_data1, col_data2 = st.columns(2)
                    data_inicio = col_data1.date_input("Data de Início", date.today())
                    data_fim = col_data2.date_input("Data de Fim", date.today())
                    
                    foto = st.file_uploader("Foto da Folha de Ponto", type=['jpg', 'jpeg', 'png'])
                    
                    if st.button("Lançar Período Completo"):
                        if foto and data_fim >= data_inicio:
                            img_b64 = base64.b64encode(foto.read()).decode()
                            # Loop para inserir cada dia do intervalo
                            atual = data_inicio
                            dias_cont = 0
                            while atual <= data_fim:
                                conn.execute("INSERT INTO diarias (prestador_id, data, valor, foto_url) VALUES (?,?,?,?)",
                                             (p_dict[p_sel], str(atual), 150.0, img_b64))
                                atual += timedelta(days=1)
                                dias_cont += 1
                            conn.commit()
                            st.success(f"Sucesso! {dias_cont} diárias lançadas para {p_sel}.")
                        else:
                            st.error("Verifique as datas e a foto.")
                    st.markdown('</div>', unsafe_allow_html=True)
        conn.close()

    # --- 3. COLABORADOR ---
    elif perfil == "Colaborador":
        st.title("👤 Meu Extrato")
        conn = get_db_connection()
        colab = conn.execute("SELECT * FROM prestadores WHERE documento = ?", (usuario_doc,)).fetchone()
        
        if colab:
            st.info(f"Bem-vindo, {colab['nome']}!")
            query = f"""
                SELECT data, valor FROM diarias 
                WHERE prestador_id = {colab['id']} 
                ORDER BY data DESC
            """
            df_colab = pd.read_sql(query, conn)
            if not df_colab.empty:
                st.metric("Total de Diárias", len(df_colab))
                st.dataframe(df_colab, use_container_width=True)
            else:
                st.write("Nenhuma diária encontrada.")
        else:
            st.error("Colaborador não encontrado com este CPF.")
        conn.close()

    # --- 4. FINANCEIRO ---
    elif perfil == "Financeiro":
        st.title("💰 Financeiro")
        query = """
            SELECT d.id, e.nome as Empresa, p.nome as Colaborador, d.data, d.valor, d.foto_url
            FROM diarias d
            JOIN prestadores p ON d.prestador_id = p.id
            JOIN empresas e ON p.empresa_id =
