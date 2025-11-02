# app_lider_ultimate_final.py
import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd
import random

# -------------------------------
# Configuração da página
# -------------------------------
st.set_page_config(page_title="Painel do Líder Ultimate", layout="wide")
st.title("🚀 Painel do Líder Ultimate - Evolução Pessoal e Profissional")

# -------------------------------
# Frases motivacionais
# -------------------------------
frases = [
    "O sucesso é feito de pequenas ações consistentes.",
    "Coragem não é ausência de medo, é agir apesar dele.",
    "Ideias valem ouro quando você age sobre elas.",
    "Grandes líderes inspiram pelo exemplo.",
    "Cada desafio é uma oportunidade disfarçada."
]
st.info(random.choice(frases))

# -------------------------------
# Conexão com banco de dados
# -------------------------------
conn = sqlite3.connect("diario_lider_ultimate.db")
c = conn.cursor()

# Criar tabelas se não existirem
c.execute('''
    CREATE TABLE IF NOT EXISTS diario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        ideia TEXT,
        feito TEXT,
        aprendizado TEXT
    )
''')
c.execute('''
    CREATE TABLE IF NOT EXISTS projetos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        progresso REAL,
        notas TEXT
    )
''')
c.execute('''
    CREATE TABLE IF NOT EXISTS desafios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descricao TEXT,
        status TEXT,
        reflexao TEXT
    )
''')
conn.commit()

# -------------------------------
# Funções auxiliares
# -------------------------------
def adicionar_diario(data, ideia, feito, aprendizado):
    c.execute("INSERT INTO diario (data, ideia, feito, aprendizado) VALUES (?, ?, ?, ?)",
              (data, ideia, feito, aprendizado))
    conn.commit()

def adicionar_projeto(nome, progresso, notas):
    c.execute("INSERT INTO projetos (nome, progresso, notas) VALUES (?, ?, ?)",
              (nome, progresso, notas))
    conn.commit()

def adicionar_desafio(descricao, status, reflexao):
    c.execute("INSERT INTO desafios (descricao, status, reflexao) VALUES (?, ?, ?)",
              (descricao, status, reflexao))
    conn.commit()

def calcular_pontos():
    di = c.execute("SELECT COUNT(*) FROM diario").fetchone()[0]
    de = c.execute("SELECT COUNT(*) FROM desafios WHERE status='Concluído'").fetchone()[0]
    pr_total = c.execute("SELECT SUM(progresso)/100 FROM projetos").fetchone()[0] or 0
    return di*10 + de*20 + int(pr_total*50)

# -------------------------------
# Menu lateral
# -------------------------------
menu = ["Dashboard", "Diário do Líder", "Mini-Projeto 1%", "Desafio de Exposição"]
choice = st.sidebar.selectbox("Navegar", menu)

# -------------------------------
# Tela: Diário do Líder
# -------------------------------
if choice == "Diário do Líder":
    st.header("📝 Diário do Líder")
    data = datetime.now().strftime("%Y-%m-%d")
    ideia = st.text_area("💡 Ideia do dia")
    feito = st.text_area("🔥 O que fiz bem hoje")
    aprendizado = st.text_area("📚 Aprendizado / Observação")
    
    if st.button("Salvar Diário"):
        if ideia or feito or aprendizado:
            adicionar_diario(data, ideia, feito, aprendizado)
            st.success("Diário registrado!")
        else:
            st.warning("Preencha ao menos um campo.")

    st.subheader("📖 Histórico")
    df_diario = pd.read_sql("SELECT * FROM diario ORDER BY id DESC", conn)
    if not df_diario.empty:
        st.dataframe(df_diario)
    else:
        st.info("Nenhum diário registrado ainda.")

