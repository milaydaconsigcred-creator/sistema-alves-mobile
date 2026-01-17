import streamlit as st
import requests
import json
from PIL import Image, ImageOps, ImageEnhance
import pytesseract
from pyzbar.pyzbar import decode
import re

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Alves Gestão", page_icon="🍱")

if "codigo_estoque" not in st.session_state:
    st.session_state.codigo_estoque = ""

URL_BASE = "https://restaurante-alves-default-rtdb.firebaseio.com/"

st.title("ALVES GESTÃO 🍱")

# --- ÁREA DA CÂMARA ---
st.subheader("📷 1. Escanear")
foto = st.camera_input("Foque no código ou nos números")

if foto:
    try:
        img_original = Image.open(foto)
        
        # Tentativa 1: Código de Barras (Original)
        barras = decode(img_original)
        
        # Tentativa 2: Se falhar, tenta com Contraste para Números
        if not barras:
            img_proc = ImageOps.grayscale(img_original)
            img_proc = ImageEnhance.Contrast(img_proc).enhance(2.5)
            
            # Tenta Barras de novo na imagem tratada
            barras = decode(img_proc)
            
            if barras:
                codigo = barras[0].data.decode('utf-8')
                st.session_state.codigo_estoque = codigo
            else:
                # Tenta OCR (Números) como última esperança
                config_ocr = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789'
                texto = pytesseract.image_to_string(img_proc, config=config_ocr)
                numeros = re.sub(r'\D', '', texto)
                if len(numeros) >= 5:
                    st.session_state.codigo_estoque = numeros
                else:
                    st.warning("⚠️ Leitura automática falhou. Por favor, digite o número abaixo.")
        else:
            codigo = barras[0].data.decode('utf-8')
            st.session_state.codigo_estoque = codigo
            st.success("✅ Código lido!")

    except Exception as e:
        st.error("Erro ao processar imagem.")

st.divider()

# --- ÁREA DE ENTRADA MANUAL (Otimizada) ---
st.subheader("📦 2. Confirmar Dados")

# "type='number'" não existe no text_input do streamlit, 
# mas o valor inicial sendo o que foi lido ajuda.
cod_final = st.text_input("Número do Produto (Digite se necessário):", 
                         value=st.session_state.codigo_estoque,
                         help="Insira os números abaixo do código de barras")

with st.form("estoque_form", clear_on_submit=True):
    op = st.radio("Operação", ["Reposição", "Baixa", "Cadastrar"], horizontal=True)
    qtd = st.number_input("Quantidade", min_value=0.0, step=1.0, format="%.0f")
    
    nome_item = ""
    if op == "Cadastrar":
        nome_item = st.text_input("Nome do Produto Novo")
        
    submetido = st.form_submit_button("CONCLUIR E SALVAR")

if submetido:
    if not cod_final:
        st.error("Introduza o código do produto.")
    else:
        path = f"produtos/{cod_final}"
        if op == "Cadastrar":
            if nome_item:
                requests.patch(f"{URL_BASE}/{path}.json", data=json.dumps({"nome": nome_item, "estoque": qtd}))
                st.success(f"✅ {nome_item} cadastrado!")
            else: st.error("Falta o nome do produto!")
        else:
            res = requests.get(f"{URL_BASE}/{path}.json").json()
            if res:
                atual = res.get('estoque', 0)
                novo = atual + qtd if op == "Reposição" else atual - qtd
                requests.patch(f"{URL_BASE}/{path}.json", data=json.dumps({"estoque": novo}))
                st.success(f"✅ Atualizado! Novo total: {novo}")
            else:
                st.error("❌ Produto não encontrado!")
        
        # Limpa para a próxima leitura
        st.session_state.codigo_estoque = ""

# Botão para limpar caso queiram começar de novo
if st.button("Limpar e Novo Scanner"):
    st.session_state.codigo_estoque = ""
    st.rerun()


