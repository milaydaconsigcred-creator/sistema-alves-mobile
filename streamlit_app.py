import streamlit as st
import requests
import json
from PIL import Image
from pyzbar.pyzbar import decode

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Alves Gestão", page_icon="🍱")

# Memória para o código não sumir
if "codigo_estoque" not in st.session_state:
    st.session_state.codigo_estoque = ""

URL_BASE = "https://restaurante-alves-default-rtdb.firebaseio.com/"

st.title("ALVES GESTÃO 🍱")

# --- ÁREA DO SCANNER ---
st.subheader("📷 1. Escanear")
foto = st.camera_input("Aponte para o código de barras")

if foto:
    # Processa a foto usando pyzbar (mais estável)
    try:
        img = Image.open(foto)
        resultados = decode(img)
        
        if resultados:
            # Pega o primeiro código encontrado
            codigo_lido = resultados[0].data.decode('utf-8')
            st.session_state.codigo_estoque = codigo_lido
            st.success(f"✅ Código: {codigo_lido}")
        else:
            st.warning("⚠️ Não foi possível ler as barras. Tente afastar um pouco o celular ou melhorar a iluminação.")
    except Exception as e:
        st.error("Erro ao processar imagem. Tente tirar a foto novamente.")

st.divider()

# --- ÁREA DE DADOS ---
st.subheader("📦 2. Confirmar Dados")

# O campo puxa o que foi lido, mas aceita digitação manual
cod_final = st.text_input("Código do Produto", value=st.session_state.codigo_estoque)

with st.form("estoque_form", clear_on_submit=False):
    operacao = st.radio("Ação", ["Reposição", "Baixa", "Cadastrar"], horizontal=True)
    qtd = st.number_input("Quantidade", min_value=0.0, step=1.0)
    
    nome_item = ""
    if operacao == "Cadastrar":
        nome_item = st.text_input("Nome do Novo Produto")
        
    enviar = st.form_submit_button("CONCLUIR")

if enviar:
    if not cod_final:
        st.error("Erro: Falta o código de barras!")
    else:
        path = f"produtos/{cod_final}"
        if operacao == "Cadastrar":
            if nome_item:
                requests.patch(f"{URL_BASE}/{path}.json", data=json.dumps({"nome": nome_item, "estoque": qtd}))
                st.success(f"✅ {nome_item} cadastrado!")
                st.session_state.codigo_estoque = ""
            else: st.error("Por favor, digite o nome do produto.")
        else:
            # Busca no Firebase
            res = requests.get(f"{URL_BASE}/{path}.json").json()
            if res:
                atual = res.get('estoque', 0)
                novo = atual + qtd if operacao == "Reposição" else atual - qtd
                requests.patch(f"{URL_BASE}/{path}.json", data=json.dumps({"estoque": novo}))
                st.success(f"✅ Sucesso! Novo saldo de {res.get('nome')}: {novo}")
                st.session_state.codigo_estoque = "" 
            else:
                st.error("❌ Produto não encontrado no sistema!")
