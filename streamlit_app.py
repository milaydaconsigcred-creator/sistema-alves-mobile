import streamlit as st
import requests
import json
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DO FIREBASE ---
URL_BASE = "https://restaurante-alves-default-rtdb.firebaseio.com/"

st.set_page_config(page_title="Alves Gestão Mobile", page_icon="🍱", layout="centered")

# --- ESTILO E LOGICA DE IMPRESSÃO ---
st.markdown("""
    <style>
    /* Estilo Geral Moderno */
    .stApp { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 12px; height: 55px; font-weight: bold; font-size: 16px; }
    
    .welcome-card { 
        background: linear-gradient(135deg, #1a2a6c, #b21f1f, #fdbb2d); 
        padding: 25px; border-radius: 20px; color: white; text-align: center; margin-bottom: 25px;
    }

    /* FORMATO ETIQUETA PARA IMPRESSÃO */
    @media print {
        body * { visibility: hidden; }
        .etiqueta-print, .etiqueta-print * { visibility: visible; }
        .etiqueta-print { 
            position: absolute; left: 0; top: 0; 
            width: 100% !important; border: 2px solid black !important;
            padding: 10px;
        }
        header, .stSidebar, .stTabs, button { display: none !important; }
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
    except: st.error("Erro ao salvar dados.")

# --- MENU ---
menu = st.sidebar.selectbox("Navegação", 
    ["Início", "📦 Gestão de Estoque", "🥗 Nutricionista", "👨‍🍳 Cozinheiro", "🏷️ Gerador de Etiquetas", "⚠️ Alertas"])

if menu == "Início":
    st.markdown('<div class="welcome-card"><h1>ALVES GESTÃO 🍱</h1><p>Controle Profissional de Estoque</p></div>', unsafe_allow_html=True)
    st.success(f"🔓 Sistema Conectado | {datetime.now().strftime('%d/%m/%Y')}")

elif menu == "📦 Gestão de Estoque":
    st.header("📦 Controle de Estoque")
    aba = st.tabs(["Cadastrar", "Reposição", "Baixa"])

    with aba[0]:
        # Tentativa de Input de Câmera Nativo do Navegador
        st.write("📸 **Tire uma foto do código de barras para ler o número:**")
        cam_shot = st.camera_input("Scanner", key="scan_cad")
        if cam_shot:
            st.warning("Verifique o número na foto e digite abaixo:")
            
        cod = st.text_input("Número do Código de Barras", key="in_cad")
        nome = st.text_input("Nome do Produto")
        c1, c2 = st.columns(2)
        preco = c1.number_input("Preço", min_value=0.0)
        unid = c2.selectbox("Unidade", ["UN", "KG", "L", "CX"])
        est_ini = c1.number_input("Estoque Inicial", min_value=0.0)
        est_min = c2.number_input("Mínimo Aviso", min_value=0.0)
        venc = st.date_input("Vencimento")
        
        if st.button("💾 SALVAR PRODUTO"):
            if cod and nome:
                save_db(f"produtos/{cod}", {"nome": nome, "preco": preco, "medida": unid, "estoque": est_ini, "minimo": est_min, "vencimento": str(venc)})
                st.success("Salvo!")

    with aba[1]:
        cod_rep = st.text_input("Código para Repor", key="in_rep")
        qtd_rep = st.number_input("Qtd a ADICIONAR", min_value=0.0)
        if st.button("➕ Confirmar Entrada"):
            p = get_db(f"produtos/{cod_rep}")
            if p:
                save_db(f"produtos/{cod_rep}", {"estoque": p.get('estoque', 0) + qtd_rep})
                st.success("Atualizado!")

    with aba[2]:
        cod_bx = st.text_input("Código para Baixa", key="in_bx")
        qtd_bx = st.number_input("Qtd a RETIRAR", min_value=0.0)
        if st.button("📉 Confirmar Saída"):
            p = get_db(f"produtos/{cod_bx}")
            if p and p['estoque'] >= qtd_bx:
                save_db(f"produtos/{cod_bx}", {"estoque": p['estoque'] - qtd_bx})
                st.warning("Baixa realizada!")

elif menu == "🥗 Nutricionista":
    senha = st.text_input("Senha", type="password")
    if senha == "alvesnutri":
        st.subheader("Planejamento Nutricional")
        data_c = st.date_input("Data do Cardápio")
        txt_c = st.text_area("Descrição do Cardápio")
        txt_f = st.text_area("Itens para Baixa (Ficha Técnica)")
        if st.button("🚀 ENVIAR"):
            save_db(f"cardapios/{data_c.strftime('%Y%m%d')}", {"cardapio": txt_c, "ficha": txt_f})
            st.success("Publicado!")

elif menu == "👨‍🍳 Cozinheiro":
    st.header("👨‍🍳 Painel da Cozinha")
    hoje = datetime.now().strftime("%Y%m%d")
    d = get_db(f"cardapios/{hoje}")
    if d:
        st.info(f"**CARDÁPIO:**\n{d['cardapio']}")
        st.success(f"**LISTA DE RETIRADA:**\n{d['ficha']}")
    else: st.warning("Aguardando nutricionista.")

elif menu == "🏷️ Gerador de Etiquetas":
    st.header("🏷️ Etiquetas")
    e_nome = st.text_input("Produto")
    c1, c2 = st.columns(2)
    e_venc = c1.date_input("Validade")
    e_manip = c2.date_input("Manipulação")
    e_resp = st.text_input("Responsável")
    e_obs = st.selectbox("Conservação", ["Refrigeração", "Congelado", "Seco"])
    
    if st.button("📄 GERAR ETIQUETA"):
        st.session_state.ready = True

    if st.session_state.get('ready'):
        st.markdown(f"""
            <div class="etiqueta-print" style="border: 2px solid black; padding: 15px; background: white; color: black; font-family: Arial;">
                <h3 style="text-align: center; margin: 0;">RESTAURANTE ALVES</h3>
                <hr style="border: 1px solid black;">
                <p><b>PRODUTO:</b> {e_nome.upper()}</p>
                <p><b>MANIPULAÇÃO:</b> {e_manip.strftime('%d/%m/%Y')}</p>
                <p><b>VALIDADE:</b> {e_venc.strftime('%d/%m/%Y')}</p>
                <p><b>RESPONSÁVEL:</b> {e_resp.upper()}</p>
                <p><b>CONSERVAÇÃO:</b> {e_obs.upper()}</p>
            </div>
            <br>
            <button onclick="window.print()" style="width:100%; height:55px; background-color:#b21f1f; color:white; border-radius:12px; font-weight:bold; cursor:pointer; border:none;">
                🖨️ IMPRIMIR ETIQUETA AGORA
            </button>
        """, unsafe_allow_html=True)

elif menu == "⚠️ Alertas":
    st.header("⚠️ Alertas Críticos")
    prods = get_db("produtos")
    if prods:
        for c, p in prods.items():
            if p['estoque'] <= p.get('minimo', 0):
                st.error(f"🚨 **{p['nome']}** | Saldo: {p['estoque']}")

