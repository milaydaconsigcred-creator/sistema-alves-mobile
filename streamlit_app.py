import streamlit as st
import requests
import json
from datetime import datetime
import streamlit.components.v1 as components

# --- CONFIGURAÇÃO DO FIREBASE ---
URL_BASE = "https://restaurante-alves-default-rtdb.firebaseio.com/"

st.set_page_config(page_title="Alves Gestão Mobile", page_icon="🍱", layout="centered")

# --- FUNÇÃO DO SCANNER JAVASCRIPT MELHORADA ---
def scanner_component(key):
    scanner_html = f"""
    <div id="reader-{key}" style="width: 100%; border-radius: 10px; overflow: hidden;"></div>
    <script src="https://unpkg.com/html5-qrcode"></script>
    <script>
        if (!window.scanner_{key}) {{
            const html5QrcodeScanner = new Html5QrcodeScanner(
                "reader-{key}", {{ fps: 15, qrbox: {{width: 250, height: 150}} }}
            );
            
            function onScanSuccess(decodedText) {{
                // Envia o resultado para o Streamlit
                window.parent.postMessage({{
                    type: 'streamlit:set_widget_value',
                    key: '{key}',
                    value: decodedText
                }}, '*');
            }}
            
            html5QrcodeScanner.render(onScanSuccess);
            window.scanner_{key} = html5QrcodeScanner;
        }}
    </script>
    """
    return components.html(scanner_html, height=380)

# --- ESTILIZAÇÃO ---
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    .stButton>button { width: 100%; border-radius: 12px; height: 50px; font-weight: bold; background-color: #1a2a6c; color: white; }
    .welcome-card { background: linear-gradient(135deg, #1a2a6c, #b21f1f); padding: 20px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px;}
    
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
    except: st.error("Erro ao salvar no banco.")

# --- NAVEGAÇÃO ---
menu = st.sidebar.selectbox("Menu Principal", 
    ["Início", "📦 Gestão de Estoque", "🥗 Nutricionista", "👨‍🍳 Cozinheiro", "🏷️ Gerador de Etiquetas", "⚠️ Alertas"])

if menu == "Início":
    st.markdown('<div class="welcome-card"><h1>ALVES GESTÃO 🍱</h1><p>Controle de Estoque Profissional</p></div>', unsafe_allow_html=True)

elif menu == "📦 Gestão de Estoque":
    st.header("📦 Gestão de Estoque")
    aba = st.tabs(["Cadastrar", "Reposição", "Baixa"])

    with aba[0]:
        st.write("### 📸 Ler Código")
        scanner_component("cod_cad")
        # O valor lido pelo scanner aparece aqui automaticamente
        cod = st.text_input("Código de Barras Detectado:", key="cod_cad")
        
        nome = st.text_input("Nome do Produto")
        c1, c2 = st.columns(2)
        preco = c1.number_input("Preço Unitário", min_value=0.0)
        unid = c2.selectbox("Unidade", ["UN", "KG", "L", "CX"])
        est_ini = c1.number_input("Estoque Inicial", min_value=0.0)
        est_min = c2.number_input("Estoque Mínimo", min_value=0.0)
        venc = st.date_input("Data de Vencimento")
        
        if st.button("💾 SALVAR NOVO PRODUTO"):
            if cod and nome:
                save_db(f"produtos/{cod}", {"nome": nome, "preco": preco, "medida": unid, "estoque": est_ini, "minimo": est_min, "vencimento": str(venc)})
                st.success(f"Produto {nome} cadastrado com sucesso!")

    with aba[1]:
        st.write("### 📸 Scanner de Reposição")
        scanner_component("cod_rep")
        cod_rep = st.text_input("Código Lido:", key="cod_rep")
        qtd_rep = st.number_input("Qtd a Adicionar", min_value=0.0, key="n_rep")
        if st.button("➕ Confirmar Entrada de Estoque"):
            p = get_db(f"produtos/{cod_rep}")
            if p:
                nova_qtd = p.get('estoque', 0) + qtd_rep
                save_db(f"produtos/{cod_rep}", {"estoque": nova_qtd})
                st.success(f"Estoque atualizado: {nova_qtd} {p['medida']}")
            else: st.error("Produto não encontrado!")

    with aba[2]:
        st.write("### 📸 Scanner de Baixa")
        scanner_component("cod_bx")
        cod_bx = st.text_input("Código Lido:", key="cod_bx")
        qtd_bx = st.number_input("Qtd a Retirar", min_value=0.0, key="n_bx")
        if st.button("📉 Confirmar Saída de Estoque"):
            p = get_db(f"produtos/{cod_bx}")
            if p and p['estoque'] >= qtd_bx:
                nova_qtd = p['estoque'] - qtd_bx
                save_db(f"produtos/{cod_bx}", {"estoque": nova_qtd})
                st.warning(f"Baixa realizada! Restam {nova_qtd} no estoque.")
            elif p: st.error("Estoque insuficiente!")

elif menu == "🥗 Nutricionista":
    senha = st.text_input("Senha de Acesso", type="password")
    if senha == "alvesnutri":
        st.subheader("Planejamento Nutricional")
        data_c = st.date_input("Data do Cardápio")
        txt_c = st.text_area("Descrição do Cardápio")
        txt_f = st.text_area("Ficha Técnica / Retirada")
        if st.button("🚀 PUBLICAR PARA COZINHA"):
            save_db(f"cardapios/{data_c.strftime('%Y%m%d')}", {"cardapio": txt_c, "ficha": txt_f})
            st.success("Publicado!")

elif menu == "👨‍🍳 Cozinheiro":
    st.header("👨‍🍳 Painel do Cozinheiro")
    hoje = datetime.now().strftime("%Y%m%d")
    d = get_db(f"cardapios/{hoje}")
    if d:
        st.info(f"**CARDÁPIO DE HOJE:**\n{d['cardapio']}")
        st.success(f"**LISTA DE RETIRADA:**\n{d['ficha']}")
    else: st.warning("A nutricionista ainda não lançou o cardápio de hoje.")

elif menu == "🏷️ Gerador de Etiquetas":
    st.header("🏷️ Gerador de Etiquetas")
    e_nome = st.text_input("Nome do Alimento")
    c1, c2 = st.columns(2)
    e_venc = c1.date_input("Validade")
    e_manip = c2.date_input("Manipulação")
    e_resp = st.text_input("Responsável")
    e_obs = st.selectbox("Armazenamento", ["Refrigeração", "Congelado", "Temperatura Ambiente"])
    
    if st.button("📄 GERAR ETIQUETA"):
        st.session_state.print_ready = True

    if st.session_state.get('print_ready'):
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
                🖨️ IMPRIMIR ETIQUETA
            </button>
        """, unsafe_allow_html=True)

elif menu == "⚠️ Alertas":
    st.header("⚠️ Itens Críticos")
    prods = get_db("produtos")
    if prods:
        for c, p in prods.items():
            if p['estoque'] <= p.get('minimo', 0):
                st.error(f"🚨 **{p['nome']}** | Estoque Atual: {p['estoque']} (Mínimo: {p['minimo']})")
