import streamlit as st
import requests
import json
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DO FIREBASE ---
URL_BASE = "https://restaurante-alves-default-rtdb.firebaseio.com/"

st.set_page_config(page_title="Sistema Alves Mobile", page_icon="📱", layout="centered")

# Funções de Comunicação com o Banco de Dados
def get_db(path):
    try:
        res = requests.get(f"{URL_BASE}/{path}.json")
        return res.json() if res.status_code == 200 else {}
    except:
        return {}

def save_db(path, data):
    try:
        requests.patch(f"{URL_BASE}/{path}.json", data=json.dumps(data))
    except:
        st.error("Erro ao conectar com o banco de dados.")

# Estilização para botões maiores no celular
st.markdown("""
    <style>
    .stButton>button { width: 100%; height: 50px; border-radius: 10px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("RESTAURANTE ALVES 📱")

# Menu Principal Lateral
menu = st.sidebar.selectbox("Escolha o Painel", 
    ["Início", "📦 Gestão de Estoque", "🥗 Nutricionista", "👨‍🍳 Cozinheiro", "🏷️ Gerador de Etiquetas", "⚠️ Alertas"])

# --- TELA INICIAL ---
if menu == "Início":
    st.info("Painel Mobile Integrado. Use o menu lateral para navegar.")
    st.metric("Status do Sistema", "Online")

# --- 1. GESTÃO DE ESTOQUE (ADMIN) ---
elif menu == "📦 Gestão de Estoque":
    st.header("📦 Controle de Estoque")
    aba = st.tabs(["Cadastrar Novo", "Reposição", "Baixa"])

    with aba[0]: # CADASTRAMENTO
        # Dica: No celular, ao clicar aqui, use a função 'Escanear Texto' ou o ícone de câmera do teclado
        cod = st.text_input("Código de Barras", key="cad_cod")
        nome = st.text_input("Nome do Produto")
        preco = st.number_input("Preço Unitário", min_value=0.0, format="%.2f")
        cat = st.selectbox("Categoria", ["Proteínas", "Hortifruti", "Estocáveis", "Limpeza", "Outros"])
        unid = st.selectbox("Unidade", ["UN", "KG", "LITRO", "CX"])
        est_ini = st.number_input("Estoque Inicial", min_value=0.0)
        est_min = st.number_input("Estoque Mínimo (Aviso)", min_value=0.0)
        venc = st.date_input("Data de Vencimento")
        
        if st.button("💾 SALVAR PRODUTO"):
            if cod and nome:
                dados = {
                    "nome": nome, "preco": preco, "categoria": cat, "medida": unid,
                    "estoque": est_ini, "minimo": est_min, "vencimento": str(venc)
                }
                save_db(f"produtos/{cod}", dados)
                st.success(f"Produto {nome} cadastrado!")
            else:
                st.error("Preencha o Código e o Nome!")

    with aba[1]: # REPOSIÇÃO RÁPIDA
        cod_rep = st.text_input("Ler Código para REPOSIÇÃO")
        qtd_rep = st.number_input("Quantidade a ADICIONAR", min_value=0.0)
        if st.button("➕ Confirmar Entrada"):
            prod = get_db(f"produtos/{cod_rep}")
            if prod:
                novo_valor = prod.get('estoque', 0) + qtd_rep
                save_db(f"produtos/{cod_rep}", {"estoque": novo_valor})
                st.success(f"Estoque atualizado: {novo_valor} {prod['medida']}")
            else:
                st.error("Produto não encontrado no sistema!")

    with aba[2]: # BAIXA DE ESTOQUE
        cod_bx = st.text_input("Ler Código para BAIXA")
        qtd_bx = st.number_input("Quantidade a RETIRAR", min_value=0.0)
        if st.button("📉 Confirmar Saída"):
            prod = get_db(f"produtos/{cod_bx}")
            if prod:
                if prod['estoque'] >= qtd_bx:
                    novo_valor = prod['estoque'] - qtd_bx
                    save_db(f"produtos/{cod_bx}", {"estoque": novo_valor})
                    st.warning(f"Baixa registrada! Saldo atual: {novo_valor}")
                else:
                    st.error(f"Saldo insuficiente! Estoque atual: {prod['estoque']}")

# --- 2. NUTRICIONISTA (SENHA: alvesnutri) ---
elif menu == "🥗 Nutricionista":
    senha = st.text_input("Senha da Nutricionista", type="password")
    if senha == "alvesnutri":
        st.header("🥗 Área da Nutricionista")
        data_card = st.date_input("Data do Planejamento")
        txt_cardapio = st.text_area("Descrição do Cardápio (Para o Cozinheiro ver)")
        txt_ficha = st.text_area("Ficha Técnica / Lista de Retirada (Itens e Qtds)")
        
        if st.button("🚀 Publicar Cardápio"):
            path_data = data_card.strftime("%Y%m%d")
            save_db(f"cardapios/{path_data}", {"cardapio": txt_cardapio, "ficha": txt_ficha})
            st.success("Cardápio e Ficha Técnica publicados!")
    elif senha != "":
        st.error("Senha incorreta!")

# --- 3. COZINHEIRO ---
elif menu == "👨‍🍳 Cozinheiro":
    st.header("👨‍🍳 Painel da Cozinha")
    # Busca o cardápio pela data de hoje
    hoje_str = datetime.now().strftime("%Y%m%d")
    dados = get_db(f"cardapios/{hoje_str}")
    
    if dados:
        st.subheader("🍽️ O que cozinhar hoje:")
        st.info(dados.get('cardapio', 'Sem descrição'))
        st.subheader("📝 Lista de Retirada do Estoque:")
        st.success(dados.get('ficha', 'Sem itens listados'))
    else:
        st.warning("A nutricionista ainda não postou o cardápio de hoje.")

# --- 4. ETIQUETAS (DO ZERO) ---
elif menu == "🏷️ Gerador de Etiquetas":
    st.header("🏷️ Cadastro de Etiqueta")
    st.write("Preencha os dados abaixo para gerar a etiqueta de manipulação:")
    
    et_nome = st.text_input("Nome do Alimento/Produto")
    et_venc = st.date_input("Data de Vencimento")
    et_resp = st.text_input("Nome do Responsável")
    et_manip = st.date_input("Data de Manipulação", value=datetime.now())
    et_obs = st.selectbox("Forma de Armazenamento", ["Sob Refrigeração", "Congelado", "Temperatura Ambiente"])
    
    if st.button("🖨️ Visualizar Etiqueta"):
        st.markdown(f"""
        <div style="border: 3px solid black; padding: 15px; background-color: white; color: black; font-family: 'Arial Black';">
            <h2 style="text-align: center; margin: 0;">ALVES RESTAURANTE</h2>
            <hr style="border: 1px solid black;">
            <p style="font-size: 18px;"><b>PRODUTO:</b> {et_nome.upper()}</p>
            <p style="font-size: 16px;"><b>MANIPULADO EM:</b> {et_manip.strftime('%d/%m/%Y')}</p>
            <p style="font-size: 16px;"><b>VALIDADE:</b> {et_venc.strftime('%d/%m/%Y')}</p>
            <p style="font-size: 16px;"><b>RESPONSÁVEL:</b> {et_resp.upper()}</p>
            <p style="font-size: 16px;"><b>ARMAZENAMENTO:</b> {et_obs.upper()}</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("---")
        st.caption("Para imprimir: Use o botão de compartilhar/imprimir do seu navegador celular.")

# --- 5. ALERTAS (ESTOQUE MÍNIMO E VENCIMENTO) ---
elif menu == "⚠️ Alertas":
    st.header("⚠️ Alertas de Estoque e Validade")
    prods = get_db("produtos")
    hoje = datetime.now().date()
    
    if prods:
        # Coluna de Estoque Baixo
        st.subheader("🔴 Itens Acabando (Estoque Crítico)")
        for c, p in prods.items():
            estoque_atual = float(p.get('estoque', 0))
            estoque_min = float(p.get('minimo', 0))
            if estoque_atual <= estoque_min:
                st.error(f"**{p['nome']}** | Tem: {estoque_atual} | Mínimo: {estoque_min}")

        # Coluna de Vencimento
        st.subheader("🟠 Próximos do Vencimento (Próximos 10 dias)")
        for c, p in prods.items():
            try:
                dt_venc = datetime.strptime(p['vencimento'], "%Y-%m-%d").date()
                if dt_venc <= hoje + timedelta(days=10):
                    st.warning(f"**{p['nome']}** | Vence em: {dt_venc.strftime('%d/%m/%Y')}")
            except:
                continue
    else:
        st.write("Nenhum produto cadastrado para análise.")
