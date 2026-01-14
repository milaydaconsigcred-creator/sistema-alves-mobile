import streamlit as st
import requests
import json
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DO FIREBASE ---
URL_BASE = "https://restaurante-alves-default-rtdb.firebaseio.com/"

st.set_page_config(page_title="Sistema Alves Mobile", page_icon="360", layout="centered")

# Funções de Comunicação
def get_db(path):
    res = requests.get(f"{URL_BASE}/{path}.json")
    return res.json() if res.status_code == 200 else {}

def save_db(path, data):
    requests.patch(f"{URL_BASE}/{path}.json", data=json.dumps(data))

# --- CSS PARA ESTILO MOBILE ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; height: 50px; border-radius: 10px; font-weight: bold; }
    .status-box { padding: 20px; border-radius: 10px; margin-bottom: 10px; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("RESTAURANTE ALVES 📱")

# Menu Principal
menu = st.sidebar.selectbox("Escolha o Painel", 
    ["Início", "📦 Gestão de Estoque", "🥗 Nutricionista", "👨‍🍳 Cozinheiro", "🏷️ Gerador de Etiquetas", "⚠️ Alertas"])

# --- INÍCIO ---
if menu == "Início":
    st.info("Bem-vindo ao Sistema de Gestão Móvel. Use o menu lateral para navegar.")
    st.metric("Status do Servidor", "Conectado ao Firebase")

# --- 1. GESTÃO DE ESTOQUE (ADMIN) ---
elif menu == "📦 Gestão de Estoque":
    st.header("📦 Controle de Estoque")
    aba = st.tabs(["Cadastrar", "Reposição", "Baixa"])

    with aba[0]: # CADASTRAR NOVO
        cod = st.text_input("Código de Barras (Clique para usar a câmera do celular)")
        nome = st.text_input("Nome do Produto")
        preco = st.number_input("Preço Unitário", min_value=0.0, format="%.2f")
        cat = st.selectbox("Categoria", ["Proteínas", "Hortifruti", "Estocáveis", "Limpeza", "Outros"])
        unid = st.selectbox("Unidade", ["UN", "KG", "LITRO", "CX"])
        est_ini = st.number_input("Estoque Inicial", min_value=0.0)
        est_min = st.number_input("Estoque Mínimo (Aviso)", min_value=0.0)
        venc = st.date_input("Data de Vencimento")
        
        if st.button("💾 SALVAR NOVO PRODUTO"):
            if cod and nome:
                dados = {
                    "nome": nome, "preco": preco, "categoria": cat, "medida": unid,
                    "estoque": est_ini, "minimo": est_min, "vencimento": str(venc)
                }
                save_db(f"produtos/{cod}", dados)
                st.success(f"{nome} cadastrado com sucesso!")
            else: st.error("Preencha Código e Nome!")

    with aba[1]: # REPOSIÇÃO RÁPIDA
        cod_rep = st.text_input("Ler Código para Reposição")
        qtd_rep = st.number_input("Qtd a somar", min_value=0.0)
        if st.button("➕ Confirmar Entrada"):
            prod = get_db(f"produtos/{cod_rep}")
            if prod:
                novo_valor = prod.get('estoque', 0) + qtd_rep
                save_db(f"produtos/{cod_rep}", {"estoque": novo_valor})
                st.success(f"Estoque atualizado: {novo_valor} {prod['medida']}")
            else: st.error("Produto não encontrado!")

    with aba[2]: # BAIXA DE ESTOQUE
        cod_bx = st.text_input("Ler Código para Baixa")
        qtd_bx = st.number_input("Qtd a retirar", min_value=0.0)
        if st.button("📉 Confirmar Saída"):
            prod = get_db(f"produtos/{cod_bx}")
            if prod:
                if prod['estoque'] >= qtd_bx:
                    novo_valor = prod['estoque'] - qtd_bx
                    save_db(f"produtos/{cod_bx}", {"estoque": novo_valor})
                    st.warning(f"Saída registrada! Restam: {novo_valor}")
                else: st.error("Estoque insuficiente!")

# --- 2. ALERTAS ---
elif menu == "⚠️ Alertas":
    st.header("⚠️ Alertas de Estoque")
    prods = get_db("produtos")
    hoje = datetime.now().date()
    
    st.subheader("🔴 Itens Acabando")
    if prods:
        for c, p in prods.items():
            if float(p.get('estoque', 0)) <= float(p.get('minimo', 0)):
                st.error(f"**{p['nome']}** | Tem: {p['estoque']} | Mínimo: {p['minimo']}")

    st.subheader("🟠 Próximo do Vencimento (15 dias)")
    if prods:
        for c, p in prods.items():
            dt_venc = datetime.strptime(p['vencimento'], "%Y-%m-%d").date()
            if dt_venc <= hoje + timedelta(days=15):
                st.warning(f"**{p['nome']}** | Vence em: {dt_venc.strftime('%d/%m/%Y')}")

# --- 3. NUTRICIONISTA ---
elif menu == "🥗 Nutricionista":
    senha = st.text_input("Senha da Nutricionista", type="password")
    if senha == "alvesnutri":
        st.header("🥗 Planejamento de Cardápio")
        data_card = st.date_input("Para qual data?")
        txt_cardapio = st.text_area("Descrição do Cardápio (Ex: Arroz, feijão e frango)")
        txt_ficha = st.text_area("Ficha Técnica / Lista de Retirada (Ex: 2kg de arroz, 1kg de frango)")
        
        if st.button("🚀 Publicar para o Cozinheiro"):
            path_data = data_card.strftime("%Y%m%d")
            save_db(f"cardapios/{path_data}", {"cardapio": txt_cardapio, "ficha": txt_ficha})
            st.success("Cardápio enviado com sucesso!")

# --- 4. COZINHEIRO ---
elif menu == "👨‍🍳 Cozinheiro":
    st.header("👨‍🍳 Painel do Cozinheiro")
    hoje_str = datetime.now().strftime("%Y%m%d")
    dados = get_db(f"cardapios/{hoje_str}")
    
    if dados:
        st.subheader("🍽️ Cardápio do Dia")
        st.info(dados['cardapio'])
        st.subheader("📝 Lista de Retirada (Ingredientes)")
        st.success(dados['ficha'])
    else:
        st.info("Nenhum cardápio cadastrado para hoje.")

# --- 5. ETIQUETAS (CADASTRO DO ZERO) ---
elif menu == "🏷️ Gerador de Etiquetas":
    st.header("🏷️ Nova Etiqueta de Identificação")
    
    with st.container():
        et_nome = st.text_input("Nome do Alimento")
        et_venc = st.date_input("Data de Vencimento Final")
        et_resp = st.text_input("Nome do Responsável")
        et_manip = st.date_input("Data de Manipulação", value=datetime.now())
        et_obs = st.selectbox("Armazenamento", ["Sob Refrigeração", "Congelado", "Temperatura Ambiente"])
        
        if st.button("🖨️ Gerar Etiqueta para Impressão"):
            st.markdown(f"""
            <div style="border: 2px solid black; padding: 10px; background-color: white; color: black; font-family: Arial;">
                <h3 style="text-align: center; margin: 0;">ALVES RESTAURANTE</h3>
                <hr>
                <b>PRODUTO:</b> {et_nome.upper()}<br>
                <b>MANIPULAÇÃO:</b> {et_manip.strftime('%d/%m/%Y')}<br>
                <b>VALIDADE:</b> {et_venc.strftime('%d/%m/%Y')}<br>
                <b>RESPONSÁVEL:</b> {et_resp.upper()}<br>
                <b>CONSERVAÇÃO:</b> {et_obs}
            </div>
            """, unsafe_allow_html=True)
            st.write("---")
            st.caption("Dica: Use a opção 'Imprimir' do seu navegador para enviar para a impressora Bluetooth.")