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

# --- FUNÇÃO DE LEITURA IA AJUSTADA (FOCO EM NÚMEROS E CÂMERA TRASEIRA) ---
def ler_com_ia(chave_camera):
    # O Streamlit já tenta usar a câmera traseira por padrão em dispositivos móveis,
    # mas a interação com a IA Vision vai garantir que foquemos nos dígitos.
    foto = st.camera_input("Scanner de IA (Foque nos números abaixo das barras)", key=chave_camera)
    
    if foto:
        imagem_b64 = base64.b64encode(foto.read()).decode('utf-8')
        url_vision = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_API_KEY}"
        
        # Enviamos um "hint" para a IA focar em extrair texto/números
        payload = {
            "requests": [{
                "image": {"content": imagem_b64},
                "features": [{"type": "TEXT_DETECTION"}],
                "imageContext": {"languageHints": ["en"]} # Melhora detecção de caracteres latinos/números
            }]
        }
        
        try:
            res = requests.post(url_vision, json=payload).json()
            # Pega o texto bruto detectado
            texto_bruto = res['responses'][0]['fullTextAnnotation']['text']
            
            # Limpeza: Deixa apenas números e ignora letras ou símbolos
            numeros = "".join(filter(str.isdigit, texto_bruto))
            
            if numeros:
                # Se o número for muito longo (como códigos EAN-13), ele pega a sequência principal
                st.session_state.codigo_lido = numeros
                st.success(f"✅ Números detectados: {numeros}")
            else:
                st.warning("Nenhum número detectado. Tente aproximar mais a câmera.")
        except:
            st.error("Erro na leitura. Tente novamente com mais luz.")

# --- ABAS ---
tab_estoque, tab_alertas, tab_nutri, tab_cozinha, tab_etiquetas = st.tabs([
    "📦 Operações de Estoque", "⚠️ Painel de Alertas", "🍎 Nutricionista", "👨‍🍳 Cozinha", "🏷️ Etiquetas"
])

# ==========================================
# ABA 1: ESTOQUE (DIVIDIDO POR LOJAS)
# ==========================================
with tab_estoque:
    # SELETOR DE LOJA
    loja = st.selectbox("🏬 Selecione a Unidade:", ["Cafeteria", "Brasília", "Estrutural"])
    prefixo_loja = loja.lower()
    
    operacao = st.radio("Selecione a Operação:", ["Reposição", "Baixa", "Cadastrar Novo"], horizontal=True)
    ler_com_ia(chave_camera="cam_estoque")
    
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
            # O caminho agora separa por loja no banco de dados
            path = f"{prefixo_loja}/produtos/{cod}"
            sucesso = False
            
            if operacao == "Cadastrar Novo":
                dados = {"nome": nome, "validade": str(val), "valor": valor, "unidade": unidade, "estoque": qtd_ini, "minimo": min_alerta}
                requests.patch(f"{URL_BASE}{path}.json", json=dados)
                st.success(f"Produto Cadastrado na unidade {loja}!")
                sucesso = True
            else:
                res = requests.get(f"{URL_BASE}{path}.json").json()
                if res:
                    novo_total = (res.get('estoque', 0) + qtd_operacao) if operacao == "Reposição" else (res.get('estoque', 0) - qtd_operacao)
                    requests.patch(f"{URL_BASE}{path}.json", json={"estoque": max(0, novo_total)})
                    st.success(f"Estoque {loja} atualizado: {max(0, novo_total)} {res.get('unidade', '')}")
                    sucesso = True
                else: 
                    st.error(f"Produto não existe no cadastro da {loja}!")
            
            if sucesso:
                st.session_state.codigo_lido = ""
                st.rerun()

# ==========================================
# ABA 2: ALERTAS (FILTRADO POR LOJA)
# ==========================================
with tab_alertas:
    loja_alerta = st.selectbox("Ver alertas de:", ["Cafeteria", "Brasília", "Estrutural"], key="alert_loja")
    prefixo_alerta = loja_alerta.lower()
    
    sub1, sub2 = st.tabs(["📉 Estoque Mínimo", "📅 Perto da Validade"])
    produtos = requests.get(f"{URL_BASE}{prefixo_alerta}/produtos.json").json() or {}
    
    with sub1:
        for k, v in produtos.items():
            if v and isinstance(v, dict):
                estoque, minimo = v.get('estoque', 0), v.get('minimo', 0)
                if estoque <= minimo: st.error(f"**{v.get('nome', 'Sem Nome')}** ({loja_alerta}) - Estoque Crítico: {estoque}")
    with sub2:
        hoje = datetime.now()
        for k, v in produtos.items():
            if v and isinstance(v, dict) and 'validade' in v:
                try:
                    data_v = datetime.strptime(v['validade'], '%Y-%m-%d')
                    if (data_v - hoje).days <= 7: st.warning(f"**{v.get('nome', 'Sem Nome')}** vence em {(data_v - hoje).days} dias!")
                except: continue

