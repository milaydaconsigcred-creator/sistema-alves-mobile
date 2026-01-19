import streamlit as st
import requests
import json
import base64
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Alves Gestão Total", page_icon="🍱", layout="wide")

# Credenciais
GOOGLE_API_KEY = "AIzaSyAGjkY5Ynkgm5U6w81W2BpAdhg5fdOeFdU" 
URL_BASE = "https://restaurante-alves-default-rtdb.firebaseio.com/"

if "codigo_lido" not in st.session_state:
    st.session_state.codigo_lido = ""

# --- ESTILIZAÇÃO ---
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 50px; border-radius: 5px; background-color: #f0f2f6; }
    </style>
    """, unsafe_allow_html=True)

st.title("ALVES GESTÃO INTEGRADA 🍱🤖")

# --- ABAS DO SISTEMA ---
tab_estoque, tab_nutri, tab_cozinha, tab_etiquetas = st.tabs([
    "📦 Estoque (IA)", "🍎 Nutricionista", "👨‍🍳 Cozinha", "🏷️ Etiquetas"
])

# ==========================================
# ABA 1: ESTOQUE COM INTELIGÊNCIA ARTIFICIAL
# ==========================================
with tab_estoque:
    st.subheader("Leitura de Código por Imagem")
    foto = st.camera_input("Tire foto dos números do produto")

    if foto:
        imagem_b64 = base64.b64encode(foto.read()).decode('utf-8')
        url_vision = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_API_KEY}"
        payload = {
            "requests": [{"image": {"content": imagem_b64}, "features": [{"type": "TEXT_DETECTION"}]}]
        }

        with st.spinner('IA analisando...'):
            try:
                response = requests.post(url_vision, json=payload)
                resultado = response.json()
                texto = resultado['responses'][0]['fullTextAnnotation']['text']
                numeros = "".join(filter(str.isdigit, texto))
                if numeros:
                    st.session_state.codigo_lido = numeros
                    st.success(f"✅ IA identificou: {numeros}")
            except:
                st.error("Falha na leitura. Tente focar melhor nos números.")

    st.divider()

    # Formulário Unificado: Cadastrar, Reposição e Baixa
    with st.form("estoque_form"):
        col_cod, col_qtd = st.columns([2, 1])
        with col_cod:
            cod_final = st.text_input("Código do Produto", value=st.session_state.codigo_lido)
        with col_qtd:
            qtd = st.number_input("Quantidade", min_value=1, step=1)
        
        operacao = st.radio("Ação", ["Reposição (+)", "Baixa (-)", "Cadastrar Novo"], horizontal=True)
        nome_novo = st.text_input("Nome do Produto (Apenas para cadastro)")
        minimo = st.number_input("Estoque Mínimo (Alerta)", min_value=0, value=5)
        
        btn_salvar = st.form_submit_button("EXECUTAR OPERAÇÃO")

    if btn_salvar and cod_final:
        path = f"produtos/{cod_final}"
        res = requests.get(f"{URL_BASE}{path}.json").json()

        if operacao == "Cadastrar Novo":
            if nome_novo:
                dados = {"nome": nome_novo, "estoque": qtd, "minimo": minimo}
                requests.patch(f"{URL_BASE}{path}.json", json=dados)
                st.success(f"✅ {nome_novo} cadastrado com sucesso!")
            else: st.error("Informe o nome para cadastrar!")
        
        elif res:
            estoque_atual = res.get('estoque', 0)
            novo_valor = (estoque_atual + qtd) if "Reposição" in operacao else (estoque_atual - qtd)
            requests.patch(f"{URL_BASE}{path}.json", json={"estoque": max(0, novo_valor)})
            st.success(f"✅ {res['nome']}: Novo estoque é {max(0, novo_valor)}")
        else:
            st.error("❌ Produto não encontrado! Use a opção 'Cadastrar Novo'.")

    # --- LISTA DE ALERTAS ---
    st.subheader("⚠️ Alertas de Estoque Baixo")
    todos = requests.get(f"{URL_BASE}produtos.json").json()
    if todos:
        for id, info in todos.items():
            if info.get('estoque', 0) <= info.get('minimo', 5):
                st.warning(f"🚨 **{info['nome']}** está com apenas **{info['estoque']}** unidades!")

# ==========================================
# ABA 2: NUTRICIONISTA (Fichas Técnicas)
# ==========================================
with tab_nutri:
    st.subheader("🥗 Controle Nutricional")
    with st.expander("Cadastrar Ficha Técnica"):
        prato = st.text_input("Nome do Prato")
        calorias = st.text_input("Calorias")
        alergenos = st.text_input("Alérgenos")
        if st.button("Salvar Ficha"):
            requests.patch(f"{URL_BASE}fichas/{prato}.json", json={"cal": calorias, "alert": alergenos})
            st.success("Ficha salva!")

# ==========================================
# ABA 3: COZINHA (Cardápio e Pedidos)
# ==========================================
with tab_cozinha:
    st.subheader("👨‍🍳 Painel do Cozinheiro")
    menu = requests.get(f"{URL_BASE}cardapio.json").json()
    if menu:
        st.write("🍽️ **Cardápio do Dia:**")
        for item in menu:
            st.info(item)
    
    novo_item_menu = st.text_input("Adicionar ao Cardápio")
    if st.button("Atualizar Menu"):
        # Lógica simples para lista de cardápio
        requests.put(f"{URL_BASE}cardapio.json", json=[novo_item_menu])
        st.rerun()

# ==========================================
# ABA 4: ETIQUETAS
# ==========================================
with tab_etiquetas:
    st.subheader("🏷️ Gerador de Etiquetas")
    etq_nome = st.text_input("Nome para Etiqueta")
    etq_validade = st.date_input("Data de Validade")
    if st.button("Gerar Etiqueta para Impressão"):
        st.markdown(f"""
            <div style="border: 2px solid black; padding: 10px; width: 250px; text-align: center;">
                <h3>ALVES GESTÃO</h3>
                <p><b>PRODUTO:</b> {etq_nome}</p>
                <p><b>VALIDADE:</b> {etq_validade.strftime('%d/%m/%Y')}</p>
                <p>Lote: {datetime.now().strftime('%Y%m%d')}</p>
            </div>
        """, unsafe_allow_html=True)

