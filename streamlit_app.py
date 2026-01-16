import streamlit as st
import requests
import json
from datetime import datetime
from PIL import Image
import cv2
import numpy as np

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Alves Gestão Mobile", page_icon="🍱", layout="centered")

# --- CONFIGURAÇÃO DO FIREBASE ---
URL_BASE = "https://restaurante-alves-default-rtdb.firebaseio.com/"

# --- FUNÇÃO DE LEITURA (OPENCV) ---
def ler_codigo_da_foto(image_file):
    if image_file is not None:
        try:
            # Converte para OpenCV
            file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, 1)
            
            # Detector de código de barras
            detector = cv2.barcode.BarcodeDetector()
            ok, decoded_info, decoded_type, points = detector.detectAndDecode(img)
            
            if ok and decoded_info[0]:
                return decoded_info[0]
            
            # Tenta QR Code
            qr_detector = cv2.QRCodeDetector()
            ok_qr, val, _, _ = qr_detector.detectAndDecode(img)
            if ok_qr and val:
                return val
        except Exception as e:
            st.error(f"Erro no processamento: {e}")
    return ""

# --- BANCO DE DADOS ---
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
    [data-testid="stFileUploader"] { background-color: #ffffff; border: 2px dashed #1e3c72; border-radius: 10px; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- MENU ---
menu = st.sidebar.selectbox("Menu", ["Início", "📦 Estoque", "🥗 Nutricionista", "👨‍🍳 Cozinheiro", "🏷️ Etiquetas", "⚠️ Alertas", "📚 Histórico"])

if menu == "Início":
    st.title("ALVES GESTÃO 🍱")
    st.info("Sistema de Estoque Mobile")

elif menu == "📦 Estoque":
    aba = st.tabs(["Cadastrar", "Reposição", "Baixa"])
    
    for i, nome_aba in enumerate(["cad", "rep", "bx"]):
        with aba[i]:
            st.write(f"### 📷 Ler Código ({nome_aba.upper()})")
            
            # MUDANÇA CHAVE: file_uploader com captura de câmera direta
            foto = st.file_uploader("Clique para Abrir a Câmera", type=['jpg', 'png', 'jpeg'], key=f"cam_{nome_aba}")
            
            codigo_detectado = ""
            if foto:
                codigo_detectado = ler_codigo_da_foto(foto)
                if codigo_detectado:
                    st.success(f"✅ Identificado: {codigo_detectado}")
                else:
                    st.warning("⚠️ Não li as barras. Tente outra foto mais nítida.")

            cod = st.text_input("Código:", value=codigo_detectado, key=f"input_{nome_aba}")
            
            if nome_aba == "cad":
                n = st.text_input("Nome do Produto")
                est = st.number_input("Qtd Atual", min_value=0.0)
                if st.button("💾 SALVAR PRODUTO"):
                    if cod and n:
                        save_db(f"produtos/{cod}", {"nome": n, "estoque": est, "vencimento": str(datetime.now().date())})
                        st.success("Salvo!")

            elif nome_aba == "rep":
                qtd = st.number_input("Adicionar", min_value=0.0)
                if st.button("➕ Confirmar"):
                    p = get_db(f"produtos/{cod}")
                    if p:
                        save_db(f"produtos/{cod}", {"estoque": p.get('estoque', 0) + qtd})
                        st.success("Estoque Atualizado!")

            elif nome_aba == "bx":
                qtd = st.number_input("Retirar", min_value=0.0)
                if st.button("📉 Confirmar"):
                    p = get_db(f"produtos/{cod}")
                    if p and p['estoque'] >= qtd:
                        save_db(f"produtos/{cod}", {"estoque": p['estoque'] - qtd})
                        st.warning("Baixa realizada!")

# --- (Restante do código de Nutri, Cozinha e Alertas segue igual) ---
elif menu == "👨‍🍳 Cozinheiro":
    st.header("Cozinha")
    hoje = datetime.now().strftime("%Y%m%d")
    d = get_db(f"cardapios/{hoje}")
    if d:
        st.info(f"**CARDÁPIO:**\n{d['cardapio']}")
        st.success(f"**RETIRADA:**\n{d['ficha']}")
    else: st.warning("Sem cardápio hoje.")

elif menu == "⚠️ Alertas":
    st.header("Alertas")
    prods = get_db("produtos")
    if prods:
        for c, p in prods.items():
            if p['estoque'] <= p.get('minimo', 0):
                st.error(f"🚨 ESTOQUE BAIXO: {p['nome']} ({p['estoque']})")



