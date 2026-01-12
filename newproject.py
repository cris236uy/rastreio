import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import io
import re
from PIL import Image
import pytesseract
import platform

# --- CONFIGURAÇÃO AUTOMÁTICA DO TESSERACT ---
def configurar_tesseract():
    if platform.system() == "Windows":
        # Ajuste o caminho abaixo para o seu local de instalação no Windows
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    # No Linux (Streamlit Cloud), o comando 'tesseract' já fica no PATH global via packages.txt

configurar_tesseract()

# --- BANCO DE DADOS ---
def conectar():
    return sqlite3.connect('financeiro_diarias.db')

def inicializar_banco():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS prestadores (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT, documento TEXT UNIQUE, chave_pix TEXT, contato TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS diarias (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, prestador_id INTEGER,
                        data_servico DATE, valor REAL, status TEXT DEFAULT 'Pendente')''')
    conn.commit()
    conn.close()

inicializar_banco()

# --- EXTRAÇÃO DE DADOS (BASEADO NA SUA FOLHA VERO RH) ---
def extrair_dados_folha(imagem):
    try:
        img = Image.open(imagem)
        # O lang='por' requer que o tesseract-ocr-por esteja instalado
        texto = pytesseract.image_to_string(img, lang='por')
        
        dados = {"nome": "", "cpf": "", "contato": "", "pix": "", "dia": ""}

        # Nome: Pega o que está escrito após 'Nome:'
        nome_search = re.search(r"Nome:\s*([A-Za-z\s]+)", texto, re.I)
        if nome_search: dados["nome"] = nome_search.group(1).strip()

        # CPF: 11 dígitos
        cpf_search = re.search(r"(\d{3}\.?\d{3}\.?\d{3}-?\d{2})", texto)
        if cpf_search: dados["cpf"] = cpf_search.group(1)

        # Contato: Telefone com DDD
        contato_search = re.search(r"(\(?\d{2}\)?\s?\d{4,5}-?\d{4})", texto)
        if contato_search: dados["contato"] = contato_search.group(1)

        # Pix: Pega e-mail ou sequência após 'PIX'
        pix_search = re.search(r"PIX:\s*([^\s\n]+)", texto, re.I)
        if pix_search: dados["pix"] = pix_search.group(1).strip()

        # Dia: Busca número da linha com horário (ex: 15:00 na linha 09)
        dia_search = re.search(r"(\d{2})\s+\d{2}[:\.]\d{2}", texto)
        if dia_search: dados["dia"] = dia_search.group(1)

        return dados, texto
    except Exception as e:
        return None, f"Erro no motor OCR: {str(e)}"

# --- INTERFACE ---
st.set_page_config(page_title="Vero RH - Automação", layout="wide")
st.title("📄 Processador de Diárias Inteligente")

menu = st.sidebar.radio("Navegação", ["Processar Nova Folha", "Gestão de Pagamentos"])

if menu == "Processar Nova Folha":
    upload = st.file_uploader("Suba a foto da folha de presença", type=['jpg', 'png', 'jpeg'])

    if upload:
        dados, texto_bruto = extrair_dados_folha(upload)
        
        if dados:
            st.success("Leitura concluída! Verifique os campos abaixo:")
            with st.form("confirmacao_dados"):
                c1, c2 = st.columns(2)
                nome_f = c1.text_input("Nome", value=dados['nome'])
                cpf_f = c2.text_input("CPF", value=dados['cpf'])
                pix_f = c1.text_input("Chave PIX", value=dados['pix'])
                dia_f = c2.text_input("Dia do Mês", value=dados['dia'])
                valor_f = st.number_input("Valor Diária (R$)", value=150.0)

                if st.form_submit_button("Salvar Diária"):
                    conn = conectar()
                    cursor = conn.cursor()
                    # Garante que o prestador existe
                    cursor.execute("INSERT OR IGNORE INTO prestadores (nome, documento, chave_pix) VALUES (?,?,?)", 
                                   (nome_f, cpf_f, pix_f))
                    cursor.execute("SELECT id FROM prestadores WHERE documento = ?", (cpf_f,))
                    p_id = cursor.fetchone()[0]
                    
                    # Salva diária
                    data_diaria = date(date.today().year, date.today().month, int(dia_f) if dia_f else 1)
                    cursor.execute("INSERT INTO diarias (prestador_id, data_servico, valor) VALUES (?,?,?)", 
                                   (p_id, data_diaria, valor_f))
                    conn.commit()
                    conn.close()
                    st.success("Diária registrada com sucesso!")
        else:
            st.error(texto_bruto)

elif menu == "Gestão de Pagamentos":
    conn = conectar()
    df = pd.read_sql_query('''SELECT d.id, p.nome, d.data_servico as Data, d.valor as R$, d.status 
                              FROM diarias d JOIN prestadores p ON d.prestador_id = p.id''', conn)
    conn.close()
    st.dataframe(df, use_container_width=True)
    
    # Botão para Exportar Excel
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    st.download_button("📥 Baixar Relatório Excel", buffer, "relatorio.xlsx")
