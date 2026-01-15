import streamlit as st
import requests
import json
from datetime import datetime
import streamlit.components.v1 as components

# --- CONFIGURAÇÃO DO FIREBASE ---
URL_BASE = "https://restaurante-alves-default-rtdb.firebaseio.com/"

st.set_page_config(page_title="Alves Gestão Mobile", page_icon="🍱", layout="centered")

# --- SCANNER DE ALTA PRECISÃO (SIMULA APK NATIVO) ---
def scanner_pro(key):
    scanner_html = f"""
    <div style="background: #000; padding: 5px; border-radius: 15px;">
        <div id="reader-{key}" style="width: 100%; border-radius: 10px;"></div>
    </div>
    <script src="https://unpkg.com/html5-qrcode"></script>
    <script>
        function onScanSuccess(decodedText) {{
            window.parent.postMessage({{
                type: 'streamlit:set_widget_value',
                key: '{key}',
                value: decodedText
            }}, '*');
            // Feedback tátil (vibração) se o celular permitir
            if (navigator.vibrate) navigator.vibrate(100);
        }}
        
        const html5QrCode = new Html5Qrcode("reader-{key}");
        const config = {{ 
            fps: 30, // Mais rápido para não perder o foco
            qrbox: {{ width: 250, height: 150 }},
            aspectRatio: 1.0,
            experimentalFeatures: {{ useBarCodeDetectorIfSupported: true }} // Usa o motor do Android/iOS se disponível
        }};

        // Força câmera traseira com resolução máxima
        html5QrCode.start(
            {{ facingMode: "environment" }}, 
            config, 
            onScanSuccess
        ).catch(err => console.error(err));
    </script>
    """
    return components.html(scanner_html, height=400)

# --- ESTILO ---
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    .stButton>button { width: 100%; border-radius: 12px; height: 55px; font-weight: bold; background-color: #1e3c72; color: white; }
    /* Estilo da Etiqueta */
    @media print {
        header, .stSidebar, .stTabs, button, .no-print { display: none !important; }
        .etiqueta-print { display: block !important; border: 3px solid black; padding: 20px; color: black !important; }
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
    except: st.error("Erro no banco.")

# --- MENU ---
menu = st.sidebar.selectbox("Menu", ["Início", "📦 Estoque", "🥗 Nutricionista", "👨‍🍳 Cozinheiro", "🏷️ Etiquetas", "⚠️ Alertas", "📚 Histórico"])

if menu == "Início":
    st.title("ALVES GESTÃO 🍱")
    st.info("💡 Para instalar como Aplicativo: Clique nos 3 pontinhos do Chrome e escolha 'Instalar Aplicativo'.")

elif menu == "📦 Estoque":
    aba = st.tabs(["Cadastrar", "Reposição", "Baixa"])
    
    with aba[0]:
        scanner_pro("cod_cad")
        cod = st.text_input("Código Lido:", key="cod_cad")
        nome = st.text_input("Nome")
        c1, c2 = st.columns(2)
        preco = c1.number_input("Preço", min_value=0.0)
        unid = c2.selectbox("Unid", ["UN", "KG", "L", "CX"])
        est_ini = c1.number_input("Estoque Atual", min_value=0.0)
        est_min = c2.number_input("Estoque Mínimo", min_value=0.0)
        venc = st.date_input("Validade")
        if st.button("💾 SALVAR PRODUTO"):
            save_db(f"produtos/{cod}", {"nome": nome, "preco": preco, "medida": unid, "estoque": est_ini, "minimo": est_min, "vencimento": str(venc)})
            st.success("Salvo!")

    with aba[1]:
        scanner_pro("cod_rep")
        cod_rep = st.text_input("Código:", key="cod_rep")
        qtd_rep = st.number_input("Qtd a Adicionar", min_value=0.0)
        if st.button("➕ Confirmar Entrada"):
            p = get_db(f"produtos/{cod_rep}")
            if p:
                save_db(f"produtos/{cod_rep}", {"estoque": p.get('estoque', 0) + qtd_rep})
                st.success("Estoque Atualizado!")

    with aba[2]:
        scanner_pro("cod_bx")
        cod_bx = st.text_input("Código:", key="cod_bx")
        qtd_bx = st.number_input("Qtd a Retirar", min_value=0.0)
        if st.button("📉 Confirmar Saída"):
            p = get_db(f"produtos/{cod_bx}")
            if p and p['estoque'] >= qtd_bx:
                save_db(f"produtos/{cod_bx}", {"estoque": p['estoque'] - qtd_bx})
                st.warning("Baixa realizada!")

elif menu == "🥗 Nutricionista":
    senha = st.text_input("Senha", type="password")
    if senha == "alvesnutri":
        data_c = st.date_input("Data")
        txt_c = st.text_area("Cardápio")
        txt_f = st.text_area("Ficha de Retirada")
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
    else: st.warning("Aguardando cardápio de hoje. A tela foi limpa.")

elif menu == "📚 Histórico":
    st.header("Histórico")
    todos = get_db("cardapios")
    if todos:
        datas = sorted(todos.keys(), reverse=True)
        sel = st.selectbox("Data", datas)
        st.write(f"**Cardápio:** {todos[sel]['cardapio']}")
        st.write(f"**Ficha:** {todos[sel]['ficha']}")

elif menu == "🏷️ Etiquetas":
    e_nome = st.text_input("Produto")
    c1, c2 = st.columns(2)
    e_venc = c1.date_input("Validade")
    e_manip = c2.date_input("Manipulação")
    e_resp = st.text_input("Responsável")
    e_obs = st.selectbox("Conservação", ["Refrigeração", "Congelado", "Seco"])
    if st.button("📄 GERAR"):
        st.session_state.ok = True
    if st.session_state.get('ok'):
        st.markdown(f'<div class="etiqueta-print"><h3>ALVES RESTAURANTE</h3><hr><p><b>PRODUTO:</b> {e_nome.upper()}</p><p><b>VALIDADE:</b> {e_venc.strftime("%d/%m/%Y")}</p><p><b>RESP.:</b> {e_resp.upper()}</p></div>', unsafe_allow_html=True)
        st.markdown('<button onclick="window.print()">IMPRIMIR</button>', unsafe_allow_html=True)

elif menu == "⚠️ Alertas":
    st.header("Alertas")
    prods = get_db("produtos")
    hoje_dt = datetime.now()
    if prods:
        for c, p in prods.items():
            if p['estoque'] <= p.get('minimo', 0):
                st.error(f"📉 **ESTOQUE BAIXO:** {p['nome']} ({p['estoque']})")
            try:
                v_dt = datetime.strptime(p['vencimento'], '%Y-%m-%d')
                dias = (v_dt - hoje_dt).days
                if 0 <= dias <= 7: st.warning(f"⌛ **VENCENDO:** {p['nome']} em {dias} dias")
                elif dias < 0: st.error(f"❌ **VENCIDO:** {p['nome']}")
            except: pass
