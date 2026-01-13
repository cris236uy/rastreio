import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date, timedelta
import io
import base64
from PIL import Image

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Vero RH - Gestão Nuvem", layout="wide", page_icon="🔴")

# --- DESIGN VERO RH ---
st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%); color: #ffffff; }
        .stButton>button { background: linear-gradient(90deg, #E60000 0%, #990000 100%) !important; color: white !important; border-radius: 25px !important; border: none !important; }
        .logo-vero { color: #E60000; font-weight: 900; font-size: 60px; letter-spacing: -3px; }
        .logo-rh { color: #ffffff; font-weight: 200; font-size: 60px; }
        .login-card { background: rgba(255, 255, 255, 0.05); padding: 40px; border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px); max-width: 500px; margin: auto; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO COM GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_aba(nome_aba):
    try:
        # Tenta ler a aba. Se estiver vazia, retorna um DataFrame com as colunas corretas
        df = conn.read(worksheet=nome_aba, ttl=0)
        return df.dropna(how="all")
    except:
        # Estrutura padrão caso a aba ainda não tenha dados
        estruturas = {
            "empresas": ["id", "nome"],
            "prestadores": ["id", "nome", "documento", "empresa_id"],
            "diarias": ["id", "prestador_id", "data", "valor", "assinatura", "foto_url"]
        }
        return pd.DataFrame(columns=estruturas.get(nome_aba, []))

# --- LOGIN ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown('<div style="text-align:center; padding-top: 50px;"><span class="logo-vero">vero</span><span class="logo-rh">RH</span></div>', unsafe_allow_html=True)
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        perfil = st.selectbox("Acesso", ["Vero Master", "RH Empresa Vinculada", "Financeiro", "Colaborador"])
        
        empresa_selecionada = None
        if perfil == "RH Empresa Vinculada":
            df_emp = carregar_aba("empresas")
            if not df_emp.empty:
                empresa_selecionada = st.selectbox("Sua Empresa", df_emp['nome'].tolist())
            else:
                st.warning("Nenhuma empresa cadastrada pelo Master ainda.")

        senha = st.text_input("Senha", type="password")
        if st.button("ENTRAR NO SISTEMA", use_container_width=True):
            if senha == "vero123":
                st.session_state.update({"autenticado": True, "perfil": perfil, "empresa": empresa_selecionada})
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.sidebar.button("🔴 Sair", on_click=lambda: st.session_state.update({"autenticado": False}))

    # --- PORTAL VERO MASTER ---
    if st.session_state.perfil == "Vero Master":
        st.title("🏗️ Gestão de Empresas Parceiras")
        df_e = carregar_aba("empresas")
        st.write("### Empresas Cadastradas")
        st.dataframe(df_e, use_container_width=True, hide_index=True)
        
        with st.form("add_emp"):
            nome_n = st.text_input("Nome da Empresa Cliente")
            if st.form_submit_button("Vincular Empresa"):
                novo_id = int(df_e['id'].max() + 1) if not df_e.empty else 1
                novo_df = pd.concat([df_e, pd.DataFrame([{"id": novo_id, "nome": nome_n}])], ignore_index=True)
                conn.update(worksheet="empresas", data=novo_df)
                st.success("Empresa salva na Planilha Google!")
                st.rerun()

    # --- PORTAL RH VINCULADO ---
    elif st.session_state.perfil == "RH Empresa Vinculada":
        st.title(f"📋 RH - {st.session_state.empresa}")
        df_p = carregar_aba("prestadores")
        df_e = carregar_aba("empresas")
        emp_id = df_e[df_e['nome'] == st.session_state.empresa]['id'].values[0]

        t1, t2 = st.tabs(["Funcionários", "Enviar Folhas"])
        
        with t1:
            meus_p = df_p[df_p['empresa_id'] == emp_id]
            st.dataframe(meus_p[['id', 'nome', 'documento']], use_container_width=True, hide_index=True)
            with st.form("cad_p"):
                n_p = st.text_input("Nome do Colaborador")
                d_p = st.text_input("CPF")
                if st.form_submit_button("Cadastrar Funcionário"):
                    n_id = int(df_p['id'].max() + 1) if not df_p.empty else 1
                    df_p_novo = pd.concat([df_p, pd.DataFrame([{"id": n_id, "nome": n_p, "documento": d_p, "empresa_id": emp_id}])], ignore_index=True)
                    conn.update(worksheet="prestadores", data=df_p_novo)
                    st.success("Salvo com sucesso!")
                    st.rerun()

        with t2:
            meus_p = df_p[df_p['empresa_id'] == emp_id]
            if not meus_p.empty:
                colab = st.selectbox("Colaborador", meus_p['nome'])
                colab_id = meus_p[meus_p['nome'] == colab]['id'].values[0]
                d1, d2 = st.columns(2)
                inicio = d1.date_input("Início")
                fim = d2.date_input("Fim")
                foto = st.file_uploader("Foto da Folha", type=['jpg', 'png', 'jpeg'])
                
                if st.button("LANÇAR PERÍODO"):
                    df_d = carregar_aba("diarias")
                    img_b64 = base64.b64encode(foto.read()).decode() if foto else ""
                    novos = []
                    curr = inicio
                    while curr <= fim:
                        novos.append({"id": len(df_d)+len(novos)+1, "prestador_id": colab_id, "data": str(curr), "valor": 150.0, "assinatura": 0, "foto_url": img_b64})
                        curr += timedelta(days=1)
                    df_d_final = pd.concat([df_d, pd.DataFrame(novos)], ignore_index=True)
                    conn.update(worksheet="diarias", data=df_d_final)
                    st.success("Diárias enviadas para a Planilha!")

    # --- PORTAL FINANCEIRO ---
    elif st.session_state.perfil == "Financeiro":
        st.title("💰 Auditoria Global")
        df_d = carregar_aba("diarias")
        df_p = carregar_aba("prestadores")
        
        # Merge para mostrar nomes em vez de IDs
        resumo = df_d.merge(df_p, left_on="prestador_id", right_on="id", how="left")
        st.dataframe(resumo[['data', 'nome', 'valor', 'assinatura']], use_container_width=True)
        
        id_view = st.number_input("ID para ver imagem", min_value=1, step=1)
        if st.button("Ver Folha"):
            try:
                b64 = df_d[df_d['id'] == id_view]['foto_url'].values[0]
                st.image(io.BytesIO(base64.b64decode(b64)), use_container_width=True)
            except: st.error("Erro ao carregar imagem.")
