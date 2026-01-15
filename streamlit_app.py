import streamlit as st
import requests
import json
from datetime import datetime
from PIL import Image
from pyzbar.pyzbar import decode # Biblioteca para ler o código na foto

# --- CONFIGURAÇÃO DO FIREBASE ---
URL_BASE = "https://restaurante-alves-default-rtdb.firebaseio.com/"

st.set_page_config(page_title="Alves Gestão Mobile", page_icon="🍱", layout="centered")

# --- FUNÇÃO PARA LER CÓDIGO DE BARRA DA FOTO ---
def ler_codigo_da_foto(image_file):
    if image_file is not None:
        img = Image.open(image_file)
        detectado = decode(img)
        if detectado:
            return detectado[0].data.decode('utf-8')
        else:
            st.error("❌ Não foi possível ler o código nesta foto. Tente uma mais nítida.")
    return ""

# --- ESTILIZAÇÃO ---
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    .stButton>button { width: 100%; border-radius: 12px; height: 50px; font-weight: bold; background-color: #1e3c72; color: white; }
    @media print {
        header, .stSidebar, .stTabs, button { display: none !important; }
        .etiqueta-print { display: block !important; border: 2px solid black; padding: 20px; color: black !important; }
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
    st.success("Sistema Pronto para Operação")

elif menu == "📦 Estoque":
    aba = st.tabs(["Cadastrar", "Reposição", "Baixa"])
    
    # LÓGICA PARA AS TRÊS ABAS (REPETIDA PARA GARANTIR FUNCIONAMENTO)
    for i, nome_aba in enumerate(["cad", "rep", "bx"]):
        with aba[i]:
            st.subheader(f"📷 Scanner ({nome_aba.upper()})")
            foto = st.camera_input("Tire foto do código de barras", key=f"cam_{nome_aba}")
            
            codigo_detectado = ""
            if foto:
                codigo_detectado = ler_codigo_da_foto(foto)
                if codigo_detectado:
                    st.success(f"✅ Código identificado: {codigo_detectado}")

            # O campo de texto agora é preenchido pela variável codigo_detectado
            cod = st.text_input("Número do Código:", value=codigo_detectado, key=f"input_{nome_aba}")
            
            if nome_aba == "cad":
                n = st.text_input("Nome do Produto")
                est = st.number_input("Estoque Inicial", min_value=0.0)
                min_est = st.number_input("Estoque Mínimo", min_value=0.0)
                v = st.date_input("Validade")
                if st.button("💾 SALVAR PRODUTO"):
                    save_db(f"produtos/{cod}", {"nome": n, "estoque": est, "minimo": min_est, "vencimento": str(v)})
                    st.success("Cadastrado!")
            
            elif nome_aba == "rep":
                qtd = st.number_input("Qtd Adicionar", min_value=0.0)
                if st.button("➕ Confirmar Entrada"):
                    p = get_db(f"produtos/{cod}")
                    if p:
                        save_db(f"produtos/{cod}", {"estoque": p.get('estoque', 0) + qtd})
                        st.success("Estoque aumentado!")
            
            elif nome_aba == "bx":
                qtd = st.number_input("Qtd Retirar", min_value=0.0)
                if st.button("📉 Confirmar Saída"):
                    p = get_db(f"produtos/{cod}")
                    if p and p['estoque'] >= qtd:
                        save_db(f"produtos/{cod}", {"estoque": p['estoque'] - qtd})
                        st.warning("Baixa realizada!")

elif menu == "👨‍🍳 Cozinheiro":
    st.header("Cozinha")
    hoje = datetime.now().strftime("%Y%m%d")
    d = get_db(f"cardapios/{hoje}")
    if d:
        st.info(f"**CARDÁPIO:**\n{d['cardapio']}")
        st.success(f"**RETIRADA:**\n{d['ficha']}")
    else: st.warning("A tela foi limpa. Sem cardápio para hoje.")

elif menu == "📚 Histórico":
    st.header("Histórico")
    todos = get_db("cardapios")
    if todos:
        datas = sorted(todos.keys(), reverse=True)
        sel = st.selectbox("Data", datas)
        st.write(f"**Cardápio:** {todos[sel]['cardapio']}")
        st.write(f"**Ficha:** {todos[sel]['ficha']}")

elif menu == "⚠️ Alertas":
    st.header("Alertas de Estoque e Validade")
    prods = get_db("produtos")
    if prods:
        for c, p in prods.items():
            if p['estoque'] <= p.get('minimo', 0):
                st.error(f"🚨 ESTOQUE BAIXO: {p['nome']} ({p['estoque']})")
            # Validade (Lógica Restaurada)
            try:
                v_dt = datetime.strptime(p['vencimento'], '%Y-%m-%d')
                dias = (v_dt - datetime.now()).days
                if 0 <= dias <= 7: st.warning(f"⌛ VENCENDO: {p['nome']} em {dias} dias")
            except: pass
                

