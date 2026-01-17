import streamlit as st
import requests
import json
from datetime import datetime
import cv2
import numpy as np

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Alves Gestão", page_icon="🍱")

URL_BASE = "https://restaurante-alves-default-rtdb.firebaseio.com/"

# --- 1. RECUPERAR CÓDIGO DA URL (Caso o app reinicie) ---
# Se o app reiniciar, ele olha para o link e puxa o código de lá
query_params = st.query_params
codigo_na_url = query_params.get("cod", "")

# --- 2. FUNÇÃO DE LEITURA ---
def ler_imagem(arquivo):
    try:
        file_bytes = np.asarray(bytearray(arquivo.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, 1)
        detector = cv2.barcode.BarcodeDetector()
        ok, info, _, _ = detector.detectAndDecode(img)
        if ok and info[0]: return info[0]
        
        qd = cv2.QRCodeDetector()
        ok_q, info_q, _, _ = qd.detectAndDecode(img)
        if ok_q: return info_q
    except: return None
    return None

st.title("ALVES GESTÃO 🍱")

# --- 3. ÁREA DE CAPTURA ---
st.subheader("📷 Passo 1: Tirar Foto")
foto = st.file_uploader("Toque para abrir a câmera", type=['jpg', 'jpeg', 'png'], key="uploader")

if foto:
    if st.button("🔍 PROCESSAR E SALVAR"):
        resultado = ler_imagem(foto)
        if resultado:
            # O SEGREDO: Salva o código nos parâmetros da URL e recarrega
            st.query_params["cod"] = resultado
            st.success(f"Código detectado: {resultado}")
            st.rerun()
        else:
            st.error("Não foi possível ler as barras. Tente novamente.")

st.divider()

# --- 4. FORMULÁRIO DE ESTOQUE ---
st.subheader("📦 Passo 2: Finalizar")

# O campo de texto agora puxa automaticamente o que está na URL
cod_final = st.text_input("Código do Produto", value=codigo_na_url)

with st.form("estoque_form"):
    aba = st.radio("Operação", ["Reposição", "Baixa", "Cadastrar"], horizontal=True)
    
    nome_p = ""
    if aba == "Cadastrar":
        nome_p = st.text_input("Nome do Produto")
        
    qtd = st.number_input("Quantidade", min_value=0.0, step=1.0)
    
    confirmar = st.form_submit_button("GRAVAR NO SISTEMA")

if confirmar:
    if not cod_final:
        st.error("Erro: Sem código de barras!")
    else:
        path = f"produtos/{cod_final}"
        if aba == "Cadastrar":
            if nome_p:
                requests.patch(f"{URL_BASE}/{path}.json", data=json.dumps({"nome": nome_p, "estoque": qtd}))
                st.success("Cadastrado!")
            else: st.warning("Informe o nome.")
        else:
            res = requests.get(f"{URL_BASE}/{path}.json").json()
            if res:
                novo = res.get('estoque', 0) + qtd if aba == "Reposição" else res.get('estoque', 0) - qtd
                requests.patch(f"{URL_BASE}/{path}.json", data=json.dumps({"estoque": novo}))
                st.success(f"Sucesso! Novo saldo: {novo}")
                # Limpa a URL para o próximo produto
                st.query_params.clear()
            else:
                st.error("Produto não encontrado!")
