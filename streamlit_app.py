import streamlit as st
import requests
import json
from datetime import datetime
import cv2
import numpy as np

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Alves Gestão", page_icon="🍱")

# --- 2. MEMÓRIA RESISTENTE ---
if "codigo_lido" not in st.session_state:
    st.session_state.codigo_lido = ""

URL_BASE = "https://restaurante-alves-default-rtdb.firebaseio.com/"

# --- 3. FUNÇÃO DE LEITURA ---
def decodificar(image_file):
    try:
        file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, 1)
        # Tenta Barcode
        bd = cv2.barcode.BarcodeDetector()
        ok, info, _, _ = bd.detectAndDecode(img)
        if ok and info[0]: return info[0]
        # Tenta QR
        qd = cv2.QRCodeDetector()
        ok_q, info_q, _, _ = qd.detectAndDecode(img)
        if ok_q: return info_q
    except: pass
    return None

# --- 4. INTERFACE PRINCIPAL ---
st.title("ALVES GESTÃO 🍱")

# Processamento da foto ANTES de desenhar o restante da tela
foto = st.file_uploader("📷 ABRIR CÂMERA", type=['jpg', 'png', 'jpeg'], key="main_cam")
if foto:
    res = decodificar(foto)
    if res:
        st.session_state.codigo_lido = res
        st.success(f"✅ Código: {res}")
    else:
        st.error("❌ Não foi possível ler. Tente outra foto.")

# --- 5. MENU ---
menu = st.sidebar.selectbox("Menu", ["📦 Estoque", "👨‍🍳 Cozinheiro", "⚠️ Alertas"])

if menu == "📦 Estoque":
    # Usamos um formulário para evitar que a página reinicie sozinha
    with st.form("form_estoque", clear_on_submit=False):
        aba = st.radio("Ação", ["Cadastrar", "Reposição", "Baixa"], horizontal=True)
        
        # O campo de texto SEMPRE olha para a memória
        cod_input = st.text_input("Número do Código de Barras", value=st.session_state.codigo_lido)
        nome_item = st.text_input("Nome do Item")
        qtd = st.number_input("Quantidade", min_value=0.0)
        
        btn_confirmar = st.form_submit_button("🚀 CONFIRMAR OPERAÇÃO")

    if btn_confirmar:
        if not cod_input:
            st.error("Insira ou leia um código!")
        else:
            # Lógica de Banco de Dados
            path = f"produtos/{cod_input}"
            if aba == "Cadastrar":
                requests.patch(f"{URL_BASE}/{path}.json", data=json.dumps({"nome": nome_item, "estoque": qtd}))
                st.success("Cadastrado!")
            else:
                res_db = requests.get(f"{URL_BASE}/{path}.json").json()
                if res_db:
                    estoque_atual = res_db.get('estoque', 0)
                    novo_estoque = estoque_atual + qtd if aba == "Reposição" else estoque_atual - qtd
                    requests.patch(f"{URL_BASE}/{path}.json", data=json.dumps({"estoque": novo_estoque}))
                    st.success(f"Sucesso! Novo saldo: {novo_estoque}")
                else:
                    st.error("Produto não encontrado!")
            
            # Limpa a memória após o envio
            st.session_state.codigo_lido = ""

elif menu == "👨‍🍳 Cozinheiro":
    hoje = datetime.now().strftime("%Y%m%d")
    d = requests.get(f"{URL_BASE}/cardapios/{hoje}.json").json()
    if d:
        st.info(f"**CARDÁPIO:** {d['cardapio']}")
        st.success(f"**RETIRADA:** {d['ficha']}")
    else: st.warning("Sem cardápio hoje.")




