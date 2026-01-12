import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import re
from PIL import Image, ImageOps, ImageFilter
import pytesseract
import platform

# --- CONFIGURAÇÃO DO TESSERACT ---
def configurar_tesseract():
    if platform.system() == "Windows":
        # Altere para o seu caminho local se estiver testando no Windows
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

configurar_tesseract()

# --- BANCO DE DADOS ---
def inicializar_banco():
    conn = sqlite3.connect('financeiro_diarias.db')
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

# --- TRATAMENTO DE IMAGEM E OCR ---
def processar_ocr(imagem_upload):
    try:
        img = Image.open(imagem_upload)
        
        # Pré-processamento para melhorar a leitura de manuscritos
        img = ImageOps.grayscale(img) # Cinza
        img = img.filter(ImageFilter.SHARPEN) # Nitidez
        
        texto = pytesseract.image_to_string(img, lang='por')
        
        dados = {"nome": "", "cpf": "", "contato": "", "pix": "", "dia": ""}

        # Regex customizadas para a folha Vero RH
        # Nome: captura após 'Nome:'
        nome_search = re.search(r"Nome:\s*([A-Za-z\s]+)", texto, re.I)
        if nome_search: dados["nome"] = nome_search.group(1).strip()

        # CPF: padrão de 11 dígitos
        cpf_search = re.search(r"(\d{3}\.?\d{3}\.?\d{3}-?\d{2})", texto)
        if cpf_search: dados["cpf"] = cpf_search.group(1)

        # Contato: padrão (XX) XXXXX-XXXX
        contato_search = re.search(r"(\(?\d{2}\)?\s?\d{4,5}-?\d{4})", texto)
        if contato_search: dados["contato"] = contato_search.group(1)

        # PIX: captura após 'CHAVE PIX:'
        pix_search = re.search(r"PIX:\s*([^\s\n]+)", texto, re.I)
        if pix_search: dados["pix"] = pix_search.group(1).strip()

        # DIA: busca o número da linha que tem horários preenchidos (ex: 15:00)
        # Na sua imagem, o OCR detectará '09 15:00'
        dia_search = re.search(r"(\d{2})\s+\d{2}[:\.]\d{2}", texto)
        if dia_search: dados["dia"] = dia_search.group(1)

        return dados, texto
    except Exception as e:
        return None, str(e)

# --- INTERFACE STREAMLIT ---
st.title("📑 Automação Vero RH")

tab1, tab2 = st.tabs(["Processar Folha", "Histórico"])

with tab1:
    upload = st.file_uploader("Suba a foto da folha", type=['jpg', 'jpeg', 'png'])
    
    if upload:
        dados, texto_bruto = processar_ocr(upload)
        
        if dados:
            st.info("💡 Revise os dados detectados antes de salvar:")
            with st.form("confirmar_dados"):
                col1, col2 = st.columns(2)
                nome = col1.text_input("Nome", value=dados['nome'])
                cpf = col2.text_input("CPF", value=dados['cpf'])
                pix = col1.text_input("Chave PIX", value=dados['pix'])
                dia = col2.text_input("Dia Detectado", value=dados['dia'])
                valor = st.number_input("Valor da Diária", value=150.0)

                if st.form_submit_button("Confirmar e Salvar"):
                    conn = sqlite3.connect('financeiro_diarias.db')
                    cursor = conn.cursor()
                    
                    # Salva ou atualiza prestador
                    cursor.execute("INSERT OR IGNORE INTO prestadores (nome, documento, chave_pix) VALUES (?,?,?)", (nome, cpf, pix))
                    cursor.execute("SELECT id FROM prestadores WHERE documento = ?", (cpf,))
                    p_id = cursor.fetchone()[0]
                    
                    # Salva diária
                    data_diaria = date(date.today().year, 1, int(dia) if dia.isdigit() else 1) # Jan conforme imagem
                    cursor.execute("INSERT INTO diarias (prestador_id, data_servico, valor) VALUES (?,?,?)", (p_id, data_diaria, valor))
                    
                    conn.commit()
                    conn.close()
                    st.success("✅ Registro salvo com sucesso!")
        else:
            st.error(f"Erro ao processar imagem: {texto_bruto}")

with tab2:
    conn = sqlite3.connect('financeiro_diarias.db')
    df = pd.read_sql_query("SELECT d.id, p.nome, d.data_servico, d.valor, d.status FROM diarias d JOIN prestadores p ON d.prestador_id = p.id", conn)
    conn.close()
    st.table(df)
