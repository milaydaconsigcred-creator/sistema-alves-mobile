import streamlit as st
import requests
import json
from datetime import datetime
from PIL import Image
import cv2
import numpy as np

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Alves Gestão Mobile", page_icon="🍱", layout="centered")

# --- INICIALIZAÇÃO DA MEMÓRIA (SESSION STATE) ---
if 'codigo_lido' not in st.session_state:
    st.session_state.codigo_lido = ""

# --- CONFIGURAÇÃO DO FIREBASE ---
URL_BASE = "https://restaurante-alves-default-rtdb.firebaseio.com/"

# --- FUNÇÃO DE LEITURA (OPENCV) ---
def ler_codigo_da_foto(image_file):
    if image_file is not None:
        try:
            file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, 1)
            detector = cv2.barcode.BarcodeDetector()
            ok, decoded_info, _, _ = detector.detectAndDecode(img)
            if ok and decoded_info[0]:
                return decoded_info[0]
            
            qr_detector = cv2.QRCodeDetector()
            ok_qr, val, _, _ = qr_detector.detectAndDecode(img)
            if ok_qr and val:
                return val
        except Exception as e:
            st.error(f"Erro no processamento: {e}")
    return None

# --- FUNÇÕES DB ---
def get_db(path):
    try:
        res = requests.get(f"{URL_BASE}/{path}.json")
        return res.json() if res.status_code == 200 else {}
    except: return {}

def save_db(path, data):
    try: requests.patch(f"{URL_BASE}/{path}.json", data=json.dumps(data))
    except: st.error("Erro de conexão.")

# --- ESTILO ---
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    .stButton>button { width: 100%; border-radius: 12px; height: 55px; background-color: #1e3c72; color: white; }
    div[data-testid="stFileUploader"] { background-color: white; border: 2px dashed #1e3c72; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- MENU ---
menu = st.sidebar.selectbox("Menu", ["📦 Estoque", "🥗 Nutricionista", "👨‍🍳 Cozinheiro", "⚠️ Alertas", "📚 Histórico"])

if menu == "📦 Estoque":
    # Definimos qual aba ficará aberta usando o Session State
    aba_selecionada = st.radio("Ação:", ["Cadastrar", "Reposição", "Baixa"], horizontal=True)
    
    st.divider()
    st.write(f"### 📷 Scanner para {aba_selecionada}")
    
    # Uploader que abre a câmera
    foto = st.file_uploader("Toque para tirar foto do código", type=['jpg', 'png', 'jpeg'], key="uploader_estoque")
    
    if foto:
        resultado = ler_codigo_da_foto(foto)
        if resultado:
            st.session_state.codigo_lido = resultado
            st.success(f"✅ Código capturado: {resultado}")
        else:
            st.warning("⚠️ Não foi possível ler. Tente focar melhor.")

    # O campo de texto agora "escuta" o que está na memória
    cod = st.text_input("Número do Código:", value=st.session_state.codigo_lido)
    
    if aba_selecionada == "Cadastrar":
        n = st.text_input("Nome do Produto")
        est = st.number_input("Qtd Inicial", min_value=0.0)
        if st.button("💾 SALVAR NOVO"):
            if cod and n:
                save_db(f"produtos/{cod}", {"nome": n, "estoque": est, "vencimento": str(datetime.now().date())})
                st.success("Produto salvo!")
                st.session_state.codigo_lido = "" # Limpa a memória após salvar

    elif aba_selecionada == "Reposição":
        qtd = st.number_input("Adicionar quantidade", min_value=0.0)
        if st.button("➕ CONFIRMAR ENTRADA"):
            p = get_db(f"produtos/{cod}")
            if p:
                save_db(f"produtos/{cod}", {"estoque": p.get('estoque', 0) + qtd})
                st.success("Estoque atualizado!")
                st.session_state.codigo_lido = ""

    elif aba_selecionada == "Baixa":
        qtd = st.number_input("Retirar quantidade", min_value=0.0)
        if st.button("📉 CONFIRMAR SAÍDA"):
            p = get_db(f"produtos/{cod}")
            if p and p['estoque'] >= qtd:
                save_db(f"produtos/{cod}", {"estoque": p['estoque'] - qtd})
                st.warning("Baixa realizada!")
                st.session_state.codigo_lido = ""

elif menu == "👨‍🍳 Cozinheiro":
    st.header("Cozinha")
    hoje = datetime.now().strftime("%Y%m%d")
    d = get_db(f"cardapios/{hoje}")
    if d:
        st.info(f"**CARDÁPIO:**\n{d['cardapio']}")
        st.success(f"**LISTA DE RETIRADA:**\n{d['ficha']}")
    else: st.warning("Sem cardápio para hoje.")

elif menu == "⚠️ Alertas":
    st.header("Alertas")
    prods = get_db("produtos")
    if prods:
        for c, p in prods.items():
            if p['estoque'] <= p.get('minimo', 0):
                st.error(f"🚨 ESTOQUE BAIXO: {p['nome']} ({p['estoque']})")




