import streamlit as st
import requests
import json
from streamlit_quagga2 import st_quagga2

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Alves Gestão", page_icon="🍱")

URL_BASE = "https://restaurante-alves-default-rtdb.firebaseio.com/"

st.title("ALVES GESTÃO 🍱")

# --- CSS PARA DEIXAR O SCANNER BONITO NO CELULAR ---
st.markdown("""
    <style>
    #video-container video { width: 100%; border-radius: 15px; border: 3px solid #1e3c72; }
    .stButton>button { width: 100%; height: 60px; border-radius: 15px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. SCANNER AO VIVO (Não sai do App) ---
st.subheader("📷 Escanear Código")
st.info("Aponte a câmera para o código de barras. Ele lerá automaticamente.")

# Este componente abre a câmera DENTRO do site
# Ele tenta evitar o bloqueio de permissão sendo um componente direto
barcode = st_quagga2(key='scanner')

if barcode:
    st.success(f"✅ Lido: {barcode}")
    st.session_state.cod_final = barcode

# --- 2. FORMULÁRIO DE ESTOQUE ---
st.divider()

if "cod_final" not in st.session_state:
    st.session_state.cod_final = ""

# O funcionário pode ajustar manualmente se o scanner falhar
cod_input = st.text_input("Código do Produto:", value=st.session_state.cod_final)

with st.form("alves_form"):
    aba = st.radio("Operação", ["Reposição", "Baixa", "Cadastrar"], horizontal=True)
    qtd = st.number_input("Quantidade", min_value=0.0, step=1.0)
    
    nome_p = ""
    if aba == "Cadastrar":
        nome_p = st.text_input("Nome do Novo Produto")
        
    confirmar = st.form_submit_button("CONCLUIR")

if confirmar:
    if not cod_input:
        st.error("Erro: Sem código!")
    else:
        path = f"produtos/{cod_input}"
        if aba == "Cadastrar":
            if nome_p:
                requests.patch(f"{URL_BASE}/{path}.json", data=json.dumps({"nome": nome_p, "estoque": qtd}))
                st.success("✅ Cadastrado!")
            else: st.warning("Digite o nome!")
        else:
            res = requests.get(f"{URL_BASE}/{path}.json").json()
            if res:
                atual = res.get('estoque', 0)
                novo = atual + qtd if aba == "Reposição" else atual - qtd
                requests.patch(f"{URL_BASE}/{path}.json", data=json.dumps({"estoque": novo}))
                st.success(f"✅ Sucesso! Novo saldo: {novo}")
            else:
                st.error("❌ Produto não encontrado!")

