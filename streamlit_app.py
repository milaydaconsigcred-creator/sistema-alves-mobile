import streamlit as st
import requests
import json
import cv2
import numpy as np

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Alves Gestão", page_icon="🍱")

# Inicializa a memória para o código não sumir
if "codigo_estoque" not in st.session_state:
    st.session_state.codigo_estoque = ""

URL_BASE = "https://restaurante-alves-default-rtdb.firebaseio.com/"

st.title("ALVES GESTÃO 🍱")

# --- ÁREA DO SCANNER ---
st.subheader("📷 1. Escanear")
foto = st.camera_input("Tire foto do código de barras")

if foto:
    # Processa a foto na hora
    file_bytes = np.asarray(bytearray(foto.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    detector = cv2.barcode.BarcodeDetector()
    ok, info, _, _ = detector.detectAndDecode(img)
    
    if ok and info[0]:
        st.session_state.codigo_estoque = info[0]
        st.success(f"✅ Código: {info[0]}")
    else:
        st.warning("⚠️ Não leu. Tente focar melhor ou limpar a lente.")

st.divider()

# --- ÁREA DE DADOS ---
st.subheader("📦 2. Confirmar")

# O campo puxa o que foi lido, mas aceita digitação se a câmera falhar
cod_final = st.text_input("Código do Produto", value=st.session_state.codigo_estoque)

with st.form("estoque_form"):
    operacao = st.radio("Ação", ["Reposição", "Baixa", "Cadastrar"], horizontal=True)
    qtd = st.number_input("Quantidade", min_value=0.0, step=1.0)
    
    nome_item = ""
    if operacao == "Cadastrar":
        nome_item = st.text_input("Nome do Produto")
        
    enviar = st.form_submit_button("CONCLUIR")

if enviar:
    if not cod_final:
        st.error("Erro: Falta o código!")
    else:
        path = f"produtos/{cod_final}"
        if operacao == "Cadastrar":
            if nome_item:
                requests.patch(f"{URL_BASE}/{path}.json", data=json.dumps({"nome": nome_item, "estoque": qtd}))
                st.success("✅ Produto Cadastrado!")
            else: st.error("Falta o nome!")
        else:
            res = requests.get(f"{URL_BASE}/{path}.json").json()
            if res:
                atual = res.get('estoque', 0)
                novo = atual + qtd if operacao == "Reposição" else atual - qtd
                requests.patch(f"{URL_BASE}/{path}.json", data=json.dumps({"estoque": novo}))
                st.success(f"✅ Sucesso! Novo saldo: {novo}")
                st.session_state.codigo_estoque = "" # Limpa para o próximo
            else:
                st.error("❌ Produto não encontrado!")