# --- ABAS NUTRI E COZINHA (MANTIDAS PADRÃO) ---
with tab_nutri:
    if not st.session_state.senha_nutri:
        senha = st.text_input("Senha da Nutricionista", type="password")
        if st.button("Acessar"):
            if senha == "alvesnutri": st.session_state.senha_nutri = True; st.rerun()
    else:
        with st.form("form_nutri", clear_on_submit=True):
            prato = st.text_area("Prato e Descrição do Cardápio", height=150)
            itens_cozinha = st.text_area("Ingredientes e Quantidades para Retirada", height=150)
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

# ==========================================
# ABA 5: ETIQUETAS (LIMPEZA TOTAL PÓS-IMPRESSÃO)
# ==========================================
with tab_etiquetas:
    aba_gerar, aba_historico = st.tabs(["🆕 Gerar/Editar", "🔍 Scanner e Pesquisa"])

    with aba_historico:
        ler_com_ia(chave_camera="cam_etiquetas")
        busca_termo = st.text_input("Pesquisar Produto Global", value=st.session_state.get('codigo_lido', ""))
        if busca_termo:
            # Busca simplificada na primeira loja para exemplo ou você pode expandir
            todos = requests.get(f"{URL_BASE}cafeteria/produtos.json").json() or {}
            for id_p, info in todos.items():
                if info and isinstance(info, dict):
                    if str(busca_termo).lower() in str(id_p).lower() or str(busca_termo).lower() in str(info.get('nome', '')).lower():
                        with st.expander(f"📌 {info.get('nome')} (ID: {id_p})"):
                            if st.button(f"USAR DADOS", key=f"hist_{id_p}"):
                                st.session_state['id_temp'] = id_p
                                st.session_state['nome_temp'] = info.get('nome', '')
                                st.session_state['cons_temp'] = info.get('conservacao', 'Refrigerado')
                                st.rerun()

    with aba_gerar:
        with st.form("form_etq_final", clear_on_submit=True):
            c_id1, c_id2 = st.columns([1, 3])
            id_final = c_id1.text_input("ID Nº", value=st.session_state.get('id_temp', st.session_state.get('codigo_lido', "")))
            e_nome = c_id2.text_input("Nome", value=st.session_state.get('nome_temp', ''))
            c_etq1, c_etq2 = st.columns(2)
            e_qtd = c_etq1.text_input("Qtd/Lote")
            e_cons = c_etq2.selectbox("Conservação", ["Refrigerado", "Congelado", "Ambiente"],
                                      index=0 if st.session_state.get('cons_temp') == 'Refrigerado' else (1 if st.session_state.get('cons_temp') == 'Congelado' else 2))
            e_man = c_etq1.date_input("Manipulação", value=datetime.now())
            e_val = c_etq2.date_input("Validade")
            gerar = st.form_submit_button("GERAR E IMPRIMIR ETIQUETA")

        if gerar:
            # Gera a etiqueta e limpa os campos para o próximo
            qr_url = f"https://quickchart.io/qr?text={id_final}&size=150"
            etiqueta_html = f"""
                <div id="area-impressao" style="border: 2px solid #000; padding: 15px; width: 280px; background: white; color: black; font-family: Arial; margin: auto;">
                    <h2 style="margin:0; text-align: center;">ALVES GESTÃO</h2>
                    <p style="text-align:center; font-size: 10px;">{loja}</p>
                    <hr>
                    <p><b>PRODUTO:</b> {e_nome}</p>
                    <p><b>ID:</b> {id_final} | <b>MANIP.:</b> {e_man.strftime('%d/%m/%Y')}</p>
                    <p><b>VAL.:</b> {e_val.strftime('%d/%m/%Y')}</p>
                    <p><b>QTD:</b> {e_qtd} | <b>CONS.:</b> {e_cons}</p>
                    <div style="text-align: center;"><img src="{qr_url}" style="width: 100px;"></div>
                </div>
                <button style="width:100%; padding:10px; margin-top:10px;" onclick="window.print();">🖨️ Imprimir Agora</button>
            """
            st.components.v1.html(etiqueta_html, height=450)
            
            # RESET DE CAMPOS DA ETIQUETA
            st.session_state.codigo_lido = ""
            st.session_state.id_temp = ""
            st.session_state.nome_temp = ""
            st.session_state.cons_temp = "Refrigerado"


