import streamlit as st
import requests
import json
from datetime import datetime
from PIL import Image
import cv2
import numpy as np

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Alves Gestão Mobile", 
    page_icon="🍱", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. COMANDO DE DESPERTAR CÂMERA (SCRIPT) ---
st.markdown("""
    <script>
    async function ativarCamera() {
        try {
            await navigator.mediaDevices.getUserMedia({ video: true });
            console.log("Câmera Autorizada");
        } catch (err) {
            console.error("Erro na permissão: ", err);
        }
    }
    ativarCamera();
    </script>
    """, unsafe_allow_html=True)

# --- 3. CONFIGURAÇÃO DO FIREBASE ---
URL_BASE = "https://restaurante-alves-default-rtdb.firebaseio.com/"

# --- 4. FUNÇÃO DE LEITURA (OPENCV) ---
def ler_codigo_da_foto(image_file):
    if image_file is not None:
        try:
            file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, 1)
            
            # Tenta ler Código de Barras
            detector = cv2.barcode.BarcodeDetector()
            ok, decoded_info, decoded_type, points = detector.detectAndDecode(img)
            
            if ok and decoded_info[0]:
                if navigator.vibrate: st.write("<script>window.navigator.vibrate(200)</script>", unsafe_allow_html=True)
                return decoded_info[0]
            
            # Tenta QR Code
            qr_detector = cv2.QRCodeDetector()
            ok_qr, val, _, _ = qr_detector.detectAndDecode(img)
            if ok_qr and val:
                return val
                
            st.warning("⚠️ Foto capturada, mas as barras não estão nítidas. Tente focar melhor ou afastar um pouco.")
        except Exception as e:
            st.error(f"Erro no processamento: {e}")
    return ""

# --- 5. FUNÇÕES DE BANCO DE DADOS ---
def get_db(path):
    try:
        res = requests.get(f"{URL_BASE}/{path}.json")
        return res.json() if res.status_code == 200 else {}
    except: return {}

def save_db(path, data):
    try: requests.patch(f"{URL_BASE}/{path}.json", data=json.dumps(data))
    except: st.error("Erro de conexão com o Firebase.")

# --- 6. ESTILO VISUAL (CSS) ---
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

# --- 7. MENU LATERAL ---
st.sidebar.title("🍱 MENU ALVES")
if st.sidebar.button("🔓 LIBERAR CÂMERA"):
    st.markdown("<script>navigator.mediaDevices.getUserMedia({ video: true })</script>", unsafe_allow_html=True)
    st.sidebar.success("Comando enviado! Clique na tela se a mensagem aparecer.")

menu = st.sidebar.selectbox("Ir para:", ["Início", "📦 Estoque", "🥗 Nutricionista", "👨‍🍳 Cozinheiro", "🏷️ Etiquetas", "⚠️ Alertas", "📚 Histórico"])

# --- 8. LÓGICA DAS PÁGINAS ---

if menu == "Início":
    st.title("ALVES GESTÃO 🍱")
    st.success("App Operacional. Se a câmera pedir permissão, clique em 'Allow' ou 'Permitir'.")

