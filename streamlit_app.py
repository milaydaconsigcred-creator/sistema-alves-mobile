import streamlit as st
import requests
import json
from PIL import Image, ImageOps, ImageEnhance
from pyzbar.pyzbar import decode

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
        img = Image.open(foto)
        
        # --- TRATAMENTO DE IMAGEM AVANÇADO ---
        # 1. Aumentar o tamanho da imagem (Zoom Digital para barras pequenas)
        w, h = img.size
        img = img.resize((w*2, h*2), resample=Image.LANCZOS)
        
        # 2. Converter para Cinza e aumentar Contraste agressivamente
        img_proc = ImageOps.grayscale(img)
        img_proc = ImageEnhance.Contrast(img_proc).enhance(3.0) 
        img_proc = ImageEnhance.Sharpness(img_proc).enhance(2.0)
        
        # Tenta ler a imagem tratada
        resultados = decode(img_proc)
        
        # Se falhar, tenta na imagem original (caso o tratamento tenha borrado)
        if not resultados:
            resultados = decode(img)
        
        if resultados:
            codigo_lido = resultados[0].data.decode('utf-8')
            st.session_state.codigo_estoque = codigo_lido
            st.success(f"✅ Código identificado: {codigo_lido}")
            st.vibrate() # Vibra o celular se o navegador permitir
        else:
            st.error("⚠️ Não foi possível decodificar. Siga as instruções abaixo:")
            st.write("""
            * **Distância:** Mantenha o celular a um palmo de distância (15-20cm).
            * **Luz:** Evite sombras ou reflexos brilhantes em cima das barras.
            * **Alinhamento:** Deixe o código bem "deitado" (horizontal) na tela.
            """)
            
    except Exception as e:
        st.error("Erro no processamento da imagem.")

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
