import streamlit as st
import requests
import json
from datetime import datetime
import streamlit.components.v1 as components

# --- CONFIGURAÇÃO DO FIREBASE ---
URL_BASE = "https://restaurante-alves-default-rtdb.firebaseio.com/"

st.set_page_config(page_title="Alves Gestão Mobile", page_icon="🍱", layout="centered")

# --- COMPONENTE DE SCANNER MELHORADO ---
def scanner_pro(key):
    scanner_html = f"""
    <div style="background: #eee; padding: 10px; border-radius: 10px;">
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
        }}
        
        // Configuração focada em câmera traseira e códigos de barra (EAN/CODE128)
        const html5QrCode = new Html5Qrcode("reader-{key}");
        const config = {{ 
            fps: 15, 
            qrbox: {{ width: 300, height: 150 }},
            aspectRatio: 1.0
        }};

        // Inicia automaticamente tentando a câmera traseira
        html5QrCode.start(
            {{ facingMode: "environment" }}, 
            config, 
            onScanSuccess
        ).catch(err => console.log("Erro ao iniciar camera", err));
    </script>
    """
    return components.html(scanner_html, height=420)

# --- ESTILIZAÇÃO MODERNA ---
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    .welcome-card { 
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
        padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px;
    }
    .stButton>button { width: 100%; border-radius: 12px; height: 50px; font-weight: bold; background-color: #1e3c72; color: white; border: none; }
    
    @media print {
        body * { visibility: hidden; }
        .etiqueta-print, .etiqueta-print * { visibility: visible; }
        .etiqueta-print { position: absolute; left: 0; top: 0; width: 100%; border: 2px solid black; padding: 15px; }
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
    except: st.error("Erro de conexão.")

# --- NAVEGAÇÃO ---
menu = st.sidebar.selectbox("Menu", ["Início", "📦 Estoque", "🥗 Nutricionista", "👨‍🍳 Cozinheiro", "🏷️ Etiquetas", "⚠️ Alertas", "📚 Histórico"])

if menu == "Início":
    st.markdown('<div class="welcome-card"><h1>ALVES GESTÃO 🍱</h1><p>Sistema Mobile Profissional</p></div>', unsafe_allow_html=True)
    st.info(f"📅 Hoje: {datetime.now().strftime('%d/%m/%Y')}")

elif menu == "📦 Estoque":
    st.header("📦 Gestão de Estoque")
    aba = st.tabs(["Cadastrar", "Reposição", "Baixa"])
    
    with aba[0]: # CADASTRO
        st.subheader("📷 Ler Novo Produto")
        scanner_pro("cod_cad")
        cod = st.text_input("Código Detectado:", key="cod_cad")
        nome = st.text_input("Nome do Produto")
        c1, c2 = st.columns(2)
        preco = c1.number_input("Preço", min_value=0.0)
        unid = c2.selectbox("Unid", ["UN", "KG", "L", "CX"])
        est_ini = c1.number_input("Estoque Inicial", min_value=0.0)
        est_min = c2.number_input("Mínimo", min_value=0.0)
        venc = st.date_input("Vencimento")
        if st.button("💾 SALVAR PRODUTO"):
            if cod and nome:
                save_db(f"produtos/{cod}", {"nome": nome, "preco": preco, "medida": unid, "estoque": est_ini, "minimo": est_min, "vencimento": str(venc)})
                st.success("Salvo!")

    with aba[1]: # REPOSIÇÃO
        st.subheader("📷 Scanner para Entrada")
        scanner_pro("cod_rep")
        cod_rep = st.text_input("Código Lido:", key="cod_rep")
        qtd_rep = st.number_input("Quantidade a Adicionar", min_value=0.0)
        if st.button("➕ Confirmar Reposição"):
            p = get_db(f"produtos/{cod_rep}")
            if p:
                save_db(f"produtos/{cod_rep}", {"estoque": p.get('estoque', 0) + qtd_rep})
                st.success("Estoque Atualizado!")
            else: st.error("Produto não encontrado.")

    with aba[2]: # BAIXA
        st.subheader("📷 Scanner para Saída")
        scanner_pro("cod_bx")
        cod_bx = st.text_input("Código Lido:", key="cod_bx")
        qtd_bx = st.number_input("Quantidade a Retirar", min_value=0.0)
        if st.button("📉 Confirmar Baixa"):
            p = get_db(f"produtos/{cod_bx}")
            if p and p['estoque'] >= qtd_bx:
                save_db(f"produtos/{cod_bx}", {"estoque": p['estoque'] - qtd_bx})
                st.warning("Baixa realizada!")
            else: st.error("Saldo insuficiente.")

elif menu == "🥗 Nutricionista":
    senha = st.text_input("Senha", type="password")
    if senha == "alvesnutri":
        data_c = st.date_input("Data do Cardápio")
        txt_c = st.text_area("O que será servido?")
        txt_f = st.text_area("Lista de ingredientes (Baixa)")
        if st.button("🚀 PUBLICAR"):
            save_db(f"cardapios/{data_c.strftime('%Y%m%d')}", {"cardapio": txt_c, "ficha": txt_f})
            st.success("Cardápio enviado!")

elif menu == "👨‍🍳 Cozinheiro":
    st.header("👨‍🍳 Painel da Cozinha")
    hoje = datetime.now().strftime("%Y%m%d")
    d = get_db(f"cardapios/{hoje}")
    if d:
        st.info(f"**CARDÁPIO DO DIA:**\n{d['cardapio']}")
        st.success(f"**LISTA DE RETIRADA:**\n{d['ficha']}")
    else:
        st.warning("⚠️ Nenhum cardápio para hoje. A tela está limpa.")

elif menu == "📚 Histórico":
    st.header("📚 Cardápios Anteriores")
    todos = get_db("cardapios")
    if todos:
        datas = sorted(todos.keys(), reverse=True)
        data_sel = st.selectbox("Selecione a Data", datas)
        item = todos[data_sel]
        st.write(f"**Cardápio:** {item['cardapio']}")
        st.write(f"**Ficha de Retirada:** {item['ficha']}")

elif menu == "🏷️ Etiquetas":
    st.header("🏷️ Gerar Etiqueta")
    e_nome = st.text_input("Produto")
    c1, c2 = st.columns(2)
    e_venc = c1.date_input("Validade")
    e_manip = c2.date_input("Manipulação")
    e_resp = st.text_input("Responsável")
    e_obs = st.selectbox("Conservação", ["Refrigeração", "Congelado", "Seco"])
    if st.button("📄 GERAR ETIQUETA"):
        st.session_state.p_ok = True
    if st.session_state.get('p_ok'):
        st.markdown(f"""
            <div class="etiqueta-print" style="border: 2px solid black; padding: 15px; background: white; color: black; font-family: Arial;">
                <h3 style="text-align: center; margin: 0;">RESTAURANTE ALVES</h3>
                <hr style="border: 1px solid black;">
                <p><b>PRODUTO:</b> {e_nome.upper()}</p>
                <p><b>VALIDADE:</b> {e_venc.strftime('%d/%m/%Y')} | <b>MANIP.:</b> {e_manip.strftime('%d/%m/%Y')}</p>
                <p><b>RESPONSÁVEL:</b> {e_resp.upper()}</p>
                <p><b>CONSERVAÇÃO:</b> {e_obs.upper()}</p>
            </div>
            <br>
            <button onclick="window.print()" style="width:100%; height:50px; background-color:#1e3c72; color:white; border-radius:12px; font-weight:bold; cursor:pointer;">🖨️ IMPRIMIR ETIQUETA</button>
        """, unsafe_allow_html=True)

elif menu == "⚠️ Alertas":
    st.header("⚠️ Alertas Críticos")
    prods = get_db("produtos")
    hoje_dt = datetime.now()
    if prods:
        for c, p in prods.items():
            # Estoque baixo
            if p['estoque'] <= p.get('minimo', 0):
                st.error(f"📉 **ESTOQUE BAIXO:** {p['nome']} (Saldo: {p['estoque']})")
            
            # Validade (Restaurado)
            try:
                venc_dt = datetime.strptime(p['vencimento'], '%Y-%m-%d')
                dias = (venc_dt - hoje_dt).days
                if 0 <= dias <= 7:
                    st.warning(f"⌛ **VENCENDO EM {dias} DIAS:** {p['nome']} ({venc_dt.strftime('%d/%m/%Y')})")
                elif dias < 0:
                    st.error(f"❌ **VENCIDO:** {p['nome']} (Vencimento: {venc_dt.strftime('%d/%m/%Y')})")
            except: pass
