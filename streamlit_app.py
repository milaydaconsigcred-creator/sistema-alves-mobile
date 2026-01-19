import streamlit as st
import requests
import json
import base64
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Alves Gestão Total", page_icon="🍱", layout="wide")

GOOGLE_API_KEY = "AIzaSyAGjkY5Ynkgm5U6w81W2BpAdhg5fdOeFdU" 
URL_BASE = "https://restaurante-alves-default-rtdb.firebaseio.com/"

# Inicialização de estados
if "codigo_lido" not in st.session_state: st.session_state.codigo_lido = ""
if "senha_nutri" not in st.session_state: st.session_state.senha_nutri = False

st.title("ALVES GESTÃO INTEGRADA 🍱🤖")

# --- FUNÇÃO DE LEITURA IA ---
def ler_com_ia():
    foto = st.camera_input("Scanner de IA (Foque nos números)")
    if foto:
        imagem_b64 = base64.b64encode(foto.read()).decode('utf-8')
        url_vision = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_API_KEY}"
        payload = {"requests": [{"image": {"content": imagem_b64}, "features": [{"type": "TEXT_DETECTION"}]}]}
        try:
            res = requests.post(url_vision, json=payload).json()
            texto = res['responses'][0]['fullTextAnnotation']['text']
            numeros = "".join(filter(str.isdigit, texto))
            if numeros:
                st.session_state.codigo_lido = numeros
                st.success(f"Código Identificado: {numeros}")
        except:
            st.error("Erro na leitura. Digite manualmente se necessário.")

# --- ABAS ---
tab_estoque, tab_alertas, tab_nutri, tab_cozinha, tab_etiquetas = st.tabs([
    "📦 Operações de Estoque", "⚠️ Painel de Alertas", "🍎 Nutricionista", "👨‍🍳 Cozinha", "🏷️ Etiquetas"
])

# ==========================================
# ABA 1: ESTOQUE (SEPARADO)
# ==========================================
with tab_estoque:
    operacao = st.radio("Selecione a Operação:", ["Reposição", "Baixa", "Cadastrar Novo"], horizontal=True)
    ler_com_ia()
    
    with st.form("form_estoque", clear_on_submit=True):
        if operacao == "Cadastrar Novo":
            c1, c2 = st.columns(2)
            cod = c1.text_input("Código de Barras", value=st.session_state.codigo_lido)
            nome = c2.text_input("Nome do Produto")
            val = c1.date_input("Data de Validade")
            valor = c2.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            unidade = c1.selectbox("Unidade", ["Kg", "Unidade", "Litro", "Caixa"])
            qtd_ini = c2.number_input("Quantidade Inicial", min_value=0.0)
            min_alerta = st.number_input("Estoque Mínimo para Alerta", value=5.0)
            
        elif operacao == "Baixa":
            cod = st.text_input("Código para Baixa", value=st.session_state.codigo_lido)
            qtd_operacao = st.number_input("Quantidade a retirar", min_value=0.1)
            
        else: # Reposição
            cod = st.text_input("Código para Reposição", value=st.session_state.codigo_lido)
            qtd_operacao = st.number_input("Quantidade a repor", min_value=0.1)

        if st.form_submit_button("CONFIRMAR AÇÃO"):
            path = f"produtos/{cod}"
            if operacao == "Cadastrar Novo":
                dados = {"nome": nome, "validade": str(val), "valor": valor, "unidade": unidade, "estoque": qtd_ini, "minimo": min_alerta}
                requests.patch(f"{URL_BASE}{path}.json", json=dados)
                st.success("Produto Cadastrado!")
            else:
                res = requests.get(f"{URL_BASE}{path}.json").json()
                if res:
                    novo_total = (res['estoque'] + qtd_operacao) if operacao == "Reposição" else (res['estoque'] - qtd_operacao)
                    requests.patch(f"{URL_BASE}{path}.json", json={"estoque": max(0, novo_total)})
                    st.success(f"Estoque atualizado: {max(0, novo_total)} {res.get('unidade', '')}")
                else: st.error("Produto não existe no cadastro!")
            st.session_state.codigo_lido = ""

