import streamlit as st
from PIL import Image
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Controle de Estoque - Facilities", layout="wide")
st.title("📦 Sistema de Controle de Estoque Interativo")

# Upload da imagem do estoque
arquivo = st.file_uploader("Envie uma foto do estoque", type=["jpg", "png"])
if arquivo:
    imagem = Image.open(arquivo)
    st.image(imagem, caption="Imagem do Estoque", use_column_width=True)

    st.subheader("Digite a quantidade de cada item detectado:")
    # Formulário para inserir quantidades
    with st.form("quantidades_estoque"):
        papel = st.number_input("Papel", min_value=0, value=0)
        copos = st.number_input("Copos", min_value=0, value=0)
        produto_limpeza = st.number_input("Produto de Limpeza", min_value=0, value=0)
        submitted = st.form_submit_button("Atualizar Estoque")
        
        if submitted:
            # Criar DataFrame com os dados
            dados_estoque = {
                "Item": ["Papel", "Copos", "Produto de Limpeza"],
                "Quantidade": [papel, copos, produto_limpeza]
            }
            df = pd.DataFrame(dados_estoque)

            # Exibir gráfico interativo
            fig = px.bar(df, x="Item", y="Quantidade", color="Item",
                         title="📊 Estoque de Insumos", text="Quantidade")
            fig.update_layout(yaxis_title="Quantidade", xaxis_title="Itens")
            st.plotly_chart(fig, use_container_width=True)

            # Gerar relatório em Excel
            arquivo_saida = "estoque_relatorio.xlsx"
            df.to_excel(arquivo_saida, index=False)
            st.success(f"✅ Relatório gerado: {arquivo_saida}")
