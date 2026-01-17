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

# --- ÁREA DO SCANNER ---
st.subheader("📷 1. Escanear ou Fotografar Números")
foto = st.camera_input("Tire foto do código ou dos números")

if foto:
    try:
        img = Image.open(foto)
        
        # --- TRATAMENTO PARA OCR ---
        img_gray = ImageOps.grayscale(img)
        img_gray = ImageEnhance.Contrast(img_gray).enhance(2.5)
        
        # 1. Tenta ler Código de Barras primeiro (é mais preciso)
        barras = decode(img)
        
        if barras:
            codigo = barras[0].data.decode('utf-8')
            st.session_state.codigo_estoque = codigo
            st.success(f"✅ Barras lidas: {codigo}")
        else:
            # 2. Se falhar, tenta ler os NÚMEROS (OCR)
            texto = pytesseract.image_to_string(img_gray, config='--psm 6 digits')
            # Limpa o texto para deixar apenas números
            numeros = re.sub(r'\D', '', texto)
            
            if len(numeros) >= 5: # Filtro para evitar ler "sujeira"
                st.session_state.codigo_estoque = numeros
                st.success(f"✅ Números detectados: {numeros}")
            else:
                st.warning("⚠️ Não consegui ler as barras nem os números. Tente focar apenas nos números do produto.")
                
    except Exception as e:
        st.error("Erro ao processar a imagem.")

st.divider()

# --- ÁREA DE DADOS ---
st.subheader("📦 2. Confirmar Dados")
cod_final = st.text_input("Código do Produto", value=st.session_state.codigo_estoque)

with st.form("estoque_form"):
    operacao = st.radio("Ação", ["Reposição", "Baixa", "Cadastrar"], horizontal=True)
    qtd = st.number_input("Quantidade", min_value=0.0, step=1.0)
    
    nome_item = ""
    if operacao == "Cadastrar":
        nome_item = st.text_input("Nome do Novo Produto")
        
    enviar = st.form_submit_button("CONCLUIR OPERAÇÃO")

if enviar:
    if not cod_final:
        st.error("Erro: Sem código!")
    else:
        path = f"produtos/{cod_final}"
        if operacao == "Cadastrar":
            if nome_item:
                requests.patch(f"{URL_BASE}/{path}.json", data=json.dumps({"nome": nome_item, "estoque": qtd}))
                st.success("✅ Cadastrado com sucesso!")
            else: st.error("Falta o nome!")
        else:
            res = requests.get(f"{URL_BASE}/{path}.json").json()
            if res:
                atual = res.get('estoque', 0)
                novo = atual + qtd if operacao == "Reposição" else atual - qtd
                requests.patch(f"{URL_BASE}/{path}.json", data=json.dumps({"estoque": novo}))
                st.success(f"✅ Estoque atualizado! Total: {novo}")
                st.session_state.codigo_estoque = ""
            else:
                st.error("❌ Produto não encontrado!")

