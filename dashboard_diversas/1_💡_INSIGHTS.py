import streamlit as st
import os
import pandas as pd
from config.utils import *
import config.config_interface as config_interface
import numpy as np

# Configuração inicial da aplicação
st.set_page_config(page_title="Análise Tabloide Leve +", page_icon=":bar_chart:", layout="wide")


def carregar_dados():
    """Carrega os dados do relatório tratado."""
    return carregar_arquivo_csv(config_interface.CAMINHO_RELATORIO)


def carregar_dados_mensais(data_inicial, data_final):
    """Carrega dinamicamente os arquivos mensais conforme o período selecionado."""
    meses = pd.date_range(start=data_inicial, end=data_final, freq="MS").strftime("%m")
    arquivos_mensais = []
    for mes in meses:
        caminho_arquivo = os.path.join(config_interface.PASTA_TRATADO, f"dado_final-{mes}.csv")
        if os.path.exists(caminho_arquivo):
            arquivos_mensais.append(carregar_arquivo_csv(caminho_arquivo))
    return pd.concat(arquivos_mensais, ignore_index=True) if arquivos_mensais else pd.DataFrame()


def calcular_custos_encarte(dados_filtrados):

    # Filtra todas as promoções relacionadas ao mesmo período
    filtrados = dados_filtrados

    # Dicionário para armazenar os preços por SKU e loja
    preco_por_sku_loja = {}

    for _, linha in filtrados.iterrows():
        sku = linha["SKU"]
        preco_promocional = linha["Preco Venda Promocao"]
        loja = linha["Loja"]

        if sku not in preco_por_sku_loja:
            preco_por_sku_loja[sku] = {}

        preco_por_sku_loja[sku][loja] = {
            "preco_promocional": preco_promocional,
        }

    # Verifica se todos os SKUs têm preços promocionais iguais entre as lojas
    modelo_unico = True
    for sku, lojas in preco_por_sku_loja.items():
        preco_promocional_comum = list(lojas.values())[0]["preco_promocional"]

        for loja, precos in lojas.items():
            if precos["preco_promocional"] != preco_promocional_comum:
                modelo_unico = False
                break

        if not modelo_unico:
            break

    # Define o custo com base no modelo identificado
    custo = 3600 if modelo_unico else 6400
    return custo


def gerar_insights(dados_filtrados, custo_encarte):
    # Quantidade de cupons ativados
    quant_cupons_ativados = dados_filtrados["Num.Cupom"].nunique()

    # Quantidade de itens unicos ativados
    quant_itens_unicos_ativados = dados_filtrados["Familia"].nunique()

    # Quantidade de itens vendidos
    quant_itens_vendidos = dados_filtrados["Quantidade Comprada"].sum()

    # Calcular desconto total
    desconto_total = dados_filtrados["Desconto Total"].sum()

    # Calcular a receita bruta
    receita_bruta = dados_filtrados["Quantidade Comprada"] * dados_filtrados["Preco Venda Promocao"]
    receita_bruta_total = receita_bruta.sum()

    # Calcular Lucro Bruto (dado nao totalmente correto)
    lucro_bruto = (
        dados_filtrados["Preco Venda Promocao"] - dados_filtrados["Custo Produto"]
    ) * dados_filtrados["Quantidade Comprada"]
    lucro_bruto_total = lucro_bruto.sum()

    # Lucro Liquido
    lucro_liquido = lucro_bruto_total - custo_encarte - desconto_total

    # Custo total
    custo_total = desconto_total + custo_encarte

    return (
        quant_cupons_ativados,
        quant_itens_unicos_ativados,
        quant_itens_vendidos,
        desconto_total,
        receita_bruta_total,
        lucro_bruto_total,
        lucro_liquido,
        custo_total,
    )


# Dicionário com os valores mínimos para destacar cada coluna
limiares = {
    "Quantidade Comprada": 2,
    "Desconto Unitario": 3,
    "Percentual Desconto": 20,
    "Desconto Total": 15,
}


# Função para aplicar cores com base no valor da célula
def highlight_values(val, limiar):
    try:
        # Garante que o valor é numérico antes da comparação
        if isinstance(val, (int, float)) and val >= limiar:
            return "background-color: yellow; color: black; font-weight: bold;"
    except:
        pass
    return ""


# Interface do Streamlit
st.title("Análise de Tabloide - Leve Mais")

# Carregar dados do relatório tratado
relatorio_tratado = carregar_dados()
# normalizar as colunas
relatorio_tratado["Nome Promocao"] = relatorio_tratado["Nome Promocao"].astype(str)

relatorio_tratado["SKU"] = relatorio_tratado["SKU"].astype(str)


