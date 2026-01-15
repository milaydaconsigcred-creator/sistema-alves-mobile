import streamlit as st
import requests
import json
from datetime import datetime
import streamlit.components.v1 as components

# --- CONFIGURAÇÃO DO FIREBASE ---
URL_BASE = "https://restaurante-alves-default-rtdb.firebaseio.com/"

st.set_page_config(page_title="Alves Gestão Mobile", page_icon="🍱", layout="centered")

# --- COMPONENTE DO SCANNER (RESTAURADO) ---
def scanner_pro(key):
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
        const html5QrCode = new Html5Qrcode("reader-{key}");
        const config = {{ fps: 20, qrbox: {{ width: 280, height: 120 }}, aspectRatio: 1.0 }};
        html5QrCode.start({{ facingMode: "environment" }}, config, onScanSuccess);
    </script>
    """
    return components.html(scanner_html, height=350)

# --- ESTILIZAÇÃO ---
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    .stButton>button { width: 100%; border-radius: 12px; height: 50px; font-weight: bold; background-color: #1a2a6c; color: white; }
    @media print {
        body * { visibility: hidden; }
        .etiqueta-print, .etiqueta-print * { visibility: visible; }
        .etiqueta-print { position: absolute; left: 0; top: 0; width: 100%; border: 1px solid black; padding: 10px; color: black; }
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

# --- NAVEGAÇÃO ---
menu = st.sidebar.selectbox("Menu", ["Início", "📦 Estoque", "🥗 Nutricionista", "👨‍🍳 Cozinheiro", "🏷️ Etiquetas", "⚠️ Alertas", "📚 Histórico"])

if menu == "Início":
    st.title("ALVES GESTÃO 🍱")
    st.write(f"📅 Hoje: {datetime.now().strftime('%d/%m/%Y')}")

elif menu == "📦 Estoque":
    aba = st.tabs(["Cadastrar", "Reposição", "Baixa"])
    
    with aba[0]: # CADASTRO
        scanner_pro("cod_cad")
        cod = st.text_input("Código:", key="cod_cad")
        nome = st.text_input("Nome do Produto")
        c1, c2 = st.columns(2)
        preco = c1.number_input("Preço", min_value=0.0)
        unid = c2.selectbox("Unid", ["UN", "KG", "L", "CX"])
        est_ini = c1.number_input("Estoque Inicial", min_value=0.0)
        est_min = c2.number_input("Mínimo", min_value=0.0)
        venc = st.date_input("Vencimento")
        if st.button("💾 SALVAR"):
            save_db(f"produtos/{cod}", {"nome": nome, "preco": preco, "medida": unid, "estoque": est_ini, "minimo": est_min, "vencimento": str(venc)})
            st.success("Salvo!")

    with aba[1]: # REPOSIÇÃO (RESTAURADO SCANNER)
        scanner_pro("cod_rep")
        cod_rep = st.text_input("Código Lido:", key="cod_rep")
        qtd_rep = st.number_input("Qtd a Somar", min_value=0.0)
        if st.button("➕ Confirmar Entrada"):
            p = get_db(f"produtos/{cod_rep}")
            if p:
                save_db(f"produtos/{cod_rep}", {"estoque": p.get('estoque', 0) + qtd_rep})
                st.success("Atualizado!")

    with aba[2]: # BAIXA (RESTAURADO SCANNER)
        scanner_pro("cod_bx")
        cod_bx = st.text_input("Código Lido:", key="cod_bx")
        qtd_bx = st.number_input("Qtd a Retirar", min_value=0.0)
        if st.button("📉 Confirmar Saída"):
            p = get_db(f"produtos/{cod_bx}")
            if p and p['estoque'] >= qtd_bx:
                save_db(f"produtos/{cod_bx}", {"estoque": p['estoque'] - qtd_bx})
                st.warning("Baixa realizada!")

elif menu == "🥗 Nutricionista":
    senha = st.text_input("Senha", type="password")
    if senha == "alvesnutri":
        data_c = st.date_input("Data do Cardápio")
        txt_c = st.text_area("Cardápio")
        txt_f = st.text_area("Retirada")
        if st.button("🚀 PUBLICAR"):
            save_db(f"cardapios/{data_c.strftime('%Y%m%d')}", {"cardapio": txt_c, "ficha": txt_f})
            st.success("Enviado para a cozinha!")

elif menu == "👨‍🍳 Cozinheiro":
    st.header("Cozinha")
    hoje = datetime.now().strftime("%Y%m%d")
    d = get_db(f"cardapios/{hoje}")
    if d:
        st.info(f"**CARDÁPIO DE HOJE:**\n{d['cardapio']}")
        st.success(f"**LISTA DE RETIRADA:**\n{d['ficha']}")
    else:
        st.warning("⚠️ Nenhum cardápio enviado para HOJE. A lista foi limpa automaticamente.")

elif menu == "📚 Histórico":
    st.header("Histórico de Cardápios")
    todos = get_db("cardapios")
    if todos:
        datas = sorted(todos.keys(), reverse=True)
        data_sel = st.selectbox("Escolha uma data", datas)
        item = todos[data_sel]
        st.write(f"**Cardápio:** {item['cardapio']}")
        st.write(f"**Ficha:** {item['ficha']}")

elif menu == "🏷️ Etiquetas":
    e_nome = st.text_input("Produto")
    c1, c2 = st.columns(2)
    e_venc = c1.date_input("Validade")
    e_manip = c2.date_input("Manipulação")
    e_resp = st.text_input("Responsável")
    e_obs = st.selectbox("Armazenamento", ["Refrigeração", "Congelado", "Seco"])
    if st.button("📄 GERAR"):
        st.session_state.p_ok = True
    if st.session_state.get('p_ok'):
        st.markdown(f'<div class="etiqueta-print"><h3>ALVES RESTAURANTE</h3><hr><p><b>PRODUTO:</b> {e_nome.upper()}</p><p><b>VALIDADE:</b> {e_venc.strftime("%d/%m/%Y")}</p><p><b>RESP.:</b> {e_resp.upper()}</p></div>', unsafe_allow_html=True)
        st.markdown('<button onclick="window.print()">IMPRIMIR</button>', unsafe_allow_html=True)

elif menu == "⚠️ Alertas":
    st.header("Alertas de Estoque e Validade")
    prods = get_db("produtos")
    hoje_dt = datetime.now()
    if prods:
        for c, p in prods.items():
            # Alerta de Estoque Baixo
            if p['estoque'] <= p.get('minimo', 0):
                st.error(f"📉 **ESTOQUE BAIXO:** {p['nome']} (Saldo: {p['estoque']})")
            
            # Alerta de Validade (RESTAURADO)
            try:
                venc_dt = datetime.strptime(p['vencimento'], '%Y-%m-%d')
                dias_restantes = (venc_dt - hoje_dt).days
                if dias_restantes <= 7 and dias_restantes >= 0:
                    st.warning(f"⌛ **VENCENDO EM {dias_restantes} DIAS:** {p['nome']} ({venc_dt.strftime('%d/%m/%Y')})")
                elif dias_restantes < 0:
                    st.error(f"❌ **VENCIDO:** {p['nome']} (Venceu em: {venc_dt.strftime('%d/%m/%Y')})")
            except: pass
