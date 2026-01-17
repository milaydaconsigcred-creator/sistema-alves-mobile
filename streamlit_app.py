import streamlit as st
import requests
import json
from PIL import Image, ImageOps, ImageEnhance
from pyzbar.pyzbar import decode
import numpy as np

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Alves Gestão", page_icon="🍱")

if "codigo_estoque" not in st.session_state:
    st.session_state.codigo_estoque = ""

URL_BASE = "https://restaurante-alves-default-rtdb.firebaseio.com/"

st.title("ALVES GESTÃO 🍱")

# --- ÁREA DO SCANNER ---
st.subheader("📷 1. Escanear")
foto = st.camera_input("Aponte para o código de barras")

if foto:
    try:
        # Abre a imagem
        img = Image.open(foto)
        
        # --- TRATAMENTO DE IMAGEM PARA LEITURA ---
        # 1. Converter para escala de cinza (ajuda o leitor a focar nas barras)
        img_processada = ImageOps.grayscale(img)
        # 2. Aumentar o contraste (deixa o preto mais preto e o branco mais branco)
        enhancer = ImageEnhance.Contrast(img_processada)
        img_processada = enhancer.enhance(2.0) 
        
        # Tenta ler a imagem tratada
        resultados = decode(img_processada)
        
        # Se não ler na primeira, tenta na imagem original também
        if not resultados:
            resultados = decode(img)
        
        if resultados:
            codigo_lido = resultados[0].data.decode('utf-8')
            st.session_state.codigo_estoque = codigo_lido
            st.success(f"✅ Código identificado: {codigo_lido}")
            st.balloons() # Efeito visual de sucesso
        else:
            st.warning("⚠️ O código está nítido, mas o sistema não reconheceu as barras. Tente aproximar um pouco mais ou manter o código bem horizontal.")
            
    except Exception as e:
        st.error("Erro técnico no processamento. Tente novamente.")

st.divider()

# --- ÁREA DE DADOS (O restante continua igual) ---
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
                st.session_state.codigo_estoque = ""
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
