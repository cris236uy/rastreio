import streamlit as st
import pandas as pd
import sqlite3
import random
from datetime import datetime
import plotly.express as px

# --- Banco de Dados ---
def init_db():
    conn = sqlite3.connect("diario_lider.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS diarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            texto TEXT,
            data TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS projetos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descricao TEXT,
            status TEXT,
            data TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS desafios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descricao TEXT,
            status TEXT,
            data TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- Funções CRUD ---
def add_registro(tabela, titulo, texto="", status="Em andamento"):
    conn = sqlite3.connect("diario_lider.db")
    c = conn.cursor()
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if tabela == "diarios":
        c.execute("INSERT INTO diarios (titulo, texto, data) VALUES (?, ?, ?)", (titulo, texto, data))
    else:
        c.execute(f"INSERT INTO {tabela} (titulo, descricao, status, data) VALUES (?, ?, ?, ?)",
                  (titulo, texto, status, data))
    conn.commit()
    conn.close()

def get_registros(tabela):
    conn = sqlite3.connect("diario_lider.db")
    df = pd.read_sql_query(f"SELECT * FROM {tabela}", conn)
    conn.close()
    return df

def update_registro(tabela, id, titulo, texto="", status=None):
    conn = sqlite3.connect("diario_lider.db")
    c = conn.cursor()
    if tabela == "diarios":
        c.execute("UPDATE diarios SET titulo = ?, texto = ? WHERE id = ?", (titulo, texto, id))
    else:
        c.execute(f"UPDATE {tabela} SET titulo = ?, descricao = ?, status = ? WHERE id = ?",
                  (titulo, texto, status, id))
    conn.commit()
    conn.close()

def delete_registro(tabela, id):
    conn = sqlite3.connect("diario_lider.db")
    c = conn.cursor()
    c.execute(f"DELETE FROM {tabela} WHERE id = ?", (id,))
    conn.commit()
    conn.close()

# --- Frases motivacionais ---
frases = [
    "🚀 Todo líder já começou com a primeira pequena coragem.",
    "🔥 Grandes ideias nascem de mentes que não têm medo de falhar.",
    "⏳ O tempo passa, mas a sua evolução só depende de você.",
    "💡 Uma ideia por dia te separa da mediocridade.",
    "🧠 Quem aprende, lidera. Quem lidera, transforma."
]

st.markdown(f"""
<div style='padding: 20px; background-color: #f5f5f5; border-radius: 10px; text-align: center;'>
    <h2 style='color: #ff6600;'>Diário do Líder • Cresça, Inspire, Evolua</h2>
    <p style='font-size: 18px; color: #333;'>{random.choice(frases)}</p>
</div>
""", unsafe_allow_html=True)

# --- Menu ---
menu = st.sidebar.selectbox("Menu", ["📊 Dashboard", "📖 Diário", "💼 Mini Projetos", "⚡ Desafios", "🎛️ Gerenciar Registros"])

# --- Função de formulário de adição ---
def formulario_adicionar(tabela, titulo_placeholder, texto_placeholder, status_opcional=False):
    st.subheader(f"Adicionar {tabela.capitalize()}")
    titulo = st.text_input("Título", placeholder=titulo_placeholder)
    texto = st.text_area("Descrição / Texto", placeholder=texto_placeholder)
    status = "Em andamento"
    if status_opcional:
        status = st.selectbox("Status", ["Em andamento", "Concluído", "Pausado"])
    if st.button(f"Adicionar {tabela.capitalize()}"):
        if titulo:
            add_registro(tabela, titulo, texto, status)
            st.success(f"{tabela.capitalize()} adicionada com sucesso!")
        else:
            st.error("O título é obrigatório!")

# --- Função para colorir status ---
def cor_status(status):
    cores = {"Em andamento": "#3498db", "Concluído": "#2ecc71", "Pausado": "#e67e22"}
    return cores.get(status, "#95a5a6")

# --- Dashboard ---
if menu == "📊 Dashboard":
    st.subheader("📈 Resumo do Progresso")
    
    diarios = get_registros("diarios")
    projetos = get_registros("projetos")
    desafios = get_registros("desafios")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Diários", len(diarios))
    col2.metric("Projetos", len(projetos))
    col3.metric("Desafios", len(desafios))
    
    # Gráfico de status de projetos
    if not projetos.empty:
        df_proj_status = projetos['status'].value_counts().reset_index()
        df_proj_status.columns = ['Status','Quantidade']
        fig_proj = px.pie(df_proj_status, names='Status', values='Quantidade', title="Status dos Projetos",
                          color='Status', color_discrete_map={"Em andamento":"#3498db","Concluído":"#2ecc71","Pausado":"#e67e22"})
        st.plotly_chart(fig_proj)
    
    # Gráfico de status de desafios
    if not desafios.empty:
        df_desaf_status = desafios['status'].value_counts().reset_index()
        df_desaf_status.columns = ['Status','Quantidade']
        fig_desaf = px.pie(df_desaf_status, names='Status', values='Quantidade', title="Status dos Desafios",
                          color='Status', color_discrete_map={"Em andamento":"#3498db","Concluído":"#2ecc71","Pausado":"#e67e22"})
        st.plotly_chart(fig_desaf)

# --- Telas de cadastro ---
elif menu == "📖 Diário":
    formulario_adicionar("diarios", "Meu primeiro insight", "Escreva aqui seus pensamentos e aprendizados...")

elif menu == "💼 Mini Projetos":
    formulario_adicionar("projetos", "Projeto Exemplo", "Descreva seu mini projeto...", status_opcional=True)

elif menu == "⚡ Desafios":
    formulario_adicionar("desafios", "Desafio Exemplo", "Descreva o desafio...", status_opcional=True)

# --- Gerenciar registros com cards ---
elif menu == "🎛️ Gerenciar Registros":
    st.subheader("Gerenciar registros")
    abas = st.tabs(["📖 Diários", "💼 Mini Projetos", "⚡ Desafios"])
    tabelas = ["diarios", "projetos", "desafios"]

    for i, tabela in enumerate(tabelas):
        with abas[i]:
            df = get_registros(tabela)
            if df.empty:
                st.warning(f"Nenhum registro em {tabela}.")
            else:
                for index, row in df.iterrows():
                    cor = "#f5f5f5" if tabela=="diarios" else cor_status(row["status"])
                    st.markdown(f"""
                    <div style='padding:15px; margin-bottom:10px; background-color:{cor}; border-radius:10px;'>
                        <h4>{row['titulo']}</h4>
                        <p>{row['texto'] if tabela=='diarios' else row['descricao']}</p>
                        <p>Status: <b>{row['status'] if tabela!='diarios' else '—'}</b></p>
                        <p><i>Cadastrado em: {row['data']}</i></p>
                    </div>
                    """, unsafe_allow_html=True)

                    # Edição
                    new_titulo = st.text_input(f"Título ({row['id']})", row["titulo"], key=f"titulo{row['id']}")
                    new_texto = st.text_area(f"Texto/Descrição ({row['id']})", row["texto"] if tabela=="diarios" else row["descricao"], key=f"text{row['id']}")
                    new_status = None
                    if tabela != "diarios":
                        new_status = st.selectbox(f"Status ({row['id']})", ["Em andamento","Concluído","Pausado"], index=["Em andamento","Concluído","Pausado"].index(row["status"]), key=f"status{row['id']}")
                    
                    col1, col2 = st.columns([1,1])
                    with col1:
                        if st.button(f"Salvar alterações ({row['id']})"):
                            update_registro(tabela, row['id'], new_titulo, new_texto, new_status)
                            st.success("Registro atualizado!")
                    with col2:
                        if st.button(f"Excluir ({row['id']})"):
                            delete_registro(tabela, row['id'])
                            st.warning("Registro excluído!")
