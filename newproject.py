import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Controle de Estoque - Facilities", layout="wide")
st.title("📦 Sistema de Controle de Estoque por Setor")

# Lista de setores
setores = [
    "COI", "LOGISTICA", "EMPACOTAMENTO", "FÁBRICA", "BALANÇA",
    "AMBULATÓRIO", "EXTRAÇÃO", "EMPACOTAMENTO FEM", "VESTIARIO",
    "CORPORATIVO I", "CORPORATIVO 2", "FACILITIES"
]

# Lista de materiais
materiais = [
    "Papel higiênico (pacote c/ 8 unidade)",
    "Papel Toalha (pacote c/ 8 unidade)",
    "Sab. Erva doce 5 LT",
    "Saco para lixo preto 100 L",
    "Saco para lixo preto 40 L",
    "Saco para lixo preto 60 L",
    "Saco para lixo (300 L)",
    "Saco Azul (60 L)",
    "Saco Azul 100L",
    "Saco Azul 300 L",
    "Saco Vermelho 60 L",
    "Saco Vermelho 100L",
    "Saco Vermelho 300 L",
    "Saco Cinza 60 L",
    "Saco Cinza 100L",
    "Saco Cinza 300 L",
    "Saco Marrom 60 L",
    "Saco Marrom 100L",
    "Saco Marrom 300 L",
    "Saco Amarelo 100L",
    "Saco Amarelo 300 L",
    "Saco Laranja 100 L",
    "Saco Laranja 300 L",
    "Saco Verde 60 L",
    "Saco Verde 100 L",
    "Saco Verde 300 L",
    "Detergente",
    "Pedra Sanitária",
    "Copo 180 ML (2,5 mil/cx)",
    "ALCOOL GEL INOD BACT 800ML",
    "Sab. Bactericida 800 ML",
    "Querosene",
    "Saco para lixo (200 L)",
    "Alvejante",
    "Saponaceo",
    "Esponja dupla face",
    "Desodorizador ar / 360ml",
    "Pano p/ pia"
]

# Seleção do setor
setor_selecionado = st.selectbox("Selecione o setor que fará a requisição:", setores)

st.subheader(f"Registrar requisição para o setor: {setor_selecionado}")

# Formulário de quantidades
with st.form("form_requisicao"):
    quantidades = {}
    for item in materiais:
        quantidades[item] = st.number_input(item, min_value=0, value=0)
    submitted = st.form_submit_button("Registrar Requisição")
    
    if submitted:
        df = pd.DataFrame({
            "Setor": [setor_selecionado]*len(materiais),
            "Material": list(quantidades.keys()),
            "Quantidade": list(quantidades.values())
        })
        
        st.success("✅ Requisição registrada com sucesso!")
        
        # Exibir gráfico interativo
        fig = px.bar(df[df["Quantidade"] > 0], x="Material", y="Quantidade", color="Material",
                     title=f"Requisição do setor {setor_selecionado}", text="Quantidade")
        fig.update_layout(xaxis_tickangle=-45, yaxis_title="Quantidade", xaxis_title="Materiais")
        st.plotly_chart(fig, use_container_width=True)
        
        # Salvar relatório Excel
        arquivo_excel = f"requisicao_{setor_selecionado}.xlsx"
        df.to_excel(arquivo_excel, index=False)
        st.success(f"Relatório gerado: {arquivo_excel}")
