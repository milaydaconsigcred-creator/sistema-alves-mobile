import streamlit as st
import requests
import json
from PIL import Image, ImageOps, ImageEnhance
import pytesseract
from pyzbar.pyzbar import decode
import re

st.set_page_config(page_title="Alves Gestão", page_icon="🍱")

if "codigo_estoque" not in st.session_state:
    st.session_state.codigo_estoque = ""

URL_BASE = "https://restaurante-alves-default-rtdb.firebaseio.com/"

st.title("ALVES GESTÃO 🍱")

st.subheader("📷 Escanear Produto")
# Usamos o camera_input que é o mais estável para não reiniciar o app
foto = st.camera_input("Foque nos números ou nas barras")

if foto:
    try:
        # 1. Carregar a imagem original
        img_original = Image.open(foto)
        
        # 2. Criar versões para o sistema tentar ler
        img_cinza = ImageOps.grayscale(img_original)
        img_contraste = ImageEnhance.Contrast(img_cinza).enhance(2.0)
        
        # --- TENTATIVA 1: CÓDIGO DE BARRAS ---
        barras = decode(img_original)
        if not barras:
            barras = decode(img_contraste) # Tenta no contraste se falhar na original
            
        if barras:
            codigo = barras[0].data.decode('utf-8')
            st.session_state.codigo_estoque = codigo
            st.success(f"✅ Barras lidas: {codigo}")
        else:
            # --- TENTATIVA 2: NÚMEROS (OCR) ---
            # Filtro para ler apenas dígitos
            config_numeros = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789'
            
            # Tenta ler na imagem de alto contraste (melhor para números)
            texto = pytesseract.image_to_string(img_contraste, config=config_numeros)
            numeros = re.sub(r'\D', '', texto)
            
            if len(numeros) >= 5:
                st.session_state.codigo_estoque = numeros
                st.success(f"✅ Números detectados: {numeros}")
            else:
                st.warning("⚠️ Não foi possível ler automaticamente.")
                st.info("Dica: Tente afastar um pouco o celular e garanta que haja luz direta sobre o código.")
                
    except Exception as e:
        st.error(f"Erro no processamento: {e}")

st.divider()

# Campo de entrada (O funcionário pode digitar se tudo falhar)
cod_final = st.text_input("Número do Código:", value=st.session_state.codigo_estoque)

with st.form("estoque_form"):
    operacao = st.radio("Operação", ["Reposição", "Baixa", "Cadastrar"], horizontal=True)
    qtd = st.number_input("Quantidade", min_value=0.0, step=1.0)
    
    nome_item = ""
    if operacao == "Cadastrar":
        nome_item = st.text_input("Nome do Novo Produto")
        
    enviar = st.form_submit_button("CONCLUIR")

if enviar:
    if not cod_final:
        st.error("Erro: Digite ou escanie um código!")
    else:
        path = f"produtos/{cod_final}"
        if operacao == "Cadastrar":
            if nome_item:
                requests.patch(f"{URL_BASE}/{path}.json", data=json.dumps({"nome": nome_item, "estoque": qtd}))
                st.success("✅ Cadastrado!")
                st.session_state.codigo_estoque = ""
            else: st.error("Falta o nome!")
        else:
            res = requests.get(f"{URL_BASE}/{path}.json").json()
            if res:
                atual = res.get('estoque', 0)
                novo = atual + qtd if operacao == "Reposição" else atual - qtd
                requests.patch(f"{URL_BASE}/{path}.json", data=json.dumps({"estoque": novo}))
                st.success(f"✅ Saldo Atualizado: {novo}")
                st.session_state.codigo_estoque = ""
            else:
                st.error("❌ Produto não encontrado!")

