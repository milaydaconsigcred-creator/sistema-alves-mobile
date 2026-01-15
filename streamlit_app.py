import streamlit as st
import requests
import json
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DO FIREBASE ---
URL_BASE = "https://restaurante-alves-default-rtdb.firebaseio.com/"

st.set_page_config(page_title="Alves Gestão Mobile", page_icon="🍱", layout="centered")

# --- ESTILIZAÇÃO MODERNA E AJUSTE DE IMPRESSÃO ---
st.markdown("""
    <style>
    /* Estilo Geral */
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 8px; height: 50px; font-weight: bold; background-color: #2e7d32; color: white; border: none; }
    
    /* Card de Boas Vindas */
    .welcome-card { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 30px; border-radius: 15px; color: white; margin-bottom: 20px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
    
    /* Esconder elementos na impressão */
    @media print {
        header, footer, .stSidebar, .stButton, .stTabs, .stMarkdown:not(.etiqueta-print) {
            display: none !important;
        }
        .etiqueta-print {
            display: block !important;
            border: 2px solid #000 !important;
            width: 100% !important;
            position: absolute;
            top: 0;
            left: 0;
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
    except: st.error("Erro de conexão.")

# --- BARRA LATERAL ---
st.sidebar.title("SISTEMA ALVES")
menu = st.sidebar.selectbox("Navegação", 
    ["Início", "📦 Gestão de Estoque", "🥗 Nutricionista", "👨‍🍳 Cozinheiro", "🏷️ Gerador de Etiquetas", "⚠️ Alertas"])

# --- PÁGINA INICIAL MODERNA ---
if menu == "Início":
    st.markdown("""
        <div class="welcome-card">
            <h1>RESTAURANTE ALVES 🍱</h1>
            <p>Gestão Inteligente de Estoque e Produção</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("🏪 **Unidade:** Operação Móvel")
    with col2:
        st.success(f"📅 **Data:** {datetime.now().strftime('%d/%m/%Y')}")

# --- GESTÃO DE ESTOQUE ---
elif menu == "📦 Gestão de Estoque":
    st.header("📦 Estoque")
    aba = st.tabs(["Cadastrar", "Reposição", "Baixa"])

    with aba[0]:
        # O atributo 'autocomplete' ajuda o celular a entender que é um código de barras
        cod = st.text_input("Código de Barras", placeholder="Clique aqui e use o leitor do teclado/câmera", autocomplete="off")
        nome = st.text_input("Nome do Produto")
        col_a, col_b = st.columns(2)
        preco = col_a.number_input("Preço", min_value=0.0)
        unid = col_b.selectbox("Unidade", ["UN", "KG", "L", "CX"])
        est_ini = col_a.number_input("Estoque Inicial", min_value=0.0)
        est_min = col_b.number_input("Mínimo Aviso", min_value=0.0)
        venc = st.date_input("Vencimento")
        
        if st.button("SALVAR PRODUTO"):
            if cod and nome:
                save_db(f"produtos/{cod}", {"nome": nome, "preco": preco, "medida": unid, "estoque": est_ini, "minimo": est_min, "vencimento": str(venc)})
                st.success("Salvo!")

    with aba[1]:
        cod_rep = st.text_input("Código - Reposição", key="cr")
        qtd_rep = st.number_input("Qtd a somar", min_value=0.0)
        if st.button("CONFIRMAR ENTRADA"):
            p = get_db(f"produtos/{cod_rep}")
            if p:
                save_db(f"produtos/{cod_rep}", {"estoque": p.get('estoque', 0) + qtd_rep})
                st.success("Estoque Atualizado!")

    with aba[2]:
        cod_bx = st.text_input("Código - Baixa", key="cb")
        qtd_bx = st.number_input("Qtd a retirar", min_value=0.0)
        if st.button("CONFIRMAR BAIXA"):
            p = get_db(f"produtos/{cod_bx}")
            if p and p['estoque'] >= qtd_bx:
                save_db(f"produtos/{cod_bx}", {"estoque": p['estoque'] - qtd_bx})
                st.warning("Baixa realizada!")

# --- NUTRICIONISTA ---
elif menu == "🥗 Nutricionista":
    senha = st.text_input("Senha de Acesso", type="password")
    if senha == "alvesnutri":
        st.subheader("Planejamento Nutricional")
        data_c = st.date_input("Data")
        txt_c = st.text_area("Cardápio")
        txt_f = st.text_area("Ficha de Retirada (Itens/Qtds)")
        if st.button("PUBLICAR"):
            save_db(f"cardapios/{data_c.strftime('%Y%m%d')}", {"cardapio": txt_c, "ficha": txt_f})
            st.success("Publicado!")

# --- COZINHEIRO ---
elif menu == "👨‍🍳 Cozinheiro":
    st.header("Painel da Cozinha")
    hoje = datetime.now().strftime("%Y%m%d")
    d = get_db(f"cardapios/{hoje}")
    if d:
        st.info(f"**CARDÁPIO:**\n{d['cardapio']}")
        st.success(f"**LISTA DE RETIRADA:**\n{d['ficha']}")
    else: st.write("Aguardando cardápio da nutricionista.")

# --- ETIQUETAS COM CORREÇÃO DE IMPRESSÃO ---
elif menu == "🏷️ Gerador de Etiquetas":
    st.header("🏷️ Etiquetas")
    e_nome = st.text_input("Produto")
    col1, col2 = st.columns(2)
    e_venc = col1.date_input("Validade")
    e_manip = col2.date_input("Manipulação")
    e_resp = st.text_input("Responsável")
    e_obs = st.selectbox("Armazenamento", ["Refrigeração", "Congelado", "Seco"])
    
    if st.button("GERAR ETIQUETA"):
        # Esta div possui a classe 'etiqueta-print' que o CSS usa para isolar na impressão
        st.markdown(f"""
            <div class="etiqueta-print" style="border: 2px solid black; padding: 15px; background: white; color: black; font-family: sans-serif;">
                <h2 style="text-align: center; margin: 0;">RESTAURANTE ALVES</h2>
                <hr style="border: 1px solid black;">
                <p><b>PRODUTO:</b> {e_nome.upper()}</p>
                <p><b>MANIPULADO:</b> {e_manip.strftime('%d/%m/%Y')} | <b>VALIDADE:</b> {e_venc.strftime('%d/%m/%Y')}</p>
                <p><b>RESPONSÁVEL:</b> {e_resp.upper()}</p>
                <p><b>CONSERVAÇÃO:</b> {e_obs.upper()}</p>
            </div>
            <br>
            <p style="color: red;">Para imprimir apenas o quadro acima: use o comando imprimir do navegador (Ctrl+P ou compartilhar -> imprimir).</p>
        """, unsafe_allow_html=True)

# --- ALERTAS ---
elif menu == "⚠️ Alertas":
    st.header("Alertas")
    prods = get_db("produtos")
    if prods:
        st.subheader("🔴 Estoque Baixo")
        for c, p in prods.items():
            if p['estoque'] <= p.get('minimo', 0):
                st.error(f"{p['nome']} (Saldo: {p['estoque']})")

