import streamlit as st
import requests
import json
from datetime import datetime
from streamlit_quagga2 import st_quagga2

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Alves Gestão", page_icon="🍱")

# Banco de Dados
URL_BASE = "https://restaurante-alves-default-rtdb.firebaseio.com/"

st.title("ALVES GESTÃO 🍱")

# --- SCANNER AO VIVO ---
st.subheader("📷 Escanear Código")
st.write("Aponte para o código. O celular vai ler sozinho.")

# Abre a câmera DENTRO do navegador
barcode = st_quagga2(key='scanner')

# Memória do código
if "cod_final" not in st.session_state:
    st.session_state.cod_final = ""

if barcode:
    st.session_state.cod_final = barcode
    st.success(f"✅ Lido: {barcode}")

st.divider()

# --- FORMULÁRIO ---
with st.form("alves_form"):
    # Se o scanner leu, o número aparece aqui automaticamente
    cod_input = st.text_input("Código do Produto:", value=st.session_state.cod_final)
    
    aba = st.radio("Operação", ["Reposição", "Baixa", "Cadastrar"], horizontal=True)
    qtd = st.number_input("Quantidade", min_value=0.0, step=1.0)
    
    nome_p = ""
    if aba == "Cadastrar":
        nome_p = st.text_input("Nome do Novo Produto")
        
    confirmar = st.form_submit_button("CONCLUIR")

if confirmar:
    if not cod_input:
        st.error("Erro: Sem código!")
    else:
        path = f"produtos/{cod_input}"
        if aba == "Cadastrar":
            if nome_p:
                requests.patch(f"{URL_BASE}/{path}.json", data=json.dumps({"nome": nome_p, "estoque": qtd}))
                st.success("✅ Cadastrado!")
            else: st.warning("Digite o nome!")
        else:
            # Busca no Firebase
            res = requests.get(f"{URL_BASE}/{path}.json").json()
            if res:
                atual = res.get('estoque', 0)
                novo = atual + qtd if aba == "Reposição" else atual - qtd
                requests.patch(f"{URL_BASE}/{path}.json", data=json.dumps({"estoque": novo}))
                st.success(f"✅ Sucesso! Novo saldo: {novo}")
                st.session_state.cod_final = "" # Limpa para o próximo
            else:
                st.error("❌ Produto não encontrado!")