relatorio_tratado["Data Inicial"] = pd.to_datetime(relatorio_tratado["Data Inicial"])
relatorio_tratado["Data Final"] = pd.to_datetime(relatorio_tratado["Data Final"])


data_minima = relatorio_tratado["Data Inicial"].min()
data_maxima = relatorio_tratado["Data Final"].max()

# Seleção de período
st.subheader("Seleção de Período de Promoção")
col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 1, 2, 1, 0.5, 1, 2])
data_inicial = col1.date_input(
    "Data Inicial",
    min_value=data_minima,
    max_value=data_maxima,
    format="DD/MM/YYYY",
    value=data_minima,
)
data_final = col2.date_input(
    "Data Final",
    min_value=data_minima,
    max_value=data_maxima,
    format="DD/MM/YYYY",
    value=data_maxima,
)

data_inicial = pd.to_datetime(data_inicial)
data_final = pd.to_datetime(data_final)

# Filtrar promoções que COMEÇAM e TERMINAM dentro do período selecionado
promoções_no_periodo = relatorio_tratado[
    (relatorio_tratado["Data Inicial"] >= data_inicial)
    & (relatorio_tratado["Data Final"] <= data_final)
]
# Criar um dropdown com promoções agrupadas pelo período (removendo a loja)
if not promoções_no_periodo.empty:
    promoções_no_periodo["Nome Agrupado"] = promoções_no_periodo["Nome Promocao"].str.extract(
        r"^(TABLOIDE \d+ A \d+)"
    )
    # Adicionar a data inicial e final no formato dd/mm
    promoções_no_periodo["Data Inicial Formatada"] = promoções_no_periodo[
        "Data Inicial"
    ].dt.strftime(
        "%d/%m"
    )  # Ex: "29/07"
    promoções_no_periodo["Data Final Formatada"] = promoções_no_periodo["Data Final"].dt.strftime(
        "%d/%m"
    )  # Ex: "10/08"
    promoções_no_periodo["Ano"] = promoções_no_periodo["Data Inicial"].dt.year  # Ano da promoção

    # Criar a nova coluna com o formato desejado
    promoções_no_periodo["Mês Formatado"] = (
        promoções_no_periodo["Data Inicial Formatada"]
        + " A "
        + promoções_no_periodo["Data Final Formatada"]
        + " - "
        + promoções_no_periodo["Ano"].astype(str)
    )

    # Agora, use a nova coluna "Mês Formatado" para exibir na selectbox
    promoções_no_periodo["Nome Agrupado com Mês"] = (
        promoções_no_periodo["Nome Agrupado"] + " - " + promoções_no_periodo["Mês Formatado"]
    )

    # Cria a lista de promoções únicas para o selectbox, usando 'Nome Agrupado com Mês'
    promoções_unicas = promoções_no_periodo["Nome Agrupado com Mês"].dropna().unique()

    # Exibe o selectbox com o nome e a data formatada
    nome_promocao_selecionada = col3.selectbox("Selecione a Promoção", promoções_unicas)

    # Obter o período exato da promoção selecionada (sem o mês)
    dados_promocao_selecionada = promoções_no_periodo[
        promoções_no_periodo["Nome Agrupado"]
        == nome_promocao_selecionada.split(" - ")[0]  # Remover o mês
    ]

    data_inicial_promocao = dados_promocao_selecionada["Data Inicial"].min()
    data_final_promocao = dados_promocao_selecionada["Data Final"].max()

    # Carregar apenas os cupons do período correto
    dados_mensais = carregar_dados_mensais(data_inicial, data_final)

    dados_mensais["Data Cupom"] = pd.to_datetime(dados_mensais["Data Cupom"])

    dados_filtrados = dados_mensais[
        dados_mensais["Data Cupom"].between((data_inicial_promocao), (data_final_promocao))
    ]

    dados_filtrados["SKU"] = dados_filtrados["SKU"].astype(str)
    dados_filtrados["Num.Cupom"] = dados_filtrados["Num.Cupom"].astype(str)

    # dados mensais para calcular o delta

    # Criar coluna de destaque (🔴 ou 🟢)
    dados_filtrados["Destaque"] = np.where(dados_filtrados["Desconto Unitario"] > 5, "🔴", "🟢")

    # Reorganizar para deixar "Destaque" como a primeira coluna
    dados_filtrados = dados_filtrados[
        ["Destaque"] + [col for col in dados_filtrados.columns if col != "Destaque"]
    ]

    # if "dados_filtrados_promocao" not in st.session_state:
    st.session_state["dados_filtrados_promocao"] = dados_filtrados

    # Função para alternar o estado do dataframe
    def alternar_tabela():
        st.session_state.mostrar_df = not st.session_state.mostrar_df

    # Inicializa o estado para mostrar ou esconder o dataframe
    if "mostrar_df" not in st.session_state:
        st.session_state.mostrar_df = True

    # Nome do botão depende de "mostrar_df"
    botao_nome = "Ocultar Tabela" if st.session_state.mostrar_df else "Mostrar Tabela"
    icone = "🚫" if st.session_state.mostrar_df else "👁️"

    # Criar o botão
    if col1.button(
        f"{botao_nome} {icone}", type="primary", use_container_width=True, on_click=alternar_tabela
    ):
        # Alternar o estado para mostrar/ocultar o dataframe
        st.session_state.mostrar_df = not st.session_state.mostrar_df

    if not dados_filtrados.empty:
        st.subheader(f"Cupons da Promoção {nome_promocao_selecionada}")
        # st.dataframe(
        #     dados_filtrados,
        #     use_container_width=True,
        #     hide_index=True,
        # )

        # Criando o estilo do dataframe
        styled_df = dados_filtrados.style.format(
            {
                "Desconto Total": "R$ {:.2f}",
                "Ativacao Necessaria": "{:.0f}",
                "Preco Venda Promocao": "R$ {:.2f}",
                "Desconto Unitario": "R$ {:.2f}",
                "Percentual Desconto": "{:.2f} %",
                "Custo Produto": "R$ {:.2f}",
                "Margem Produto": "{:.2f} %",
                "Margem Promocao": "{:.2f} %",
            }
        )

        ## Aplicando a coloração para os valores acima do limiar
        for coluna, limiar in limiares.items():
            styled_df = styled_df.applymap(lambda x: highlight_values(x, limiar), subset=[coluna])

        # Exibir o dataframe no Streamlit
        if st.session_state.mostrar_df:
            st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Preco Venda Unidade": st.column_config.NumberColumn(
                        "Preço Unitário", format="R$ %.2f"
                    ),
                    "Quantidade Comprada": st.column_config.NumberColumn(
                        "Qtde Comprada", format="%.2f"
                    ),
                    "Data Cupom": st.column_config.DateColumn("Dia da Compra", format="DD/MM/YYYY"),
                    "Familia": st.column_config.TextColumn("Item"),
                },
            )

        custo_encarte = calcular_custos_encarte(dados_filtrados)

        (
            quant_cupons_ativados,
            quant_itens_unicos_ativados,
            quant_itens_vendidos,
            desconto_total,
            receita_bruta_total,
            lucro_bruto_total,
            lucro_liquido,
            custo_total,
        ) = gerar_insights(dados_filtrados, custo_encarte)

        meta_lucro = custo_total * 1.2  # Garante que a meta é positiva

        st.subheader("Insights da Promoção")
        col1, col2, col3, col4 = st.columns([0.5, 0.5, 0.5, 0.5])

        col1.metric("Nº Cupons Ativados", formatar_inteiro(quant_cupons_ativados))

        col1.metric("Nº Itens Ativados", formatar_inteiro(quant_itens_unicos_ativados))

        col1.metric("Quant. Itens Vend.", formatar_float(quant_itens_vendidos))

        col2.metric("Total Desconto 💲", formatar_moeda(desconto_total))

        col2.metric("Custo Tabloide 📰", formatar_moeda(custo_encarte))

        col2.metric("Custo da Promoção 🛍️", formatar_moeda(custo_total))

        col3.metric("Receita Bruta 📈", formatar_moeda(receita_bruta_total))

        col3.metric("Lucro Bruto 📈", formatar_moeda(lucro_bruto_total))

        # Corrigir a lógica do delta
        delta = lucro_liquido - meta_lucro

        icone_lucro = "📉" if delta < 0 else "📈"

        col4.metric("Meta de Lucro Líquido 📈", formatar_moeda(meta_lucro))
        col4.metric(
            f"Lucro Líquido {icone_lucro}",  # Ajusta o ícone dinamicamente
            formatar_moeda(lucro_liquido),
            delta=formatar_moeda(delta, simbolo=False),
        )
        if lucro_liquido >= custo_total:
            superavit = lucro_liquido - custo_total
            st.success(
                f"O lucro líquido cobriu o custo total da promoção. Arrecadou {formatar_moeda(superavit)} "
                f"({(lucro_liquido / custo_total - 1) * 100:.2f}% a mais que o custo)."
            )

        else:
            deficit = custo_total - lucro_liquido
            st.error(
                f"O lucro líquido não cobriu o custo total. Faltaram {formatar_moeda(deficit)} ({abs((lucro_liquido / custo_total - 1)) * 100:.2f}%)."
            )

    else:
        st.warning("Nenhum cupom encontrado para o período selecionado.")

else:
    st.warning("Nenhuma promoção disponível no período selecionado.")
