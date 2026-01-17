import streamlit as st
import requests
import json
from datetime import datetime
import cv2
import numpy as np

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Alves Gestão", page_icon="🍱", layout="centered")

# --- INICIALIZAÇÃO DA MEMÓRIA ---
if "codigo_detectado" not in st.session_state:
    st.session_state.codigo_detectado = ""
if "campo_codigo" not in st.session_state:
    st.session_state.campo_codigo = ""

# --- CONFIGURAÇÃO DO FIREBASE ---
URL_BASE = "https://restaurante-alves-default-rtdb.firebaseio.com/"

# --- FUNÇÃO DE LEITURA (OPENCV) ---
def ler_codigo_da_foto(image_file):
    try:
        file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, 1)
        
        # Tentativa 1: Código de Barras
        detector = cv2.barcode.BarcodeDetector()
        ok, decoded_info, _, _ = detector.detectAndDecode(img)
        if ok and decoded_info[0]:
            return decoded_info[0]
        
        # Tentativa 2: QR Code
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

# --- INTERFACE ---
st.title("ALVES GESTÃO 🍱")

menu = st.sidebar.selectbox("Menu", ["📦 Estoque", "🥗 Nutricionista", "👨‍🍳 Cozinheiro", "⚠️ Alertas"])

if menu == "📦 Estoque":
    aba = st.radio("Operação:", ["Cadastrar", "Reposição", "Baixa"], horizontal=True)
    st.write(f"### 📷 Leitor para {aba}")
    
    # 1. Botão de Câmera
    foto = st.file_uploader("Toque aqui para tirar foto", type=['jpg', 'png', 'jpeg'], key="uploader")
    
    if foto:
        with st.spinner("Buscando código na imagem..."):
            res = ler_codigo_da_foto(foto)
            if res:
                st.session_state.codigo_detectado = res
                st.session_state.campo_codigo = res # Força a entrada no campo
                st.success(f"✅ Código encontrado: {res}")
            else:
                st.error("❌ Código não lido. Tente novamente com mais luz.")

    # 2. Campo de Texto (VINCULADO AO SESSION STATE)
    # Usamos o 'value' apontando para a memória
    cod = st.text_input("Número do Código de Barras:", value=st.session_state.campo_codigo)
    
    # Sincroniza se o usuário digitar manualmente
    st.session_state.campo_codigo = cod

    st.divider()

    if aba == "Cadastrar":
        n = st.text_input("Nome do Produto")
        est = st.number_input("Estoque Inicial", min_value=0.0)
        if st.button("💾 SALVAR PRODUTO"):
            if cod and n:
                save_db(f"produtos/{cod}", {"nome": n, "estoque": est, "vencimento": str(datetime.now().date())})
                st.success("✅ Salvo com sucesso!")
                st.session_state.campo_codigo = "" # Limpa para o próximo
                st.rerun()

    elif aba == "Reposição":
        qtd = st.number_input("Quantidade a Adicionar", min_value=0.0)
        if st.button("➕ CONFIRMAR ENTRADA"):
            p = get_db(f"produtos/{cod}")
            if p:
                nova_qtd = p.get('estoque', 0) + qtd
                save_db(f"produtos/{cod}", {"estoque": nova_qtd})
                st.success(f"✅ Atualizado para {nova_qtd}")
                st.session_state.campo_codigo = ""
                st.rerun()
            else:
                st.error("❌ Produto não encontrado.")

    elif aba == "Baixa":
        qtd = st.number_input("Quantidade a Retirar", min_value=0.0)
        if st.button("📉 CONFIRMAR SAÍDA"):
            p = get_db(f"produtos/{cod}")
            if p and p['estoque'] >= qtd:
                nova_qtd = p['estoque'] - qtd
                save_db(f"produtos/{cod}", {"estoque": nova_qtd})
                st.warning(f"✅ Baixa realizada! Novo estoque: {nova_qtd}")
                st.session_state.campo_codigo = ""
                st.rerun()
            else:
                st.error("❌ Saldo insuficiente.")

# --- RESTANTE DO CÓDIGO (NUTRI, COZINHA) SEGUE O MESMO PADRÃO ---
elif menu == "👨‍🍳 Cozinheiro":
    st.header("Cozinha")
    hoje = datetime.now().strftime("%Y%m%d")
    d = get_db(f"cardapios/{hoje}")
    if d:
        st.info(f"**CARDÁPIO:**\n{d['cardapio']}")
        st.success(f"**RETIRADA:**\n{d['ficha']}")




