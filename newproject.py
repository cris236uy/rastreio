import streamlit as st
from PIL import Image
import pandas as pd
import os

st.set_page_config(page_title="Controle de Estoque - Facilities", layout="wide")
st.title("📦 Sistema de Controle de Estoque")

# --- Função para detectar itens na imagem ---
def detectar_itens(imagem):
    # Aqui você pode integrar um modelo real de detecção
    # Por enquanto, simulamos resultados
    itens_detectados = {
        "Papel": 10,
        "Copos": 20,
        "Produto de Limpeza": 5
    }
    return itens_detectados

# --- Função para gerar relatório ---
def gerar_relatorio_estoque(lista_itens, arquivo_saida="estoque_relatorio.xlsx"):
    df = pd.DataFrame(lista_itens)
    df.to_excel(arquivo_saida, index=False)
    st.success(f"✅ Relatório gerado: {arquivo_saida}")

# --- Upload da imagem ---
arquivo = st.file_uploader("Envie uma foto do estoque", type=["jpg", "png"])
if arquivo:
    imagem = Image.open(arquivo)
    st.image(imagem, caption="Imagem enviada", use_column_width=True)

    # Detectar itens
    itens = detectar_itens(arquivo)
    st.subheader("Itens detectados:")
    st.json(itens)

    # Botão para gerar relatório
    if st.button("Gerar relatório"):
        gerar_relatorio_estoque([itens])
