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
    if data.weekday() == 6:  # Domingo
        if data.month == 12 and data.day in [24, 31]:
            return False  # Manter se for 24 ou 31 de dezembro
        return True  # Excluir domingos normais
    return False  # Manter se não for domingo


# Criando um dicionário inverso para buscar os códigos das lojas a partir dos nomes
mapeamento_inverso_lojas = {v: k for k, v in mapeamento_lojas.items()}

df = st.session_state["dados_filtrados_promocao"]
df["Data Cupom"] = pd.to_datetime(df["Data Cupom"])  # Converter para datetime

# Filtrando apenas as lojas que estão no dataframe atual
lojas_disponiveis = df["Loja"].astype(str).unique()
lojas_nomes = [mapeamento_lojas[loja] for loja in lojas_disponiveis if loja in mapeamento_lojas]

# Selectbox com nomes das lojas
seletor_loja = st.sidebar.selectbox("Lojas: ", lojas_nomes)

# Converter o nome da loja selecionada de volta para o código
codigo_loja = mapeamento_inverso_lojas[seletor_loja]

# Filtrar o dataframe pela loja selecionada
df_filtrado_loja = df[df["Loja"].astype(str) == codigo_loja]

# Determinar o período ativo da promoção
data_inicio = df_filtrado_loja["Data Cupom"].min()
data_fim = df_filtrado_loja["Data Cupom"].max()

# Criar um intervalo de datas sem domingos normais
dias_periodo = pd.date_range(start=data_inicio, end=data_fim)
dias_ativos = [dia for dia in dias_periodo if not excluir_domingos(dia)]
total_dias_ativos = len(dias_ativos)

# Agrupar por Nome do Item para calcular as métricas
df_resumo = (
    df_filtrado_loja.groupby("Familia")
    .agg(
        Quantidade_Vendida=("Quantidade Comprada", "sum"),
        Dias_Ativado=("Data Cupom", pd.Series.nunique),  # Contar dias distintos com venda
        Vezes_Ativado=(
            "Num.Cupom",
            lambda x: (
                df_filtrado_loja.loc[x.index, "Quantidade Comprada"]
                >= df_filtrado_loja.loc[x.index, "Ativacao Necessaria"]
            ).sum(),
        ),
    )
    .reset_index()
)

# Calcular o percentual de dias ativado corretamente
df_resumo["Dias_Ativado %"] = (df_resumo["Dias_Ativado"] / total_dias_ativos * 100).round(2)

# Renomear colunas para exibição
df_resumo = df_resumo.rename(
    columns={
        "Familia": "Nome do Item",
        "Quantidade_Vendida": "Quantidade Vendida",
        "Dias_Ativado": "Quantidade de Dias Ativado",
        "Dias_Ativado %": "Dias Ativado %",
        "Vezes_Ativado": "Vezes Ativado",
    }
)

# Exibir título e dataframe final
st.title(f"🏬 {seletor_loja}")
st.dataframe(
    df_resumo,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Dias Ativado %": st.column_config.ProgressColumn(
            "Dias Ativado %", format="%d", min_value=0, max_value=100
        )
    },
)
