import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# --- CONFIGURAÇÕES E ESTADOS ---
st.set_page_config(page_title="Validador de Logística", layout="wide")

if 'resultado' not in st.session_state:
    st.session_state.resultado = None

# --- FUNÇÕES DE API ---

def buscar_dados_cep(cep):
    """Conecta com a API ViaCEP"""
    url = f"https://viacep.com.br/ws/{cep}/json/"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            dados = response.json()
            if "erro" in dados:
                return None, "CEP não encontrado."
            return dados, None
        return None, f"Erro na API ViaCEP: Status {response.status_code}"
    except Exception as e:
        return None, f"Falha de conexão: {str(e)}"

def buscar_coordenadas(logradouro, cidade, uf):
    """Conecta com a API Nominatim (OpenStreetMap)"""
    # IMPORTANTE: O Header User-Agent é obrigatório para não ser bloqueado
    headers = {'User-Agent': 'MeuAppLogistica/1.0 (contato@exemplo.com)'}
    query = f"{logradouro}, {cidade}, {uf}, Brasil"
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={query}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        dados = response.json()
        if response.status_code == 200 and len(dados) > 0:
            return (float(dados[0]['lat']), float(dados[0]['lon'])), None
        return None, "Coordenadas não encontradas para este endereço."
    except Exception as e:
        return None, f"Erro no Mapa: {str(e)}"

# --- INTERFACE ---
st.title("📍 Localizador e Medidor de CEPs")

col1, col2 = st.columns(2)
with col1:
    cep_origem = st.text_input("CEP Origem", placeholder="Ex: 01001000")
with col2:
    cep_destino = st.text_input("CEP Destino", placeholder="Ex: 20020010")

if st.button("Consultar APIs e Gerar Mapa"):
    with st.spinner('Consultando APIs...'):
        # 1. Busca dados do Remetente
        dados_o, erro_o = buscar_dados_cep(cep_origem)
        # 2. Busca dados do Destinatário
        dados_d, erro_d = buscar_dados_cep(cep_destino)

        if dados_o and dados_d:
            # 3. Busca Coordenadas (Se houver endereço)
            coord_o, err_co = buscar_coordenadas(dados_o['logradouro'], dados_o['localidade'], dados_o['uf'])
            coord_d, err_cd = buscar_coordenadas(dados_d['logradouro'], dados_d['localidade'], dados_d['uf'])

            if coord_o and coord_d:
                # Salva tudo no estado da sessão para não sumir
                st.session_state.resultado = {
                    "origem": dados_o,
                    "destino": dados_d,
                    "coords": [coord_o, coord_d]
                }
            else:
                st.error(f"Erro de Geolocalização: {err_co or err_cd}")
        else:
            st.error(f"Erro nos CEPs: {erro_o or erro_d}")

# --- EXIBIÇÃO DOS RESULTADOS (Persistente) ---
if st.session_state.resultado:
    res = st.session_state.resultado
    
    st.markdown("---")
    c1, c2 = st.columns(2)
    
    with c1:
        st.info(f"**REMETENTE**\n\n{res['origem']['logradouro']}\n\n{res['origem']['localidade']} - {res['origem']['uf']}")
    with c2:
        st.warning(f"**DESTINATÁRIO**\n\n{res['destino']['logradouro']}\n\n{res['destino']['localidade']} - {res['destino']['uf']}")

    # Gerar Mapa
    m = folium.Map(location=res['coords'][0], zoom_start=5)
    folium.Marker(res['coords'][0], tooltip="Origem", icon=folium.Icon(color='blue')).add_to(m)
    folium.Marker(res['coords'][1], tooltip="Destino", icon=folium.Icon(color='red')).add_to(m)
    folium.PolyLine(res['coords'], color="black", weight=2, opacity=0.8).add_to(m)
    
    st_folium(m, width="100%", height=400)
