import streamlit as st
import requests
import json
from datetime import datetime
import streamlit.components.v1 as components

# --- CONFIGURAÇÃO DO FIREBASE ---
URL_BASE = "https://restaurante-alves-default-rtdb.firebaseio.com/"

st.set_page_config(page_title="Alves Gestão Mobile", page_icon="🍱", layout="centered")

# --- SCANNER PROFISSIONAL INTEGRADO ---
def scanner_pro(key):
    # Configuração avançada para ler códigos de barras (EAN, CODE128, etc)
    scanner_html = f"""
    <div id="reader-{key}" style="width: 100%; border-radius: 12px; border: 2px solid #1a2a6c; overflow: hidden;"></div>
    <script src="https://unpkg.com/html5-qrcode"></script>
    <script>
        function onScanSuccess(decodedText) {{
            window.parent.postMessage({{
                type: 'streamlit:set_widget_value',
                key: '{key}',
                value: decodedText
            }}, '*');
        }}

        const config = {{ 
            fps: 20, 
            qrbox: {{ width: 300, height: 150 }},
            aspectRatio: 1.0,
            formatsToSupport: [ 
                Html5QrcodeSupportedFormats.EAN_13, 
                Html5QrcodeSupportedFormats.CODE_128, 
                Html5QrcodeSupportedFormats.UPC_A,
                Html5QrcodeSupportedFormats.QR_CODE 
            ]
        }};

        const html5QrcodeScanner = new Html5QrcodeScanner("reader-{key}", config, false);
        html5QrcodeScanner.render(onScanSuccess);
    </script>
    """
    return components.html(scanner_html, height=420)

# --- ESTILIZAÇÃO ---
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    .welcome-card { background: linear-gradient(135deg, #1a2a6c, #b21f1f); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px;}
    .stButton>button { width: 100%; border-radius: 12px; height: 50px; font-weight: bold; background-color: #1a2a6c; color: white; border: none; }
    
    @media print {
        body * { visibility: hidden; }
        .etiqueta-print, .etiqueta-print * { visibility: visible; }
        .etiqueta-print { position: absolute; left: 0; top: 0; width: 100%; border: 2px solid black; padding: 10px; color: black; }
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

# --- NAVEGAÇÃO ---
menu = st.sidebar.selectbox("Menu", ["Início", "📦 Estoque", "🥗 Nutricionista", "👨‍🍳 Cozinheiro", "🏷️ Etiquetas", "⚠️ Alertas"])

if menu == "Início":
    st.markdown('<div class="welcome-card"><h1>ALVES GESTÃO 🍱</h1><p>Sistema Mobile v3.0</p></div>', unsafe_allow_html=True)

elif menu == "📦 Estoque":
    aba = st.tabs(["Cadastrar", "Reposição", "Baixa"])

    with aba[0]:
        st.subheader("📸 Ler Código")
        scanner_pro("cod_cad")
        cod = st.text_input("Código de Barras:", key="cod_cad")
        nome = st.text_input("Nome do Produto")
        c1, c2 = st.columns(2)
        preco = c1.number_input("Preço", min_value=0.0)
        unid = c2.selectbox("Unid", ["UN", "KG", "L", "CX"])
        est_ini = c1.number_input("Estoque Inicial", min_value=0.0)
        est_min = c2.number_input("Estoque Mínimo", min_value=0.0)
        venc = st.date_input("Vencimento")
        if st.button("💾 SALVAR"):
            if cod and nome:
                save_db(f"produtos/{cod}", {"nome": nome, "preco": preco, "medida": unid, "estoque": est_ini, "minimo": est_min, "vencimento": str(venc)})
                st.success("Salvo!")

    with aba[1]:
        st.subheader("📸 Ler para Reposição")
        scanner_pro("cod_rep")
        cod_rep = st.text_input("Código Lido:", key="cod_rep")
        qtd_rep = st.number_input("Qtd a Somar", min_value=0.0)
        if st.button("➕ Confirmar Entrada"):
            p = get_db(f"produtos/{cod_rep}")
            if p:
                save_db(f"produtos/{cod_rep}", {"estoque": p.get('estoque', 0) + qtd_rep})
                st.success("Estoque Atualizado!")
            else: st.error("Produto não cadastrado!")

    with aba[2]:
        st.subheader("📸 Ler para Baixa")
        scanner_pro("cod_bx")
        cod_bx = st.text_input("Código Lido:", key="cod_bx")
        qtd_bx = st.number_input("Qtd a Retirar", min_value=0.0)
        if st.button("📉 Confirmar Saída"):
            p = get_db(f"produtos/{cod_bx}")
            if p and p['estoque'] >= qtd_bx:
                save_db(f"produtos/{cod_bx}", {"estoque": p['estoque'] - qtd_bx})
                st.warning("Baixa realizada!")
            else: st.error("Saldo insuficiente!")

elif menu == "🥗 Nutricionista":
    senha = st.text_input("Senha", type="password")
    if senha == "alvesnutri":
        st.subheader("Nutrição")
        data_c = st.date_input("Data")
        txt_c = st.text_area("Cardápio")
        txt_f = st.text_area("Retirada de Estoque")
        if st.button("🚀 PUBLICAR"):
            save_db(f"cardapios/{data_c.strftime('%Y%m%d')}", {"cardapio": txt_c, "ficha": txt_f})
            st.success("Publicado!")

elif menu == "👨‍🍳 Cozinheiro":
    st.header("Cozinha")
    hoje = datetime.now().strftime("%Y%m%d")
    d = get_db(f"cardapios/{hoje}")
    if d:
        st.info(f"**CARDÁPIO:**\n{d['cardapio']}")
        st.success(f"**RETIRADA:**\n{d['ficha']}")
    else: st.warning("Aguardando nutricionista.")

elif menu == "🏷️ Etiquetas":
    st.header("🏷️ Etiquetas")
    e_nome = st.text_input("Nome")
    c1, c2 = st.columns(2)
    e_venc = c1.date_input("Validade")
    e_manip = c2.date_input("Manipulação")
    e_resp = st.text_input("Responsável")
    e_obs = st.selectbox("Armazenamento", ["Refrigeração", "Congelado", "Seco"])
    
    if st.button("📄 GERAR"):
        st.session_state.p_ok = True

    if st.session_state.get('p_ok'):
        st.markdown(f"""
            <div class="etiqueta-print" style="border: 2px solid black; padding: 10px; background: white; color: black; font-family: Arial;">
                <h3 style="text-align: center; margin: 0;">RESTAURANTE ALVES</h3>
                <hr style="border: 1px solid black;">
                <p><b>PRODUTO:</b> {e_nome.upper()}</p>
                <p><b>VALIDADE:</b> {e_venc.strftime('%d/%m/%Y')} | <b>MANIP.:</b> {e_manip.strftime('%d/%m/%Y')}</p>
                <p><b>RESP.:</b> {e_resp.upper()} | <b>CONS.:</b> {e_obs.upper()}</p>
            </div>
            <br>
            <button onclick="window.print()" style="width:100%; height:50px; background-color:#b21f1f; color:white; border-radius:10px; font-weight:bold; cursor:pointer; border:none;">
                🖨️ IMPRIMIR
            </button>
        """, unsafe_allow_html=True)

elif menu == "⚠️ Alertas":
    st.header("Alertas")
    prods = get_db("produtos")
    if prods:
        for c, p in prods.items():
            if p['estoque'] <= p.get('minimo', 0):
                st.error(f"🚨 {p['nome']} (Saldo: {p['estoque']})")
