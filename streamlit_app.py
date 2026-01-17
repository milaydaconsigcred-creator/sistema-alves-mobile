import streamlit as st
import requests
import json
from datetime import datetime
import cv2
import numpy as np

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Alves Gestão", page_icon="🍱")

# Inicializa variáveis se não existirem
if "codigo_persistente" not in st.session_state:
    st.session_state.codigo_persistente = ""

URL_BASE = "https://restaurante-alves-default-rtdb.firebaseio.com/"

# --- 2. FUNÇÃO DE LEITURA ---
def ler_imagem(arquivo):
    try:
        file_bytes = np.asarray(bytearray(arquivo.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, 1)
        detector = cv2.barcode.BarcodeDetector()
        ok, info, _, _ = detector.detectAndDecode(img)
        if ok and info[0]: return info[0]
        
        qr = cv2.QRCodeDetector()
        ok_q, info_q, _, _ = qr.detectAndDecode(img)
        if ok_q: return info_q
    except: return None
    return None

# --- 3. INTERFACE ---
st.title("ALVES GESTÃO 🍱")

# ÁREA DE CAPTURA (Fora de formulários para evitar resets)
st.subheader("1º Passo: Capturar Código")
arquivo_foto = st.file_uploader("📷 Tirar Foto", type=['jpg', 'jpeg', 'png'])

if arquivo_foto is not None:
    if st.button("🔍 CLIQUE PARA PROCESSAR FOTO"):
        resultado = ler_imagem(arquivo_foto)
        if resultado:
            st.session_state.codigo_persistente = resultado
            st.success(f"✅ Código identificado: {resultado}")
        else:
            st.error("❌ Não foi possível ler. Tente outra foto.")

st.divider()

# ÁREA DE DADOS
st.subheader("2º Passo: Confirmar Dados")

# O campo de texto usa o valor que está na memória
cod_final = st.text_input("Código de Barras", value=st.session_state.codigo_persistente)

# Se o usuário mudar manualmente, atualiza a memória
if cod_final != st.session_state.codigo_persistente:
    st.session_state.codigo_persistente = cod_final

menu_estoque = st.radio("Operação", ["Cadastrar", "Reposição", "Baixa"], horizontal=True)
qtd = st.number_input("Quantidade", min_value=0.0)

if st.button("💾 CONFIRMAR NO BANCO DE DADOS"):
    if not cod_final:
        st.error("Erro: O código de barras está vazio!")
    else:
        path = f"produtos/{cod_final}"
        if menu_estoque == "Cadastrar":
            nome_p = st.text_input("Nome do Produto (Obrigatório)")
            if nome_p:
                requests.patch(f"{URL_BASE}/{path}.json", data=json.dumps({"nome": nome_p, "estoque": qtd}))
                st.success("Cadastrado!")
                st.session_state.codigo_persistente = ""
                st.rerun()
            else: st.warning("Digite o nome para cadastrar.")
        else:
            # Reposição ou Baixa
            res = requests.get(f"{URL_BASE}/{path}.json").json()
            if res:
                atual = res.get('estoque', 0)
                novo = atual + qtd if menu_estoque == "Reposição" else atual - qtd
                requests.patch(f"{URL_BASE}/{path}.json", data=json.dumps({"estoque": novo}))
                st.success(f"Sucesso! Novo saldo: {novo}")
                st.session_state.codigo_persistente = ""
                st.rerun()
            else:
                st.error("Produto não encontrado no sistema!")

# --- 4. ALERTAS ---
st.sidebar.divider()
if st.sidebar.button("Limpar Campos"):
    st.session_state.codigo_persistente = ""
    st.rerun()




