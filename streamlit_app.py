import streamlit as st
import requests
import json
from datetime import datetime
import cv2
import numpy as np

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Alves Gestão", page_icon="🍱", layout="centered")

# --- INICIALIZAÇÃO DA MEMÓRIA ---
# Criamos o estado do campo de texto se ele não existir
if "campo_codigo" not in st.session_state:
    st.session_state.campo_codigo = ""

# --- CONFIGURAÇÃO DO FIREBASE ---
URL_BASE = "https://restaurante-alves-default-rtdb.firebaseio.com/"

# --- FUNÇÃO DE LEITURA (OPENCV) ---
def processar_foto():
    if st.session_state.uploader_estoque is not None:
        try:
            # Lendo a imagem
            file_bytes = np.asarray(bytearray(st.session_state.uploader_estoque.read()), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, 1)
            
            # Detector de código de barras
            detector = cv2.barcode.BarcodeDetector()
            ok, decoded_info, _, _ = detector.detectAndDecode(img)
            
            codigo = ""
            if ok and decoded_info[0]:
                codigo = decoded_info[0]
            else:
                # Tenta QR Code caso falhe o de barras
                qr_detector = cv2.QRCodeDetector()
                ok_qr, val, _, _ = qr_detector.detectAndDecode(img)
                if ok_qr and val:
                    codigo = val
            
            if codigo:
                # O PULO DO GATO: Grava direto na chave do campo de texto
                st.session_state.campo_codigo = codigo
            else:
                st.warning("⚠️ Código não detectado. Tente focar melhor nas barras.")
                
        except Exception as e:
            st.error(f"Erro ao processar: {e}")

# --- FUNÇÕES BANCO DE DADOS ---
def get_db(path):
    try:
        res = requests.get(f"{URL_BASE}/{path}.json")
        return res.json() if res.status_code == 200 else {}
    except: return {}

def save_db(path, data):
    try: requests.patch(f"{URL_BASE}/{path}.json", data=json.dumps(data))
    except: st.error("Erro ao conectar.")

# --- INTERFACE ---
st.title("ALVES GESTÃO 🍱")

menu = st.sidebar.selectbox("Menu", ["📦 Estoque", "🥗 Nutricionista", "👨‍🍳 Cozinheiro", "⚠️ Alertas"])

if menu == "📦 Estoque":
    aba = st.radio("Operação:", ["Cadastrar", "Reposição", "Baixa"], horizontal=True)
    
    st.write(f"### 📷 Leitor para {aba}")
    
    # Botão de Câmera
    st.file_uploader(
        "Toque aqui para abrir a Câmera", 
        type=['jpg', 'png', 'jpeg'], 
        key="uploader_estoque", 
        on_change=processar_foto
    )
    
    # CAMPO DE TEXTO VINCULADO À MEMÓRIA
    # O valor 'value' não é mais necessário aqui pois a 'key' faz o trabalho
    cod = st.text_input("Número do Código de Barras:", key="campo_codigo")

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
                st.success(f"✅ Estoque atualizado para {nova_qtd}")
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
                st.error("❌ Saldo insuficiente ou produto inexistente.")

elif menu == "👨‍🍳 Cozinheiro":
    st.header("Cozinha")
    hoje = datetime.now().strftime("%Y%m%d")
    d = get_db(f"cardapios/{hoje}")
    if d:
        st.info(f"**CARDÁPIO:**\n{d['cardapio']}")
        st.success(f"**RETIRADA:**\n{d['ficha']}")
    else: st.warning("Aguardando cardápio de hoje.")

elif menu == "⚠️ Alertas":
    st.header("Alertas")
    prods = get_db("produtos")
    if prods:
        for c, p in prods.items():
            if p['estoque'] <= p.get('minimo', 0):
                st.error(f"🚨 ESTOQUE BAIXO: {p['nome']} (Saldo: {p['estoque']})")




