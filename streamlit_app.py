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
if "id_temp" not in st.session_state: st.session_state.id_temp = ""
if "nome_temp" not in st.session_state: st.session_state.nome_temp = ""
if "cons_temp" not in st.session_state: st.session_state.cons_temp = "Refrigerado"

st.title("ALVES GESTÃO INTEGRADA 🍱🤖")

# --- FUNÇÃO DE LEITURA IA ---
def ler_com_ia(chave_camera):
    foto = st.camera_input("Scanner de IA", key=chave_camera)
    if foto:
        imagem_b64 = base64.b64encode(foto.read()).decode('utf-8')
        url_vision = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_API_KEY}"
        payload = {
            "requests": [{
                "image": {"content": imagem_b64},
                "features": [{"type": "TEXT_DETECTION"}],
                "imageContext": {"languageHints": ["en"]}
            }]
        }
        try:
            res = requests.post(url_vision, json=payload).json()
            texto_bruto = res['responses'][0]['fullTextAnnotation']['text']
            numeros = "".join(filter(str.isdigit, texto_bruto))
            if numeros:
                st.session_state.codigo_lido = numeros
                st.success(f"✅ Detectado: {numeros}")
            else:
                st.warning("Nenhum número detectado.")
        except:
            st.error("Erro na leitura.")

# --- ABAS ---
tab_estoque, tab_alertas, tab_nutri, tab_cozinha, tab_etiquetas = st.tabs([
    "📦 Operações de Estoque", "⚠️ Painel de Alertas", "🍎 Nutricionista", "👨‍🍳 Cozinha", "🏷️ Etiquetas"
])

# ==========================================
# ABA 1: ESTOQUE (AJUSTADO PARA /estoque/LOJA)
# ==========================================
with tab_estoque:
    loja = st.selectbox("🏬 Selecione a Unidade:", ["BRASÍLIA", "ESTRUTURAL", "CAFETERIA"])
    # Agora o prefixo é exatamente o nome em maiúsculo para bater com o PC
    prefixo_loja = loja.upper()
    
    operacao = st.radio("Selecione a Operação:", ["Reposição", "Baixa", "Cadastrar Novo"], horizontal=True)
    ler_com_ia(chave_camera="cam_estoque")
    
    with st.form("form_estoque", clear_on_submit=True):
        if operacao == "Cadastrar Novo":
            c1, c2 = st.columns(2)
            cod = c1.text_input("Código de Barras", value=st.session_state.codigo_lido)
            nome = c2.text_input("Nome do Produto")
            val = c1.text_input("Vencimento (DD/MM/AAAA)")
            preco = c2.number_input("Preço de Venda (R$)", min_value=0.0, format="%.2f")
            unidade = c1.selectbox("Unidade", ["UN", "KG"])
            qtd_ini = c2.number_input("Quantidade Inicial", min_value=0.0)
            min_alerta = st.number_input("Estoque Mínimo para Alerta", value=5.0)
            
        else:
            cod = st.text_input("Código de Barras", value=st.session_state.codigo_lido)
            qtd_operacao = st.number_input("Quantidade", min_value=0.1)

        if st.form_submit_button("CONFIRMAR AÇÃO"):
            # ROTA ATUALIZADA PARA O NOVO PADRÃO
            path = f"estoque/{prefixo_loja}/{cod}"
            sucesso = False
            
            if operacao == "Cadastrar Novo":
                dados = {
                    "nome": nome, 
                    "vencimento": val, 
                    "preco": preco, 
                    "medida": unidade, 
                    "estoque": qtd_ini, 
                    "minimo": min_alerta
                }
                requests.put(f"{URL_BASE}{path}.json", json=dados)
                # Mantém cópia em /produtos apenas se for Brasília para compatibilidade legada
                if prefixo_loja == "BRASÍLIA":
                    requests.put(f"{URL_BASE}produtos/{cod}.json", json=dados)
                st.success(f"Produto Cadastrado em {loja}!")
                sucesso = True
            else:
                res = requests.get(f"{URL_BASE}{path}.json").json()
                # Tenta buscar na pasta antiga caso não ache na nova (específico para Brasília)
                if not res and prefixo_loja == "BRASÍLIA":
                    res = requests.get(f"{URL_BASE}produtos/{cod}.json").json()
                
                if res:
                    novo_total = (res.get('estoque', 0) + qtd_operacao) if operacao == "Reposição" else (res.get('estoque', 0) - qtd_operacao)
                    novo_total = max(0, novo_total)
                    requests.patch(f"{URL_BASE}{path}.json", json={"estoque": novo_total})
                    if prefixo_loja == "BRASÍLIA":
                        requests.patch(f"{URL_BASE}produtos/{cod}.json", json={"estoque": novo_total})
                    st.success(f"Estoque {loja} atualizado: {novo_total}")
                    sucesso = True
                else: 
                    st.error(f"Produto não encontrado em {loja}!")
            
            if sucesso:
                st.session_state.codigo_lido = ""
                st.rerun()

