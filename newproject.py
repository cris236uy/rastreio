# app.py
# Máquina de Evolução Profissional (estilo "Person of Interest")
# Streamlit + Gemini (hábitos diários) + Desafios + Punições

import streamlit as st
import datetime as dt
import json
import os
from typing import List, Dict

# ==============================
# CONFIGURAÇÃO INICIAL
# ==============================
st.set_page_config(page_title="Máquina de Evolução", layout="wide")

st.title("🧠 Máquina de Evolução Profissional")
st.caption("Disciplina extrema. Progresso diário. Zero desculpas.")

# ==============================
# API GEMINI (CONFIGURADA)
# ==============================
from google import genai
from google.genai.types import GenerateContentConfig

with st.sidebar:
    st.header("🔑 Configuração da IA")
    gemini_key = st.text_input("Gemini API Key", type="password")

    if gemini_key:
        try:
            client = genai.Client(api_key=gemini_key)
            st.success("Gemini conectado com sucesso")
        except Exception as e:
            st.error("Erro ao conectar no Gemini")

# ==============================
# UTILIDADES
# ==============================
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

HABITS_FILE = os.path.join(DATA_DIR, "habits.json")
STATE_FILE = os.path.join(DATA_DIR, "state.json")


def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


state = load_json(STATE_FILE, {
    "level": 1,
    "xp": 0,
    "failures": 0,
    "last_day": str(dt.date.today())
})

habits = load_json(HABITS_FILE, [])

# ==============================
# GEMINI – GERADOR REAL DE HÁBITOS
# ==============================

def generate_habits_with_gemini(level: int) -> List[Dict]:
    prompt = f"""
Você é uma máquina implacável de evolução humana.
Crie 3 hábitos diários obrigatórios para hoje.

Perfil do usuário:
- Nível atual: {level}
- Objetivo: Evolução profissional e pessoal extrema
- Estilo: Disciplina militar, mentalidade empresarial, execução real

Regras:
- Hábitos claros, mensuráveis e desconfortáveis
- Misturar carreira, estudo, execução e corpo/mente
- Linguagem direta, sem motivação vazia

Responda SOMENTE em JSON no formato:
[
  {{"title": "", "description": ""}}
]
"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=GenerateContentConfig(
            temperature=0.4
        )
    )

    try:
        habits = json.loads(response.text)
        for i, h in enumerate(habits):
            h["id"] = i + 1
            h["done"] = False
        return habits
    except Exception:
        return []

# ==============================
# PUNIÇÕES (ANTI-FRACASSO)
# ==============================

def punishment(failures: int) -> str:
    punishments = [
        "50 flexões imediatamente",
        "1 hora extra de estudo profundo",
        "Relatório escrito de autocrítica",
        "Acordar 1h mais cedo amanhã",
        "Treino físico dobrado amanhã"
    ]
    return punishments[min(failures, len(punishments)-1)]

# ==============================
# RESET DIÁRIO
# ==============================

today = str(dt.date.today())
if state["last_day"] != today and gemini_key:
    habits = generate_habits_with_gemini(state["level"])
    save_json(HABITS_FILE, habits)
    state["last_day"] = today
    save_json(STATE_FILE, state)

# ==============================
# INTERFACE PRINCIPAL
# ==============================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Nível", state["level"])
with col2:
    st.metric("XP", state["xp"])
with col3:
    st.metric("Falhas", state["failures"])

st.divider()
st.subheader("📋 Hábitos do Dia")

completed = 0
for h in habits:
    checked = st.checkbox(f"**{h['title']}** – {h['description']}", value=h.get("done", False))
    h["done"] = checked
    if checked:
        completed += 1

save_json(HABITS_FILE, habits)

# ==============================
# AVALIAÇÃO DO DIA
# ==============================

if st.button("⚖️ Avaliar Dia"):
    if completed == len(habits) and len(habits) > 0:
        state["xp"] += 100
        if state["xp"] >= 500:
            state["level"] += 1
            state["xp"] = 0
        st.success("Execução perfeita. Você subiu de nível.")
    else:
        state["failures"] += 1
        p = punishment(state["failures"])
        st.error(f"Falha detectada. PUNIÇÃO: **{p}**")

    save_json(STATE_FILE, state)

# ==============================
# FILOSOFIA DA MÁQUINA
# ==============================

st.divider()
st.markdown(
    """
### 📜 Regra Final
- Consistência vence talento
- Dor agora, domínio depois
- A máquina observa tudo
"""
)
