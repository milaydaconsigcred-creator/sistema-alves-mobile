import streamlit as st
import requests
import json
import base64

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Alves IA", page_icon="🤖")

# COLE SUA CHAVE DO GOOGLE AQUI
GOOGLE_API_KEY = "AIzaSyAGjkY5Ynkgm5U6w81W2BpAdhg5fdOeFdU" 
URL_FIREBASE = "https://restaurante-alves-default-rtdb.firebaseio.com/produtos/"

st.title("ALVES GESTÃO + IA 🤖")

foto = st.camera_input("Tire uma foto nítida dos números")

if foto:
    # 1. Converter a foto para Base64 (formato que a IA entende)
    imagem_bytes = foto.read()
    imagem_b64 = base64.b64encode(imagem_bytes).decode('utf-8')

    # 2. Preparar a chamada para a IA do Google Vision
    url_vision = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_API_KEY}"
    payload = {
        "requests": [
            {
                "image": {"content": imagem_b64},
                "features": [{"type": "TEXT_DETECTION"}]
            }
        ]
    }

    with st.spinner('IA analisando a imagem...'):
        response = requests.post(url_vision, json=payload)
        resultado = response.json()

    # 3. Extrair os números do que a IA leu
    try:
        texto_completo = resultado['responses'][0]['fullTextAnnotation']['text']
        # Filtra apenas os números do texto
        numeros_encontrados = "".join(filter(str.isdigit, texto_completo))
        
        if numeros_encontrados:
            st.session_state.codigo_lido = numeros_encontrados
            st.success(f"✅ IA Identificou: {numeros_encontrados}")
        else:
            st.error("A IA não encontrou números na foto.")
    except:
        st.error("Erro ao conectar com a IA ou imagem ilegível.")

# --- FORMULÁRIO DE ESTOQUE ---
st.divider()
codigo_final = st.text_input("Confirmar Código", value=st.session_state.get('codigo_lido', ""))

# (O resto do seu código de salvar no Firebase continua igual aqui...)