# ==========================================
# ABA 2: ALERTAS (AJUSTADO PARA /estoque/LOJA)
# ==========================================
with tab_alertas:
    loja_alerta = st.selectbox("Ver alertas de:", ["BRASÍLIA", "ESTRUTURAL", "CAFETERIA"], key="alert_loja")
    prefixo_alerta = loja_alerta.upper()
    
    sub1, sub2 = st.tabs(["📉 Estoque Mínimo", "📅 Perto da Validade"])
    
    # Busca da nova pasta de estoque
    produtos = requests.get(f"{URL_BASE}estoque/{prefixo_alerta}.json").json()
    
    # Fallback para Brasília caso a pasta nova ainda esteja vazia
    if not produtos and prefixo_alerta == "BRASÍLIA":
        produtos = requests.get(f"{URL_BASE}produtos.json").json() or {}
    
    if not produtos: produtos = {}

    with sub1:
        for k, v in produtos.items():
            if v and isinstance(v, dict):
                estoque = float(v.get('estoque', 0))
                minimo = float(v.get('minimo', 0))
                if estoque <= minimo:
                    st.error(f"**{v.get('nome', 'Item')}** - Estoque: {estoque} (Mín: {minimo})")

    with sub2:
        hoje = datetime.now()
        for k, v in produtos.items():
            if v and isinstance(v, dict):
                data_v_str = v.get('vencimento') or v.get('validade')
                if data_v_str and data_v_str != "-":
                    try:
                        # Tenta converter os formatos comuns de data
                        for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
                            try:
                                data_v = datetime.strptime(data_v_str, fmt)
                                break
                            except: continue
                        
                        dias_restantes = (data_v - hoje).days
                        if dias_restantes <= 7:
                            st.warning(f"**{v.get('nome')}** vence em {dias_restantes} dias! ({data_v_str})")
                    except: continue

# --- DEMAIS ABAS (MANTIDAS) ---
with tab_nutri:
    if not st.session_state.senha_nutri:
        senha = st.text_input("Senha da Nutricionista", type="password")
        if st.button("Acessar"):
            if senha == "alvesnutri": st.session_state.senha_nutri = True; st.rerun()
    else:
        with st.form("form_nutri", clear_on_submit=True):
            prato = st.text_area("Prato e Descrição do Cardápio", height=150)
            itens_cozinha = st.text_area("Ingredientes para Retirada", height=150)
            if st.form_submit_button("Enviar para Cozinha"):
                requests.put(f"{URL_BASE}cardapio_dia.json", json={"prato": prato, "lista": itens_cozinha, "data": str(datetime.now().date())})
                st.success("Cardápio enviado!")
        if st.button("Sair"): st.session_state.senha_nutri = False; st.rerun()

with tab_cozinha:
    dados_c = requests.get(f"{URL_BASE}cardapio_dia.json").json()
    if dados_c and dados_c.get("data") == str(datetime.now().date()):
        st.info(f"### Cardápio de Hoje: {dados_c['prato']}")
        st.code(dados_c['lista'])
    else: st.write("Aguardando cardápio.")

with tab_etiquetas:
    aba_gerar, aba_historico = st.tabs(["🆕 Gerar/Editar", "🔍 Scanner e Pesquisa"])
    with aba_historico:
        ler_com_ia(chave_camera="cam_etiquetas")
        busca_termo = st.text_input("Pesquisar Produto", value=st.session_state.get('codigo_lido', ""))
        if busca_termo:
            loja_busca = st.selectbox("Buscar na loja:", ["BRASÍLIA", "ESTRUTURAL", "CAFETERIA"])
            todos = requests.get(f"{URL_BASE}estoque/{loja_busca}.json").json() or {}
            for id_p, info in todos.items():
                if info and isinstance(info, dict):
                    if str(busca_termo).lower() in str(id_p).lower() or str(busca_termo).lower() in str(info.get('nome', '')).lower():
                        with st.expander(f"📌 {info.get('nome')} ({loja_busca})"):
                            if st.button(f"USAR DADOS", key=f"hist_{id_p}"):
                                st.session_state['id_temp'] = id_p
                                st.session_state['nome_temp'] = info.get('nome', '')
                                st.rerun()

    with aba_gerar:
        with st.form("form_etq_final", clear_on_submit=True):
            id_final = st.text_input("ID Nº", value=st.session_state.get('id_temp', st.session_state.get('codigo_lido', "")))
            e_nome = st.text_input("Nome", value=st.session_state.get('nome_temp', ''))
            e_qtd = st.text_input("Qtd/Lote")
            e_cons = st.selectbox("Conservação", ["Refrigerado", "Congelado", "Ambiente"])
            e_man = st.date_input("Manipulação", value=datetime.now())
            e_val = st.date_input("Validade")
            gerar = st.form_submit_button("GERAR E IMPRIMIR ETIQUETA")
        if gerar:
            qr_url = f"https://quickchart.io/qr?text={id_final}&size=150"
            etiqueta_html = f"""
                <div style="border: 2px solid #000; padding: 15px; width: 280px; background: white; color: black; font-family: Arial; margin: auto;">
                    <h2 style="margin:0; text-align: center;">ALVES GESTÃO</h2>
                    <hr>
                    <p><b>PRODUTO:</b> {e_nome}</p>
                    <p><b>ID:</b> {id_final} | <b>MANIP.:</b> {e_man.strftime('%d/%m/%Y')}</p>
                    <p><b>VAL.:</b> {e_val.strftime('%d/%m/%Y')}</p>
                    <p><b>QTD:</b> {e_qtd} | <b>CONS.:</b> {e_cons}</p>
                    <div style="text-align: center;"><img src="{qr_url}" style="width: 100px;"></div>
                </div>
                <button style="width:100%; padding:10px; margin-top:10px;" onclick="window.print();">🖨️ Imprimir</button>
            """
            st.components.v1.html(etiqueta_html, height=450)



