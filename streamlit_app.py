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
            {import streamlit as st
import requests
import json
import base64

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Alves IA Pro", page_icon="🍱")

# 1. COLE SUA CHAVE AQUI (A que começa com AIza...)
GOOGLE_API_KEY = "SUA_CHAVE_AQUI" 
URL_FIREBASE = "https://restaurante-alves-default-rtdb.firebaseio.com/produtos/"

if "codigo_lido" not in st.session_state:
    st.session_state.codigo_lido = ""

st.title("ALVES GESTÃO + IA 🤖")

# --- CAPTURA DE IMAGEM ---
foto = st.camera_input("Foque nos números do código de barras")

if foto:
    # Converter para Base64
    imagem_b64 = base64.b64encode(foto.read()).decode('utf-8')

    # Chamada para Google Vision
    url_vision = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_API_KEY}"
    payload = {
        "requests": [{
            "image": {"content": imagem_b64},
            "features": [{"type": "TEXT_DETECTION"}]
        }]
    }

    with st.spinner('A IA do Google está lendo a imagem...'):
        try:
            response = requests.post(url_vision, json=payload)
            resultado = response.json()

            if 'error' in resultado:
                st.error(f"Erro do Google: {resultado['error']['message']}")
            else:
                # Extrair texto e limpar deixando apenas números
                texto = resultado['responses'][0].get('fullTextAnnotation', {}).get('text', '')
                numeros = "".join(filter(str.isdigit, texto))
                
                if numeros:
                    st.session_state.codigo_lido = numeros
                    st.success(f"✅ IA Identificou: {numeros}")
                else:
                    st.warning("A IA não detectou números. Tente aproximar mais a câmera.")
        except Exception as e:
            st.error("Erro na conexão. Verifique a internet.")

st.divider()

# --- FORMULÁRIO DE ESTOQUE ---
cod_final = st.text_input("Código Identificado", value=st.session_state.codigo_lido)

col1, col2 = st.columns(2)
with col1:
    operacao = st.selectbox("Operação", ["Reposição (+)", "Baixa (-)"])
with col2:
    quantidade = st.number_input("Qtd", min_value=1, step=1)

if st.button("CONFIRMAR E SALVAR NO FIREBASE", use_container_width=True):
    if not cod_final:
        st.error("Falta o código do produto!")
    else:
        # Lógica de atualização no Firebase
        res = requests.get(f"{URL_FIREBASE}{cod_final}.json").json()
        
        estoque_atual = res.get('estoque', 0) if res else 0
        nome_item = res.get('nome', 'Produto Novo') if res else 'Produto Novo'
        
        if operacao == "Reposição (+)":
            novo_total = estoque_atual + quantidade
        else:
            novo_total = estoque_atual - quantidade

        dados_atualizados = {"estoque": novo_total}
        requests.patch(f"{URL_FIREBASE}{cod_final}.json", json=dados_atualizados)
        
        st.balloons()
        st.success(f"Estoque de '{nome_item}' atualizado para {novo_total}!")
        st.session_state.codigo_lido = "" # Limpa para o próximo

