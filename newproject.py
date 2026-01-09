import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from math import radians, cos, sin, asin, sqrt

# Configuração da página
st.set_page_config(page_title="Calculadora de CEP", layout="wide")

def haversine(lon1, lat1, lon2, lat2):
    """Calcula a distância em km entre dois pontos (Haversine)"""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Raio da Terra em km
    return c * r

def buscar_cep(cep):
    url = f"https://viacep.com.br/ws/{cep}/json/"
    response = requests.get(url)
    if response.status_code == 200 and "erro" not in response.json():
        return response.json()
    return None

def buscar_coords(logradouro, localidade, uf):
    query = f"{logradouro}, {localidade}, {uf}, Brasil"
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={query}"
    headers = {'User-Agent': 'MeuAppDeCep/1.0'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200 and len(response.json()) > 0:
        res = response.json()[0]
        return float(res['lat']), float(res['lon'])
    return None

# Interface Streamlit
st.title("🚚 App de Logística: Distância entre CEPs")

col1, col2 = st.columns(2)

with col1:
    cep_origem = st.text_input("CEP Remetente", placeholder="01001000")
with col2:
    cep_destino = st.text_input("CEP Destinatário", placeholder="20020010")

if st.button("Calcular e Mapear"):
    if cep_origem and cep_destino:
        with st.spinner('Buscando informações...'):
            data_origem = buscar_cep(cep_origem)
            data_destino = buscar_cep(cep_destino)

            if data_origem and data_destino:
                coords_origem = buscar_coords(data_origem['logradouro'], data_origem['localidade'], data_origem['uf'])
                coords_destino = buscar_coords(data_destino['logradouro'], data_destino['localidade'], data_destino['uf'])

                if coords_origem and coords_destino:
                    distancia = haversine(coords_origem[1], coords_origem[0], coords_destino[1], coords_destino[0])
                    
                    # Exibição de Dados
                    st.success(f"### Distância Estimada: {distancia:.2f} km")
                    
                    res1, res2 = st.columns(2)
                    res1.info(f"**Origem:** {data_origem['logradouro']}, {data_origem['bairro']} - {data_origem['localidade']}/{data_origem['uf']}")
                    res2.warning(f"**Destino:** {data_destino['logradouro']}, {data_destino['bairro']} - {data_destino['localidade']}/{data_destino['uf']}")

                    # Mapa com Folium
                    m = folium.Map(location=[(coords_origem[0] + coords_destino[0])/2, 
                                           (coords_origem[1] + coords_destino[1])/2], zoom_start=5)
                    
                    folium.Marker(coords_origem, popup="Origem", icon=folium.Icon(color='blue')).add_to(m)
                    folium.Marker(coords_destino, popup="Destino", icon=folium.Icon(color='red')).add_to(m)
                    folium.PolyLine([coords_origem, coords_destino], color="black", weight=2.5, opacity=1).add_to(m)
                    
                    st_folium(m, width=1200, height=500)
                else:
                    st.error("Não foi possível obter as coordenadas geográficas exatas.")
            else:
                st.error("Um ou ambos os CEPs são inválidos.")
    else:
        st.warning("Por favor, preencha os dois CEPs.")
