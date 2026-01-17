import streamlit as st
import requests
import json
from datetime import datetime
import cv2
import numpy as np

# --- 1. CONFIGURAÇÃO LEVE ---
st.set_page_config(page_title="Alves Gestão", page_icon="🍱")

# --- 2. FUNÇÃO DE LEITURA ---
def ler_imagem(arquivo):
    try:
        file_bytes = np.asarray(bytearray(arquivo.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, 1)
        # Tenta Barcode
        bd = cv2.barcode.BarcodeDetector()
        ok, info, _, _ = bd.detectAndDecode(img)
        if ok and info[0]: return info[0]
        # Tenta QR
        qd = cv2.QRCodeDetector()
        ok_q, info_q, _, _ = qd.detectAndDecode(img)
        if ok_q: return info_q
    except: return None
    return None

# --- 3. LÓGICA DE PERSISTÊNCIA (JAVASCRIPT) ---
# Grava no navegador sempre que um código for lido
def salvar_no_navegador(codigo):
    st.components.v1.html(f"""
        <script>
            localStorage.setItem('alves_cod', '{codigo}');
        </script>
    """, height=0)

# --- 4. INTERFACE ---
st.title("ALVES GESTÃO 🍱")

# Inicializa o estado se não existir
if "codigo_input" not in st.session_state:
    st.session_state.codigo_input = ""

# SEÇÃO 1: SCANNER
st.subheader("1. Tirar Foto")
arquivo_foto = st.file_uploader("📷 Clique para abrir a câmera", type=['jpg', 'jpeg', 'png'])

if arquivo_foto:
    if st.button("🔍 PROCESSAR IMAGEM"):
        res = ler_imagem(arquivo_foto)
        if res:
            st.session_state.codigo_input = res
            salvar_no_navegador(res)
            st.success(f"Lido: {res}")
        else:
            st.error("Não foi possível ler. Tente outra foto.")

st.divider()

# SEÇÃO 2: RECUPERAÇÃO (Caso o app reinicie)
st.subheader("2. Recuperar se o App Reiniciou")
st.info("Se você tirou a foto e o app voltou ao início, clique abaixo para ver o código salvo.")

# Este botão usa um truque de HTML para mostrar o que está no localStorage do celular
if st.button("📋 VER ÚLTIMO CÓDIGO SALVO"):
    st.components.v1.html("""
        <div style="background-color: #ffeb3b; padding: 20px; border-radius: 10px; text-align: center;">
            <p style="font-family: sans-serif; margin: 0; color: black;">Último código lido:</p>
            <h1 id="display_cod" style="font-family: monospace; color: black; margin: 10px 0;">...</h1>
        </div>
        <script>
            const salvo = localStorage.getItem('alves_cod');
            document.getElementById('display_cod').innerText = salvo ? salvo : "Nenhum código encontrado";
        </script>
    """, height=150)

st.divider()

# SEÇÃO 3: FORMULÁRIO DE ENVIO
st.subheader("3. Finalizar Operação")
cod_final = st.text_input("Digite ou cole o Código aqui:", value=st.session_state.codigo_input)

aba = st.radio("Ação", ["Reposição", "Baixa", "Cadastrar"], horizontal=True)
qtd = st.number_input("Quantidade", min_value=0.0, step=1.0)

if st.button("💾 ENVIAR PARA O BANCO"):
    if not cod_final:
        st.error("Erro: Falta o código de barras!")
    else:
        URL_BASE = "https://restaurante-alves-default-rtdb.firebaseio.com/"
        path = f"produtos/{cod_final}"
        
        if aba == "Cadastrar":
            nome_p = st.text_input("Nome do Produto")
            if nome_p:
                requests.patch(f"{URL_BASE}/{path}.json", data=json.dumps({"nome": nome_p, "estoque": qtd}))
                st.success("Produto Cadastrado!")
            else: st.warning("Informe o nome do produto.")
        else:
            res_db = requests.get(f"{URL_BASE}/{path}.json").json()
            if res_db:
                atual = res_db.get('estoque', 0)
                novo = atual + qtd if aba == "Reposição" else atual - qtd
                requests.patch(f"{URL_BASE}/{path}.json", data=json.dumps({"estoque": novo}))
                st.success(f"Concluído! Novo estoque: {novo}")
                st.session_state.codigo_input = "" # Limpa para o próximo
            else:
                st.error("Produto não encontrado!")