# -------------------------------
# Tela: Mini-Projeto 1%
# -------------------------------
elif choice == "Mini-Projeto 1%":
    st.header("💼 Mini-Projeto 1%")
    nome = st.text_input("Nome do Projeto")
    progresso = st.slider("Progresso (%)", 0, 100, 0)
    notas = st.text_area("Notas / Próximo passo")
    
    if st.button("Salvar Projeto"):
        if nome:
            adicionar_projeto(nome, progresso, notas)
            st.success("Projeto salvo!")
        else:
            st.warning("Informe o nome do projeto.")

    st.subheader("📊 Projetos")
    df_projetos = pd.read_sql("SELECT * FROM projetos ORDER BY id DESC", conn)
    if not df_projetos.empty:
        st.bar_chart(df_projetos.set_index('nome')['progresso'])
        st.dataframe(df_projetos)
    else:
        st.info("Nenhum projeto registrado ainda.")

# -------------------------------
# Tela: Desafio de Exposição
# -------------------------------
elif choice == "Desafio de Exposição":
    st.header("⚡ Desafio de Exposição")
    descricao = st.text_area("Descrição")
    status = st.selectbox("Status", ["Não iniciado", "Em progresso", "Concluído"])
    reflexao = st.text_area("Reflexão pós-desafio")
    
    if st.button("Salvar Desafio"):
        if descricao:
            adicionar_desafio(descricao, status, reflexao)
            st.success("Desafio salvo!")
        else:
            st.warning("Informe a descrição.")

    st.subheader("📊 Desafios")
    df_desafios = pd.read_sql("SELECT * FROM desafios ORDER BY id DESC", conn)
    if not df_desafios.empty:
        st.bar_chart(df_desafios['status'].value_counts())
        st.dataframe(df_desafios)
    else:
        st.info("Nenhum desafio registrado ainda.")

# -------------------------------
# Tela: Dashboard Ultimate
# -------------------------------
elif choice == "Dashboard":
    st.header("📈 Painel de Evolução")

    # Carregar todos os dados
    df_diario = pd.read_sql("SELECT * FROM diario ORDER BY id DESC", conn)
    df_projetos = pd.read_sql("SELECT * FROM projetos ORDER BY id DESC", conn)
    df_desafios = pd.read_sql("SELECT * FROM desafios ORDER BY id DESC", conn)

    # Pontos totais
    pontos = calcular_pontos()
    st.metric("🏆 Pontos Totais", pontos)

    # Métricas
    st.metric("📖 Diários Registrados", len(df_diario))
    progresso_medio = round(df_projetos["progresso"].mean(), 2) if not df_projetos.empty else 0
    st.metric("💼 Progresso Médio Projetos (%)", progresso_medio)
    concluidos = df_desafios[df_desafios["status"]=="Concluído"].shape[0] if not df_desafios.empty else 0
    st.metric("⚡ Desafios Concluídos", concluidos)

    # Gráficos de evolução
    st.subheader("📊 Gráficos de Evolução")
    if not df_diario.empty:
        diario_plot = df_diario.copy()
        diario_plot['data'] = pd.to_datetime(diario_plot['data'])
        diario_grouped = diario_plot.groupby('data').count()['id']
        st.line_chart(diario_grouped)
    else:
        st.info("Nenhum diário registrado ainda.")

    if not df_projetos.empty:
        st.bar_chart(df_projetos.set_index('nome')['progresso'])
    else:
        st.info("Nenhum projeto registrado ainda.")

    if not df_desafios.empty:
        st.bar_chart(df_desafios['status'].value_counts())
    else:
        st.info("Nenhum desafio registrado ainda.")

    # Próximas ações
    st.markdown("---")
    st.subheader("💡 Próximas Ações")
    st.write("- Registrar o Diário do Líder diariamente")
    st.write("- Atualizar mini-projeto 1%")
    st.write("- Concluir pelo menos 1 desafio de exposição por semana")
    st.success("🔥 Continue consistente! Cada ação te transforma em líder real.")

st.sidebar.markdown("---")
st.sidebar.info("💡 Dica: Cada ação diária vale pontos. Acumule, registre e visualize sua evolução!")