elif menu == "📦 Estoque":
    aba = st.tabs(["Cadastrar", "Reposição", "Baixa"])
    
    for i, nome_aba in enumerate(["cad", "rep", "bx"]):
        with aba[i]:
            st.subheader(f"📷 Scanner ({nome_aba.upper()})")
            foto = st.camera_input("Focar Código de Barras", key=f"cam_{nome_aba}")
            
            codigo_detectado = ""
            if foto:
                codigo_detectado = ler_codigo_da_foto(foto)
                if codigo_detectado:
                    st.success(f"✅ Lido: {codigo_detectado}")

            cod = st.text_input("Código:", value=codigo_detectado, key=f"input_{nome_aba}")
            
            if nome_aba == "cad":
                n = st.text_input("Nome do Produto")
                est = st.number_input("Estoque Atual", min_value=0.0)
                m_est = st.number_input("Estoque Mínimo", min_value=0.0)
                v = st.date_input("Vencimento")
                if st.button("💾 SALVAR NOVO"):
                    if cod and n:
                        save_db(f"produtos/{cod}", {"nome": n, "estoque": est, "minimo": m_est, "vencimento": str(v)})
                        st.success("Cadastrado com sucesso!")

            elif nome_aba == "rep":
                qtd = st.number_input("Adicionar quantidade", min_value=0.0)
                if st.button("➕ Confirmar Entrada"):
                    p = get_db(f"produtos/{cod}")
                    if p:
                        save_db(f"produtos/{cod}", {"estoque": p.get('estoque', 0) + qtd})
                        st.success("Estoque Atualizado!")

            elif nome_aba == "bx":
                qtd = st.number_input("Retirar quantidade", min_value=0.0)
                if st.button("📉 Confirmar Baixa"):
                    p = get_db(f"produtos/{cod}")
                    if p and p['estoque'] >= qtd:
                        save_db(f"produtos/{cod}", {"estoque": p['estoque'] - qtd})
                        st.warning("Baixa realizada!")

elif menu == "🥗 Nutricionista":
    senha = st.text_input("Senha", type="password")
    if senha == "alvesnutri":
        data_c = st.date_input("Data do Cardápio")
        txt_c = st.text_area("O que vamos servir?")
        txt_f = st.text_area("Itens para baixa (Ficha técnica)")
        if st.button("🚀 PUBLICAR"):
            save_db(f"cardapios/{data_c.strftime('%Y%m%d')}", {"cardapio": txt_c, "ficha": txt_f})
            st.success("Cardápio enviado para a cozinha!")

elif menu == "👨‍🍳 Cozinheiro":
    st.header("Cozinha")
    hoje = datetime.now().strftime("%Y%m%d")
    d = get_db(f"cardapios/{hoje}")
    if d:
        st.info(f"**CARDÁPIO DO DIA:**\n{d['cardapio']}")
        st.success(f"**LISTA DE RETIRADA:**\n{d['ficha']}")
    else:
        st.warning("Aguardando cardápio de hoje...")

elif menu == "📚 Histórico":
    st.header("Histórico")
    todos = get_db("cardapios")
    if todos:
        datas = sorted(todos.keys(), reverse=True)
        sel = st.selectbox("Selecione uma data anterior", datas)
        st.write(f"**Cardápio:** {todos[sel]['cardapio']}")
        st.write(f"**Ficha:** {todos[sel]['ficha']}")

elif menu == "🏷️ Etiquetas":
    e_nome = st.text_input("Produto")
    c1, c2 = st.columns(2)
    e_venc = c1.date_input("Validade")
    e_manip = c2.date_input("Manipulação")
    e_resp = st.text_input("Responsável")
    if st.button("📄 GERAR"):
        st.session_state.ok_p = True
    if st.session_state.get('ok_p'):
        st.markdown(f'<div class="etiqueta-print"><h3>ALVES RESTAURANTE</h3><hr><p><b>PRODUTO:</b> {e_nome.upper()}</p><p><b>VALIDADE:</b> {e_venc.strftime("%d/%m/%Y")}</p><p><b>RESP.:</b> {e_resp.upper()}</p></div>', unsafe_allow_html=True)
        st.button("🖨️ IMPRIMIR", on_click=lambda: st.write("<script>window.print()</script>", unsafe_allow_html=True))

elif menu == "⚠️ Alertas":
    st.header("Alertas Críticos")
    prods = get_db("produtos")
    hoje_dt = datetime.now()
    if prods:
        for c, p in prods.items():
            if p['estoque'] <= p.get('minimo', 0):
                st.error(f"🚨 ESTOQUE BAIXO: {p['nome']} (Saldo: {p['estoque']})")
            try:
                v_dt = datetime.strptime(p['vencimento'], '%Y-%m-%d')
                dias = (v_dt - hoje_dt).days
                if 0 <= dias <= 7: st.warning(f"⌛ VENCENDO: {p['nome']} em {dias} dias")
                elif dias < 0: st.error(f"❌ VENCIDO: {p['nome']}")
            except: pass


