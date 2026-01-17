import streamlit as st
import requests
import json
from PIL import Image, ImageOps, ImageEnhance
import pytesseract
from pyzbar.pyzbar import decode
import re
import numpy as np

st.set_page_config(page_title="Alves Gestão", page_icon="🍱")

if "codigo_estoque" not in st.session_state:
    st.session_state.codigo_estoque = ""

URL_BASE = "https://restaurante-alves-default-rtdb.firebaseio.com/"

st.title("ALVES GESTÃO 🍱")

st.subheader("📷 Escanear Produto")
foto = st.camera_input("Foque nos números abaixo das barras")

if foto:
    try:
        # Carrega a imagem original
        img_original = Image.open(foto)
        
        # --- TRATAMENTO PESADO PARA NÚMEROS (OCR) ---
        # 1. Escala de cinza
        img = ImageOps.grayscale(img_original)
        # 2. Aumento extremo de contraste
        img = ImageEnhance.Contrast(img).enhance(3.0)
        # 3. Binarização (Preto e Branco puro)
        img = img.point(lambda x: 0 if x < 128 else 255, '1')
        
        # Tenta ler Código de Barras
        barras = decode(img_original)
        
        if barras:
            codigo = barras[0].data.decode('utf-8')
            st.session_state.codigo_estoque = codigo
            st.success(f"✅ Barras lidas: {codigo}")
        else:
            # Tenta ler Números (OCR) com a imagem binarizada
            # Usamos o modo 'whitelist' para o sistema focar apenas em números
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789'
            texto = pytesseract.image_to_string(img, config=custom_config)
            
            # Limpa qualquer caractere estranho
            numeros = re.sub(r'\D', '', texto)
            
            if len(numeros) >= 5:
                st.session_state.codigo_estoque = numeros
                st.success(f"✅ Números detectados: {numeros}")
            else:
                st.error("❌ Não foi possível ler. Tente aproximar um pouco mais e manter a mão firme.")
                # Mostra o que o sistema está "vendo" para ajudar o usuário
                st.image(img, caption="Como o sistema está vendo os números", width=300)
                
    except Exception as e:
        st.error(f"Erro no processador: {e}")

st.divider()

# Campo de entrada
cod_final = st.text_input("Código Confirmado:", value=st.session_state.codigo_estoque)

# O restante do seu formulário de estoque permanece o mesmo...


