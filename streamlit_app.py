import streamlit as st
import requests
import json
from datetime import datetime
import cv2
import numpy as np

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Alves Gestão", page_icon="🍱")

# --- 2. FUNÇÃO PARA SALVAR NA MEMÓRIA DO NAVEGADOR (JS) ---
def salvar_no_navegador(codigo):
    js = f"""
    <script>
        localStorage.setItem('ultimo_codigo', '{codigo}');
        console.log('Código salvo no LocalStorage');
    </script>
    """
    st.components.v1.html(js, height=0)

# --- 3. FUNÇÃO DE LEITURA ---
def ler_imagem(arquivo):
    try:
        file_bytes = np.asarray(bytearray(arquivo.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, 1)
        bd = cv2.barcode.BarcodeDetector()
        ok, info, _, _ = bd.detectAndDecode(img)
        if ok and info[0]: return info[0]
        qd = cv2.QRCodeDetector()
        ok_q, info_q, _, _ = qd.detectAndDecode(img)
        if ok_q: return info_q
    except: return None
    return None

# --- 4. INTERFACE ---
st.title("ALVES GESTÃO 🍱")

# Seção de Captura
st.subheader("1. Capturar")
arquivo_foto = st.file_uploader("📷 Tirar Foto", type=['jpg', 'jpeg', 'png'], key="uploader_final")

if arquivo_foto:
    if st.button("🔍 PROCESSAR FOTO"):
        res = ler_imagem(arquivo_foto)
        if res:
            st.session_state.codigo_lido = res
            salvar_no_navegador(res) # SALVA NA MEMÓRIA FÍSICA DO CELULAR
            st.success(f"✅ Lido com sucesso: {res}")
        else:
            st.error("❌ Não foi possível ler. Tente outra foto.")

# BOTÃO DE SEGURANÇA (Caso o app reinicie)
st.markdown("""
    <script>
    function recuperar() {
        const cod = localStorage.getItem('ultimo_codigo');
        if(cod) {
            window.parent.postMessage({type: 'streamlit:setComponentValue', value: cod}, '*');
            alert("Código recuperado: " + cod);
        } else {
            alert("Nenhum código na memória.");
        }
    }
    </script>
    """, unsafe_allow_html=True)

st.divider()

# Seção de Dados
st.subheader("2. Confirmar Dados")

# Recuperação manual se o app reiniciou
if st.button("🔄 RECUPERAR CÓDIGO (Se o app reiniciou)"):
    st.info("O último código lido foi salvo na memória do seu celular. Verifique o campo abaixo.")

cod_final = st.text_input("Código de Barras", value=st.session_state.get('codigo_lido', ""))

aba = st.radio("Operação", ["Cadastrar", "Reposição", "Baixa"], horizontal=True)
qtd = st.number_input("Quantidade", min_value=0.0)

if st.button("💾 CONFIRMAR NO BANCO"):
    if not cod_final:
        st.error("O código está vazio!")
    else:
        URL_BASE = "https://restaurante-alves-default-rtdb.firebaseio.com/"
        path = f"produtos/{cod_final}"
        
        if aba == "Cadastrar":
            nome_p = st.text_input("Nome do Produto")
            if nome_p:
                requests.patch(f"{URL_BASE}/{path}.json", data=json.dumps({"nome": nome_p, "estoque": qtd}))
                st.success("Salvo!")
        else:
            res_db = requests.get(f"{URL_BASE}/{path}.json").json()
            if res_db:
                atual = res_db.get('estoque', 0)
                novo = atual + qtd if aba == "Reposição" else atual - qtd
                requests.patch(f"{URL_BASE}/{path}.json", data=json.dumps({"estoque": novo}))
                st.success(f"Atualizado! Novo saldo: {novo}")
            else:
                st.error("Produto não cadastrado!")
