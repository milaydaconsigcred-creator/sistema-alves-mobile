import streamlit as st
import requests
import json
from datetime import datetime
from PIL import Image
import cv2
import numpy as np

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Alves Gestão Mobile", 
    page_icon="🍱", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- FORÇAR PEDIDO DE PERMISSÃO DE CÂMERA (PARA APP INSTALADO) ---
st.markdown("""
    <script>
    navigator.mediaDevices.getUserMedia({ video: true })
    .then(function(stream) { console.log("Câmera autorizada"); })
    .catch(function(err) { console.log("Erro de permissão: " + err); });
    </script>
    """, unsafe_allow_html=True)

# --- CONFIGURAÇÃO DO FIREBASE ---
URL_BASE = "https://restaurante-alves-default-rtdb.firebaseio.com/"

# --- FUNÇÃO DE LEITURA DE CÓDIGO POR FOTO (OPENCV) ---
def ler_codigo_da_foto(image_file):
    if image_file is not None:
        try:
            # Converter a foto do Streamlit para formato OpenCV
            file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, 1)
            
            # Detector de código de barras
            detector = cv2.barcode.BarcodeDetector()
            ok, decoded_info, decoded_type, points = detector.detectAndDecode(img)
            
            if ok and decoded_info[0]:
                return decoded_info[0]
            
            # Tentar QR Code se não for barras
            qr_detector = cv2.QRCodeDetector()
            ok_qr, val, _, _ = qr_detector.detectAndDecode(img)
            if ok_qr and val:
                return val
                
            st.error("⚠️ Não consegui ler as barras. Tente tirar a foto de um pouco mais longe ou com mais luz.")
        except Exception as e:
            st.error(f"Erro ao processar imagem: {e}")
    return ""

# --- FUNÇÕES DO BANCO DE DADOS ---
def get_db(path):
    try:
        res = requests.get(f"{URL_BASE}/{path}.json")
        return res.json() if res.status_code == 200 else {}
    except: return {}

def save_db(path, data):
    try: requests.patch(f"{URL_BASE}/{path}.json", data=json.dumps(data))
    except: st.error("Erro ao conectar com o servidor.")

