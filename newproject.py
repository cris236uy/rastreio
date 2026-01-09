import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# 1. Inicializar o "Estado da Sessão" para os dados não sumirem
if 'dados_app' not in st.session_state:
    st.session_state.dados_app = None

st.title("🚚 App de Logística")

col1, col2 = st.columns(2)
with col1:
    cep_origem = st.text_input("CEP Remetente", key="origem")
with col2:
    cep_destino = st.text_input("CEP Destinatário", key="destino")

# Botão de processamento
if st.button("Calcular e Mapear"):
    with st.spinner('Buscando informações...'):
        # ... (Aqui vai aquela lógica de buscar_cep e buscar_coords que passamos antes) ...
        
        # Simulando o resultado da busca para o exemplo:
        resultado = {
            "info_origem": f"Rua Exemplo, SP", # Substitua pela sua função de busca
            "info_destino": f"Rua Destino, RJ", # Substitua pela sua função de busca
            "distancia": 450.5,
            "coords": [[-23.55, -46.63], [-22.90, -43.17]]
        }
        
        # SALVANDO NA MEMÓRIA
        st.session_state.dados_app = resultado

# 2. SEMPRE mostrar o que estiver na memória (isso impede de sumir)
if st.session_state.dados_app:
    res = st.session_state.dados_app
    
    st.success(f"### Distância: {res['distancia']} km")
    
    c1, c2 = st.columns(2)
    c1.info(f"**Origem:** {res['info_origem']}")
    c2.warning(f"**Destino:** {res['info_destino']}")

    # Renderizar o mapa
    m = folium.Map(location=res['coords'][0], zoom_start=6)
    folium.PolyLine(res['coords'], color="blue").add_to(m)
    st_folium(m, width=700, height=400)
