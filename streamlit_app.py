import streamlit as st
import requests
import json
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DO FIREBASE ---
URL_BASE = "https://restaurante-alves-default-rtdb.firebaseio.com/"

st.set_page_config(page_title="Alves Gestão Mobile", page_icon="🍱", layout="centered")

# --- ESTILO MODERNO E AJUSTE DE IMPRESSÃO ---
st.markdown("""
    <style>
    /* Estilo Geral Moderno */
    .stApp { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 12px; height: 50px; font-weight: bold; transition: 0.3s; }
    
    /* Card de Boas Vindas Estilo App */
    .welcome-card { 
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
        padding: 25px; border-radius: 20px; color: white; 
        text-align: center; margin-bottom: 25px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }

    /* Regras de Impressão (Esconde tudo exceto a etiqueta) */
    @media print {
        header, footer, .stSidebar, .stTabs, button, .no-print, .stCameraInput { 
            display: none !important; 
        }
        .main .block-container { padding: 0 !important; }
        .etiqueta-print { 
            display: block !important; 
            border: 2px solid black !important; 
            width: 100%; padding: 20px; 
            color: black !important;
            position: absolute; top: 0; left: 0;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def get_db(path):
    try:
        res = requests.get(f"{URL_BASE}/{path}.json")
        return res.json() if res.status_code == 200 else {}
    except: return {}

def save_db(path, data):
    try: requests.patch(f"{URL_BASE}/{path}.json", data=json.dumps(data))
    except: st.error("Erro de conexão com o banco.")

# --- MENU LATERAL ---
menu = st.sidebar.selectbox("Navegação", 
    ["Início", "📦 Gestão de Estoque", "🥗 Nutricionista", "👨‍🍳 Cozinheiro", "🏷️ Gerador de Etiquetas", "⚠️ Alertas"])

# --- PÁGINA INICIAL ---
if menu == "Início":
    st.markdown('<div class="welcome-card"><h1>ALVES GESTÃO 🍱</h1><p>Operação de Estoque e Cozinha</p></div>', unsafe_allow_html=True)
    st.info(f"📅 Data: {datetime.now().strftime('%d/%m/%Y')}")

# --- GESTÃO DE ESTOQUE ---
elif menu == "📦 Gestão de Estoque":
    st.header("📦 Estoque")
    aba = st.tabs(["Cadastrar", "Reposição", "Baixa"])

    with aba[0]:
        st.write("📷 **Toque abaixo para abrir o Scanner**")
        # O componente de câmera do Streamlit é o mais estável para evitar erros de permissão repetida
        cam_input = st.camera_input("Capturar Código", key="cam_cad")
        
        cod = st.text_input("Código de Barras (Número):")
        nome = st.text_input("Nome do Produto")
        col1, col2 = st.columns(2)
        preco = col1.number_input("Preço", min_value=0.0)
        unid = col2.selectbox("Unidade", ["UN", "KG", "L", "CX"])
        est_ini = col1.number_input("Estoque Inicial", min_value=0.0)
        est_min = col2.number_input("Mínimo Aviso", min_value=0.0)
        venc = st.date_input("Vencimento")
        
        if st.button("💾 SALVAR PRODUTO"):
            if cod and nome:
                save_db(f"produtos/{cod}", {"nome": nome, "preco": preco, "medida": unid, "estoque": est_ini, "minimo": est_min, "vencimento": str(venc)})
                st.success("Cadastrado!")

    with aba[1]:
        st.camera_input("Scan Reposição", key="cam_rep")
        cod_rep = st.text_input("Código para Repor:")
        qtd_rep = st.number_input("Qtd a ADICIONAR", min_value=0.0)
        if st.button("➕ Confirmar Entrada"):
            p = get_db(f"produtos/{cod_rep}")
            if p:
                save_db(f"produtos/{cod_rep}", {"estoque": p.get('estoque', 0) + qtd_rep})
                st.success("Estoque Atualizado!")

    with aba[2]:
        st.camera_input("Scan Baixa", key="cam_bx")
        cod_bx = st.text_input("Código para Baixa:")
        qtd_bx = st.number_input("Qtd a RETIRAR", min_value=0.0)
        if st.button("📉 Confirmar Saída"):
            p = get_db(f"produtos/{cod_bx}")
            if p and p['estoque'] >= qtd_bx:
                save_db(f"produtos/{cod_bx}", {"estoque": p['estoque'] - qtd_bx})
                st.warning("Baixa realizada!")

# --- NUTRICIONISTA (SENHA: alvesnutri) ---
elif menu == "🥗 Nutricionista":
    senha = st.text_input("Senha", type="password")
    if senha == "alvesnutri":
        st.subheader("Planejamento Nutricional")
        data_c = st.date_input("Data do Cardápio")
        txt_c = st.text_area("O que será servido?")
        txt_f = st.text_area("Itens para retirar do estoque")
        if st.button("🚀 ENVIAR PARA COZINHA"):
            save_db(f"cardapios/{data_c.strftime('%Y%m%d')}", {"cardapio": txt_c, "ficha": txt_f})
            st.success("Publicado!")

# --- COZINHEIRO ---
elif menu == "👨‍🍳 Cozinheiro":
    st.header("Painel da Cozinha")
    hoje = datetime.now().strftime("%Y%m%d")
    d = get_db(f"cardapios/{hoje}")
    if d:
        st.info(f"**CARDÁPIO DO DIA:**\n{d['cardapio']}")
        st.success(f"**LISTA DE RETIRADA:**\n{d['ficha']}")
    else: st.warning("A nutricionista ainda não lançou o cardápio de hoje.")

# --- ETIQUETAS COM IMPRESSÃO ISOLADA ---
elif menu == "🏷️ Gerador de Etiquetas":
    st.header("🏷️ Gerar Etiqueta")
    e_nome = st.text_input("Nome do Alimento")
    c1, c2 = st.columns(2)
    e_venc = c1.date_input("Validade")
    e_manip = c2.date_input("Manipulação")
    e_resp = st.text_input("Responsável")
    e_obs = st.selectbox("Conservação", ["Sob Refrigeração", "Congelado", "Temperatura Ambiente"])
    
    if st.button("GERAR E VISUALIZAR"):
        st.session_state.print_ok = True

    if st.session_state.get('print_ok'):
        # Bloco da Etiqueta
        st.markdown(f"""
            <div class="etiqueta-print" style="border: 2px solid black; padding: 15px; background: white; color: black; font-family: Arial; margin-top: 10px;">
                <h3 style="text-align: center; margin: 0; color: black;">RESTAURANTE ALVES</h3>
                <hr style="border: 1px solid black;">
                <p style="font-size: 14px; margin: 5px 0;"><b>PRODUTO:</b> {e_nome.upper()}</p>
                <p style="font-size: 14px; margin: 5px 0;"><b>MANIPULAÇÃO:</b> {e_manip.strftime('%d/%m/%Y')}</p>
                <p style="font-size: 14px; margin: 5px 0;"><b>VALIDADE:</b> {e_venc.strftime('%d/%m/%Y')}</p>
                <p style="font-size: 14px; margin: 5px 0;"><b>RESPONSÁVEL:</b> {e_resp.upper()}</p>
                <p style="font-size: 14px; margin: 5px 0;"><b>CONSERVAÇÃO:</b> {e_obs.upper()}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Botão de Impressão Moderno
        st.markdown('''
            <button onclick="window.print()" style="
                width: 100%; background-color: #1e3c72; color: white; 
                border: none; padding: 15px; border-radius: 12px; 
                font-weight: bold; margin-top: 15px; cursor: pointer;">
                🖨️ IMPRIMIR ETIQUETA AGORA
            </button>
        ''', unsafe_allow_html=True)

# --- ALERTAS ---
elif menu == "⚠️ Alertas":
    st.header("Alertas Críticos")
    prods = get_db("produtos")
    if prods:
        for c, p in prods.items():
            if p['estoque'] <= p.get('minimo', 0):
                st.error(f"🚨 **{p['nome']}** está acabando! (Saldo: {p['estoque']})")

