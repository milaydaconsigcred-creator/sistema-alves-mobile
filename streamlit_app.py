import streamlit as st
import requests
import json
from datetime import datetime, timedelta
from streamlit_barcode_reader import barcode_reader # Biblioteca para abrir a câmera

# --- CONFIGURAÇÃO DO FIREBASE ---
URL_BASE = "https://restaurante-alves-default-rtdb.firebaseio.com/"

st.set_page_config(page_title="Alves Gestão Mobile", page_icon="🍱", layout="centered")

# --- ESTILO E LOGICA DE IMPRESSÃO ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    .welcome-card { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px; }
    
    /* Regra para imprimir apenas a etiqueta */
    @media print {
        .no-print { display: none !important; }
        .stApp { background: white !important; }
        header, footer, .stSidebar, .stTabs, button { display: none !important; }
        .etiqueta-print { display: block !important; border: 2px solid black !important; width: 100%; padding: 20px; }
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
    except: st.error("Erro de conexão.")

# --- MENU ---
menu = st.sidebar.selectbox("Navegação", 
    ["Início", "📦 Gestão de Estoque", "🥗 Nutricionista", "👨‍🍳 Cozinheiro", "🏷️ Gerador de Etiquetas", "⚠️ Alertas"])

# --- INÍCIO ---
if menu == "Início":
    st.markdown('<div class="welcome-card"><h1>ALVES RESTAURANTE 🍱</h1><p>Sistema Mobile de Gestão</p></div>', unsafe_allow_html=True)
    st.info(f"📅 Hoje é dia: {datetime.now().strftime('%d/%m/%Y')}")

# --- GESTÃO DE ESTOQUE (COM SCANNER DE CÂMERA) ---
elif menu == "📦 Gestão de Estoque":
    st.header("📦 Estoque")
    aba = st.tabs(["Cadastrar", "Reposição", "Baixa"])

    with aba[0]:
        st.write("📷 **Abrir Scanner de Câmera**")
        barcode = barcode_reader() # Abre a câmera para ler o código
        
        cod = st.text_input("Código Lido:", value=barcode if barcode else "")
        nome = st.text_input("Nome do Produto")
        preco = st.number_input("Preço", min_value=0.0)
        unid = st.selectbox("Unidade", ["UN", "KG", "L", "CX"])
        est_ini = st.number_input("Estoque Inicial", min_value=0.0)
        est_min = st.number_input("Mínimo Aviso", min_value=0.0)
        venc = st.date_input("Vencimento")
        
        if st.button("SALVAR PRODUTO"):
            if cod and nome:
                save_db(f"produtos/{cod}", {"nome": nome, "preco": preco, "medida": unid, "estoque": est_ini, "minimo": est_min, "vencimento": str(venc)})
                st.success("Salvo com sucesso!")

    with aba[1]:
        barcode_rep = barcode_reader(key="scan_rep")
        cod_rep = st.text_input("Código Reposição:", value=barcode_rep if barcode_rep else "")
        qtd_rep = st.number_input("Qtd a somar", min_value=0.0)
        if st.button("CONFIRMAR ENTRADA"):
            p = get_db(f"produtos/{cod_rep}")
            if p:
                save_db(f"produtos/{cod_rep}", {"estoque": p.get('estoque', 0) + qtd_rep})
                st.success("Estoque Atualizado!")

    with aba[2]:
        barcode_bx = barcode_reader(key="scan_bx")
        cod_bx = st.text_input("Código Baixa:", value=barcode_bx if barcode_bx else "")
        qtd_bx = st.number_input("Qtd a retirar", min_value=0.0)
        if st.button("CONFIRMAR BAIXA"):
            p = get_db(f"produtos/{cod_bx}")
            if p and p['estoque'] >= qtd_bx:
                save_db(f"produtos/{cod_bx}", {"estoque": p['estoque'] - qtd_bx})
                st.warning("Baixa realizada!")

# --- NUTRICIONISTA ---
elif menu == "🥗 Nutricionista":
    senha = st.text_input("Senha", type="password")
    if senha == "alvesnutri":
        st.subheader("Planejamento")
        data_c = st.date_input("Data")
        txt_c = st.text_area("Cardápio")
        txt_f = st.text_area("Ficha de Retirada")
        if st.button("PUBLICAR"):
            save_db(f"cardapios/{data_c.strftime('%Y%m%d')}", {"cardapio": txt_c, "ficha": txt_f})
            st.success("Enviado!")

# --- COZINHEIRO ---
elif menu == "👨‍🍳 Cozinheiro":
    st.header("Painel da Cozinha")
    hoje = datetime.now().strftime("%Y%m%d")
    d = get_db(f"cardapios/{hoje}")
    if d:
        st.info(f"**CARDÁPIO:**\n{d['cardapio']}")
        st.success(f"**LISTA DE RETIRADA:**\n{d['ficha']}")
    else: st.write("Aguardando cardápio.")

# --- ETIQUETAS COM BOTÃO DE IMPRESSÃO ---
elif menu == "🏷️ Gerador de Etiquetas":
    st.header("🏷️ Etiquetas")
    with st.container():
        e_nome = st.text_input("Produto")
        e_venc = st.date_input("Validade")
        e_manip = st.date_input("Manipulação")
        e_resp = st.text_input("Responsável")
        e_obs = st.selectbox("Conservação", ["Refrigeração", "Congelado", "Seco"])
        
        if st.button("GERAR ETIQUETA"):
            st.session_state.etiqueta_pronta = True

        if st.session_state.get('etiqueta_pronta'):
            # HTML da Etiqueta
            st.markdown(f"""
                <div class="etiqueta-print" id="printable-etiqueta" style="border: 2px solid black; padding: 15px; background: white; color: black; font-family: Arial;">
                    <h3 style="text-align: center; margin: 0;">RESTAURANTE ALVES</h3>
                    <hr style="border: 1px solid black;">
                    <p><b>PRODUTO:</b> {e_nome.upper()}</p>
                    <p><b>MANIPULADO:</b> {e_manip.strftime('%d/%m/%Y')} | <b>VALIDADE:</b> {e_venc.strftime('%d/%m/%Y')}</p>
                    <p><b>RESPONSÁVEL:</b> {e_resp.upper()}</p>
                    <p><b>CONSERVAÇÃO:</b> {e_obs.upper()}</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Botão que aciona a função de imprimir do navegador
            st.markdown('<button onclick="window.print()" style="width:100%; height:50px; background-color:#1e3c72; color:white; border-radius:8px; margin-top:10px;">🖨️ IMPRIMIR ETIQUETA</button>', unsafe_allow_html=True)

# --- ALERTAS ---
elif menu == "⚠️ Alertas":
    st.header("Alertas")
    prods = get_db("produtos")
    if prods:
        for c, p in prods.items():
            if p['estoque'] <= p.get('minimo', 0):
                st.error(f"{p['nome']} (Saldo: {p['estoque']})")

