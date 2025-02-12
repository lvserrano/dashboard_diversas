import streamlit as st
import pandas as pd

# Dicionário de mapeamento das lojas
mapeamento_lojas = {
    "1": "Espera Feliz 1",
    "2": "Caiana",
    "3": "Divino 1",
    "5": "Alto Jequitibá",
    "6": "Divino 2",
    "8": "Espera Feliz 2",
}


# Função para verificar se o dia é véspera de Natal ou Ano Novo
def excluir_domingos(data):
    # Verificar se a data é domingo
    if data.weekday() == 6:
        # Verificar se é 24 de dezembro (véspera de Natal) ou 31 de dezembro (véspera de Ano Novo)
        if data.month == 12 and data.day in [24, 31]:
            return False  # Não excluir o domingo se for véspera de Natal ou Ano Novo
        return True  # Excluir os domingos normais
    return False  # Não excluir se não for domingo


# Criando um dicionário inverso para buscar os códigos das lojas a partir dos nomes
mapeamento_inverso_lojas = {v: k for k, v in mapeamento_lojas.items()}

df = st.session_state["dados_filtrados_promocao"]

# Filtrando apenas as lojas que estão no dataframe atual
lojas_disponiveis = df["Loja"].astype(str).unique()
lojas_nomes = [mapeamento_lojas[loja] for loja in lojas_disponiveis if loja in mapeamento_lojas]

# Selectbox com nomes das lojas
seletor_loja = st.sidebar.selectbox("Lojas: ", lojas_nomes)

# Converter o nome da loja selecionada de volta para o código
codigo_loja = mapeamento_inverso_lojas[seletor_loja]

# Filtrar o dataframe pela loja selecionada
df_filtrado_loja = df[df["Loja"].astype(str) == codigo_loja]

# --- FILTRO POR FAMÍLIA ---
familias_disponiveis = df_filtrado_loja["Familia"].dropna().unique()
familia_selecionada = st.sidebar.selectbox("Selecione a Família: ", familias_disponiveis)

df_filtrado_familia = df_filtrado_loja[df_filtrado_loja["Familia"] == familia_selecionada]

# --- CÁLCULOS ---
df_filtrado_familia["Data Cupom"] = pd.to_datetime(df_filtrado_familia["Data Cupom"])

# Quantidade total vendida
quantidade_total_vendida = df_filtrado_familia["Quantidade Comprada"].sum()

# Quantidade de ativações da promoção
qtd_ativacoes = df_filtrado_familia[
    df_filtrado_familia["Quantidade Comprada"] >= df_filtrado_familia["Ativacao Necessaria"]
]["Num.Cupom"].nunique()

# Dia de maior venda e quantidade vendida nesse dia
vendas_por_dia = df_filtrado_familia.groupby("Data Cupom")["Quantidade Comprada"].sum()
dia_maior_venda = vendas_por_dia.idxmax()
quantidade_dia_maior_venda = vendas_por_dia.max()
dia_semana_maior_venda = dia_maior_venda.strftime("%A")

# Média de venda por dia
media_venda_dia = vendas_por_dia.mean()

# Converter a coluna de data para datetime
df_filtrado_familia["Data Cupom"] = pd.to_datetime(df_filtrado_familia["Data Cupom"])

# Determinar o período total
data_inicio = df["Data Cupom"].min()
data_fim = df["Data Cupom"].max()

# Criar um intervalo de datas entre o primeiro e o último dia
dias_periodo = pd.date_range(start=data_inicio, end=data_fim)

# Filtrar os dias excluindo os domingos (a não ser vésperas de Natal ou Ano Novo)
dias_ativos = [dia for dia in dias_periodo if not excluir_domingos(dia)]


# Contar quantos dias distintos tiveram vendas desse item
dias_com_venda = df_filtrado_familia["Data Cupom"].nunique()

# Calcular o percentual correto
percentual_dias_ativados = (dias_com_venda / len(dias_ativos)) * 100 if len(dias_ativos) > 0 else 0


# Média de variação de vendas diária
variacao_diaria = vendas_por_dia.diff().dropna().abs().mean()

# Variação de vendas entre o primeiro e o último dia
if len(vendas_por_dia) > 1:
    primeiro_dia = vendas_por_dia.iloc[0]
    ultimo_dia = vendas_por_dia.iloc[-1]
    variacao_primeiro_ultimo = (
        ((ultimo_dia - primeiro_dia) / primeiro_dia) * 100 if primeiro_dia > 0 else 0
    )
else:
    variacao_primeiro_ultimo = 0


# --- CÁLCULO DA CURVA ABC COM O DATAFRAME COMPLETO ---
df["faturamento_total"] = df["Quantidade Comprada"] * df["Preco Venda Promocao"]

# Agrupar por Família considerando todos os itens
df_faturamento = (
    df.groupby("Familia")
    .agg(
        quantidade_vendida=("Quantidade Comprada", "sum"),
        faturamento_total=("faturamento_total", "sum"),
    )
    .reset_index()
)

# Ordenar pelo faturamento total em ordem decrescente
df_faturamento = df_faturamento.sort_values(by="faturamento_total", ascending=False)

# Calcular o percentual acumulado de faturamento
df_faturamento["percentual_acumulado"] = (
    df_faturamento["faturamento_total"].cumsum() / df_faturamento["faturamento_total"].sum() * 100
)


# Classificação ABC
def classificar_abc(percentual):
    if percentual <= 80:
        return "A"
    elif percentual <= 95:
        return "B"
    else:
        return "C"


df_faturamento["curva_abc"] = df_faturamento["percentual_acumulado"].apply(classificar_abc)

# Obter a classificação da Curva ABC para a família selecionada
curva_abc_familia = df_faturamento.loc[
    df_faturamento["Familia"] == familia_selecionada, "curva_abc"
].values[0]

# --- EXIBIÇÃO NO DASHBOARD ---
st.title(f"📊 Análise do Item: {familia_selecionada}")

st.write(f"🔹 **Total de Itens Vendidos:** {quantidade_total_vendida:.2f}")
st.write(f"🔹 **Número de Ativações da Promoção:** {qtd_ativacoes}")

col1, col2, col3 = st.columns(3)
col1.write(f"📅 **Dia com Maior Venda:** {dia_maior_venda.strftime('%d/%m/%Y')}")
col2.write(f"📊 **Quantidade Vendida no Dia:** {quantidade_dia_maior_venda:.2f}")
col3.write(f"📆 **Dia da Semana:** {dia_semana_maior_venda}")

st.divider()

# NOVA SEÇÃO: DESEMPENHO
st.header(f"📈 Desempenho do Item: {curva_abc_familia}")

col1, col2, col3, col4 = st.columns(4)
col1.metric("📊 Média Venda por Dia", f"{media_venda_dia:.2f}")
col2.metric("📈 Percentual de Dias Ativados", f"{percentual_dias_ativados:.2f}%")
col3.metric("📉 Média de Variação de Vendas Diária", f"{variacao_diaria:.2f}")
col4.metric("📊 Variação Entre Primeiro e Último Dia", f"{variacao_primeiro_ultimo:.2f}%")

st.divider()

# st.dataframe(df_filtrado_familia, use_container_width=True, hide_index=True)