# --- ESTILIZAÇÃO CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    .stButton>button { width: 100%; border-radius: 12px; height: 55px; font-weight: bold; background-color: #1e3c72; color: white; border: none; }
    .etiqueta-print { display: none; }
    @media print {
        header, .stSidebar, .stTabs, button, .stCameraInput { display: none !important; }
        .etiqueta-print { display: block !important; border: 2px solid black; padding: 20px; color: black !important; font-family: Arial; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- NAVEGAÇÃO ---
menu = st.sidebar.selectbox("Menu Principal", ["Início", "📦 Estoque", "🥗 Nutricionista", "👨‍🍳 Cozinheiro", "🏷️ Etiquetas", "⚠️ Alertas", "📚 Histórico"])

if menu == "Início":
    st.title("ALVES GESTÃO 🍱")
    st.info("💡 Dica: Se a câmera não abrir, verifique as permissões do Chrome no seu Android.")

elif menu == "📦 Estoque":
    aba = st.tabs(["Cadastrar", "Reposição", "Baixa"])
    
    for i, nome_aba in enumerate(["cad", "rep", "bx"]):
        with aba[i]:
            st.subheader(f"📷 Scanner de {nome_aba.capitalize()}")
            # Componente de Câmera Oficial
            foto = st.camera_input("Tire foto do código de barras", key=f"cam_{nome_aba}")
            
            codigo_detectado = ""
            if foto:
                codigo_detectado = ler_codigo_da_foto(foto)
                if codigo_detectado:
                    st.success(f"✅ Código identificado: {codigo_detectado}")

            # Campo de Código
            cod = st.text_input("Número do Código:", value=codigo_detectado, key=f"input_{nome_aba}")
            
            if nome_aba == "cad":
                n = st.text_input("Nome do Alimento")
                c1, c2 = st.columns(2)
                est = c1.number_input("Estoque Inicial", min_value=0.0)
                m_est = c2.number_input("Mínimo", min_value=0.0)
                v = st.date_input("Validade")
                if st.button("💾 SALVAR PRODUTO"):
                    if cod and n:
                        save_db(f"produtos/{cod}", {"nome": n, "estoque": est, "minimo": m_est, "vencimento": str(v)})
                        st.success("Produto Cadastrado!")

            elif nome_aba == "rep":
                qtd = st.number_input("Qtd a Adicionar", min_value=0.0)
                if st.button("➕ Confirmar Entrada"):
                    p = get_db(f"produtos/{cod}")
                    if p:
                        save_db(f"produtos/{cod}", {"estoque": p.get('estoque', 0) + qtd})
                        st.success("Estoque Atualizado!")
                    else: st.error("Produto não encontrado!")

            elif nome_aba == "bx":
                qtd = st.number_input("Qtd a Retirar", min_value=0.0)
                if st.button("📉 Confirmar Baixa"):
                    p = get_db(f"produtos/{cod}")
                    if p and p['estoque'] >= qtd:
                        save_db(f"produtos/{cod}", {"estoque": p['estoque'] - qtd})
                        st.warning("Baixa realizada com sucesso!")
                    else: st.error("Saldo insuficiente ou produto não existe.")

elif menu == "🥗 Nutricionista":
    senha = st.text_input("Senha de Acesso", type="password")
    if senha == "alvesnutri":
        data_c = st.date_input("Data do Cardápio")
        txt_c = st.text_area("Descrição do Cardápio")
        txt_f = st.text_area("Ficha Técnica (Itens para baixar)")
        if st.button("🚀 ENVIAR PARA COZINHA"):
            save_db(f"cardapios/{data_c.strftime('%Y%m%d')}", {"cardapio": txt_c, "ficha": txt_f})
            st.success("Cardápio Publicado!")

elif menu == "👨‍🍳 Cozinheiro":
    st.header("👨‍🍳 Painel da Cozinha")
    hoje = datetime.now().strftime("%Y%m%d")
    d = get_db(f"cardapios/{hoje}")
    if d:
        st.info(f"**CARDÁPIO DE HOJE:**\n{d['cardapio']}")
        st.success(f"**LISTA DE RETIRADA:**\n{d['ficha']}")
    else:
        st.warning("⚠️ Lista limpa. Nenhum cardápio enviado para hoje.")

elif menu == "📚 Histórico":
    st.header("📚 Histórico de Cardápios")
    todos = get_db("cardapios")
    if todos:
        datas = sorted(todos.keys(), reverse=True)
        sel = st.selectbox("Selecione a Data", datas)
        st.write(f"**Cardápio:** {todos[sel]['cardapio']}")
        st.write(f"**Ficha:** {todos[sel]['ficha']}")

elif menu == "🏷️ Etiquetas":
    e_nome = st.text_input("Produto")
    c1, c2 = st.columns(2)
    e_venc = c1.date_input("Validade")
    e_manip = c2.date_input("Manipulação")
    e_resp = st.text_input("Responsável")
    if st.button("📄 GERAR ETIQUETA"):
        st.session_state.print_ok = True
    if st.session_state.get('print_ok'):
        st.markdown(f"""
            <div class="etiqueta-print">
                <h2 style="text-align:center">ALVES RESTAURANTE</h2>
                <hr>
                <p><b>PRODUTO:</b> {e_nome.upper()}</p>
                <p><b>VALIDADE:</b> {e_venc.strftime('%d/%m/%Y')}</p>
                <p><b>MANIPULAÇÃO:</b> {e_manip.strftime('%d/%m/%Y')}</p>
                <p><b>RESPONSÁVEL:</b> {e_resp.upper()}</p>
            </div>
            <button onclick="window.print()" style="width:100%; height:50px; background:#1e3c72; color:white; border-radius:10px;">🖨️ IMPRIMIR</button>
        """, unsafe_allow_html=True)

elif menu == "⚠️ Alertas":
    st.header("⚠️ Itens Críticos")
    prods = get_db("produtos")
    hoje_dt = datetime.now()
    if prods:
        for c, p in prods.items():
            # Alerta de Estoque
            if p['estoque'] <= p.get('minimo', 0):
                st.error(f"🚨 **ESTOQUE BAIXO:** {p['nome']} (Saldo: {p['estoque']})")
            # Alerta de Validade
            try:
                v_dt = datetime.strptime(p['vencimento'], '%Y-%m-%d')
                dias = (v_dt - hoje_dt).days
                if 0 <= dias <= 7:
                    st.warning(f"⌛ **VENCENDO EM {dias} DIAS:** {p['nome']} ({v_dt.strftime('%d/%m/%Y')})")
                elif dias < 0:
                    st.error(f"❌ **VENCIDO:** {p['nome']} (Data: {v_dt.strftime('%d/%m/%Y')})")
            except: pass
