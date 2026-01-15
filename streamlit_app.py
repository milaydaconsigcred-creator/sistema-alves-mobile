import streamlit as st
import requests
import json
from datetime import datetime
from PIL import Image
import cv2
import numpy as np

# --- CONFIGURAÇÃO DO FIREBASE ---
URL_BASE = "https://restaurante-alves-default-rtdb.firebaseio.com/"

st.set_page_config(page_title="Alves Gestão Mobile", page_icon="🍱", layout="centered")

# --- FUNÇÃO DE LEITURA COM OPENCV (MAIS ESTÁVEL) ---
def ler_codigo_da_foto(image_file):
    if image_file is not None:
        # Converter imagem para formato OpenCV
        file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, 1)
        
        # Detector de código de barras
        detector = cv2.barcode.BarcodeDetector()
        ok, decoded_info, decoded_type, points = detector.detectAndDecode(img)
        
        if ok and decoded_info:
            return decoded_info[0]
        
        # Tentar detector de QR Code (caso seja um código quadrado)
        qr_detector = cv2.QRCodeDetector()
        ok_qr, decoded_info_qr, points_qr, straight_qrcode = qr_detector.detectAndDecode(img)
        if ok_qr:
            return decoded_info_qr

        st.error("❌ Código não detectado. Tente uma foto mais próxima, reta e bem iluminada.")
    return ""

# --- ESTILIZAÇÃO ---
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    .stButton>button { width: 100%; border-radius: 12px; height: 50px; font-weight: bold; background-color: #1e3c72; color: white; }
    @media print {
        header, .stSidebar, .stTabs, button { display: none !important; }
        .etiqueta-print { display: block !important; border: 2px solid black; padding: 20px; color: black !important; }
    }
    </style>
    """, unsafe_allow_html=True)

def get_db(path):
    try:
        res = requests.get(f"{URL_BASE}/{path}.json")
        return res.json() if res.status_code == 200 else {}
    except: return {}

def save_db(path, data):
    try: requests.patch(f"{URL_BASE}/{path}.json", data=json.dumps(data))
    except: st.error("Erro no banco.")

# --- MENU ---
menu = st.sidebar.selectbox("Menu", ["Início", "📦 Estoque", "🥗 Nutricionista", "👨‍🍳 Cozinheiro", "🏷️ Etiquetas", "⚠️ Alertas", "📚 Histórico"])

if menu == "Início":
    st.title("ALVES GESTÃO 🍱")
    st.info("Sistema de Estoque com Leitura de Foto")

elif menu == "📦 Estoque":
    aba = st.tabs(["Cadastrar", "Reposição", "Baixa"])
    
    for i, nome_aba in enumerate(["cad", "rep", "bx"]):
        with aba[i]:
            st.subheader(f"📷 Scanner ({nome_aba.upper()})")
            foto = st.camera_input("Tire foto do código", key=f"cam_{nome_aba}")
            
            codigo_detectado = ""
            if foto:
                codigo_detectado = ler_codigo_da_foto(foto)
                if codigo_detectado:
                    st.success(f"✅ Lido: {codigo_detectado}")

            cod = st.text_input("Código:", value=codigo_detectado, key=f"input_{nome_aba}")
            
            if nome_aba == "cad":
                n = st.text_input("Nome do Produto")
                est = st.number_input("Estoque Inicial", min_value=0.0)
                min_est = st.number_input("Estoque Mínimo", min_value=0.0)
                v = st.date_input("Validade")
                if st.button("💾 SALVAR"):
                    save_db(f"produtos/{cod}", {"nome": n, "estoque": est, "minimo": min_est, "vencimento": str(v)})
                    st.success("Salvo!")
            
            elif nome_aba == "rep":
                qtd = st.number_input("Qtd Adicionar", min_value=0.0)
                if st.button("➕ Confirmar Entrada"):
                    p = get_db(f"produtos/{cod}")
                    if p:
                        save_db(f"produtos/{cod}", {"estoque": p.get('estoque', 0) + qtd})
                        st.success("Estoque Atualizado!")
            
            elif nome_aba == "bx":
                qtd = st.number_input("Qtd Retirar", min_value=0.0)
                if st.button("📉 Confirmar Saída"):
                    p = get_db(f"produtos/{cod}")
                    if p and p['estoque'] >= qtd:
                        save_db(f"produtos/{cod}", {"estoque": p['estoque'] - qtd})
                        st.warning("Baixa realizada!")

elif menu == "🥗 Nutricionista":
    senha = st.text_input("Senha", type="password")
    if senha == "alvesnutri":
        data_c = st.date_input("Data")
        txt_c = st.text_area("Cardápio")
        txt_f = st.text_area("Ficha de Retirada")
        if st.button("🚀 PUBLICAR"):
            save_db(f"cardapios/{data_c.strftime('%Y%m%d')}", {"cardapio": txt_c, "ficha": txt_f})
            st.success("Enviado!")

elif menu == "👨‍🍳 Cozinheiro":
    st.header("Cozinha")
    hoje = datetime.now().strftime("%Y%m%d")
    d = get_db(f"cardapios/{hoje}")
    if d:
        st.info(f"**CARDÁPIO:**\n{d['cardapio']}")
        st.success(f"**RETIRADA:**\n{d['ficha']}")
    else: st.warning("A tela foi limpa. Sem cardápio para hoje.")

elif menu == "📚 Histórico":
    st.header("Histórico")
    todos = get_db("cardapios")
    if todos:
        datas = sorted(todos.keys(), reverse=True)
        sel = st.selectbox("Data", datas)
        st.write(f"**Cardápio:** {todos[sel]['cardapio']}")
        st.write(f"**Ficha:** {todos[sel]['ficha']}")

elif menu == "⚠️ Alertas":
    st.header("Alertas")
    prods = get_db("produtos")
    if prods:
        for c, p in prods.items():
            if p['estoque'] <= p.get('minimo', 0):
                st.error(f"🚨 ESTOQUE BAIXO: {p['nome']} ({p['estoque']})")
            try:
                v_dt = datetime.strptime(p['vencimento'], '%Y-%m-%d')
                dias = (v_dt - datetime.now()).days
                if 0 <= dias <= 7: st.warning(f"⌛ VENCENDO: {p['nome']} em {dias} dias")
            except: pass