# ==========================================
# ABA 2: ALERTAS (SUB-ABAS)
# ==========================================
with tab_alertas:
    sub1, sub2 = st.tabs(["📉 Estoque Mínimo", "📅 Perto da Validade"])
    produtos = requests.get(f"{URL_BASE}produtos.json").json() or {}
    
    with sub1:
        for k, v in produtos.items():
            if v.get('estoque', 0) <= v.get('minimo', 0):
                st.error(f"**{v['nome']}** - Estoque Crítico: {v['estoque']} {v['unidade']}")
                
    with sub2:
        hoje = datetime.now()
        for k, v in produtos.items():
            if 'validade' in v:
                data_v = datetime.strptime(v['validade'], '%Y-%m-%d')
                if (data_v - hoje).days <= 7:
                    st.warning(f"**{v['nome']}** vence em {(data_v - hoje).days} dias! ({v['validade']})")

# ==========================================
# ABA 3: NUTRICIONISTA (SENHA E CARDÁPIO)
# ==========================================
with tab_nutri:
    if not st.session_state.senha_nutri:
        senha = st.text_input("Senha da Nutricionista", type="password")
        if st.button("Acessar"):
            if senha == "1234": # Altere sua senha aqui
                st.session_state.senha_nutri = True
                st.rerun()
    else:
        st.subheader("Planejamento Diário")
        with st.form("form_nutri", clear_on_submit=True):
            prato = st.text_input("Prato do Dia")
            itens_cozinha = st.text_area("Ingredientes e Quantidades (ex: 5kg Arroz, 2kg Feijão)")
            if st.form_submit_button("Enviar para Cozinha"):
                requests.put(f"{URL_BASE}cardapio_dia.json", json={"prato": prato, "lista": itens_cozinha, "data": str(datetime.now().date())})
                st.success("Cardápio enviado!")
        if st.button("Sair"): st.session_state.senha_nutri = False; st.rerun()

# ==========================================
# ABA 4: COZINHA
# ==========================================
with tab_cozinha:
    st.subheader("Cardápio Atualizado")
    dados_c = requests.get(f"{URL_BASE}cardapio_dia.json").json()
    if dados_c and dados_c.get("data") == str(datetime.now().date()):
        st.info(f"### Hoje: {dados_c['prato']}")
        st.write("**Lista de Retirada no Estoque:**")
        st.code(dados_c['lista'])
    else: st.write("Aguardando cardápio da nutricionista para hoje.")

# ==========================================
# ABA 5: ETIQUETAS + QR CODE
# ==========================================
with tab_etiquetas:
    with st.form("form_etq", clear_on_submit=True):
        e_nome = st.text_input("Nome do Produto")
        col_e1, col_e2 = st.columns(2)
        e_val = col_e1.date_input("Validade")
        e_man = col_e2.date_input("Data de Manipulação")
        e_qtd = col_e1.text_input("Quantidade/Lote")
        e_cons = col_e2.selectbox("Conservação", ["Refrigerado", "Congelado", "Temperatura Ambiente"])
        gerar = st.form_submit_button("GERAR ETIQUETA")

    if gerar:
        # Gerador de QR Code via API Gratuita (Google Charts)
        qr_data = f"Produto: {e_nome} | Val: {e_val}"
        qr_url = f"https://chart.googleapis.com/chart?chs=150x150&cht=qr&chl={qr_data}"
        
        st.markdown(f"""
            <div style="border: 2px dashed #000; padding: 15px; width: 350px; background: white; color: black; font-family: Arial;">
                <h2 style="margin:0">ALVES GESTÃO</h2>
                <hr>
                <p><b>PRODUTO:</b> {e_nome}</p>
                <p><b>VALIDADE:</b> {e_val.strftime('%d/%m/%Y')} | <b>MANIP.:</b> {e_man.strftime('%d/%m/%Y')}</p>
                <p><b>QTD:</b> {e_qtd} | <b>CONS.:</b> {e_cons}</p>
                <img src="{qr_url}" style="display:block; margin:auto;">
            </div>
        """, unsafe_allow_html=True)

