import streamlit as st
import pandas as pd
import plotly.express as px  # Biblioteca para gráficos interativos

# Dicionário de mapeamento das lojas
mapeamento_lojas = {
    "1": "Espera Feliz 1",
    "2": "Caiana",
    "3": "Divino 1",
    "5": "Alto Jequitibá",
    "6": "Divino 2",
    "8": "Espera Feliz 2",
}


def criar_grafico_barras(
    df, x_col, y_col, titulo, cor_padrao="#b61615", cor_destaque="#09b96d", limite=15
):
    """Cria um gráfico de barras customizado com diferentes limites de destaque para cada métrica."""

    # Definir limites específicos para cada métrica
    limites_destaque = {
        "Quantidade_Vendida": 100,
        "Dias_Ativado": 10,
        "Vezes_Ativado": 20,
        "Faturamento": 5000,
    }

    # Pegar o limite correto para a métrica ou usar um padrão
    limite_destaque = limites_destaque.get(y_col, 50)

    # Selecionar os top `limite` itens
    df_top = df.nlargest(limite, y_col)

    # Criar gráfico
    fig = px.bar(
        df_top,
        x=x_col,
        y=y_col,
        orientation="v",
        title=titulo,
        text_auto=True,
    )

    # Definir cores das barras dinamicamente
    fig.update_traces(
        marker=dict(
            color=[cor_destaque if v >= limite_destaque else cor_padrao for v in df_top[y_col]],
            line=dict(color="black", width=0),
        )
    )

    # Ajustar layout
    fig.update_layout(
        xaxis_title="Itens",
        yaxis_title=y_col.replace("_", " "),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False, zeroline=False, zerolinecolor="gray"),
        title_font=dict(size=25, color="#ffffff"),
    )

    return fig


def criar_grafico_pizza(df, nome_col, valor_col, titulo, limite=15):
    """Cria um gráfico de pizza personalizado com bordas e cores."""

    df_top = df.nlargest(limite, valor_col)

    # Criar o gráfico de pizza
    fig = px.pie(
        df_top,
        names=nome_col,
        values=valor_col,
        title=titulo,
        hole=0.0,  # Criar um efeito de donut (opcional)
    )

    # Personalizar cores
    cores_personalizadas = [
        "#488f31",
        "#5b9938",
        "#6aa040",
        "#7dae48",
        "#89b050",
        "#98b95a",
        "#a7c162",
        "#b6cb6c",
        "#c5d275",
        "#d3dc7f",
        "#e2e489",
        "#fcd983",
        "#f8bc6c",
        "#f49e5c",
        "#d43d51",
    ]

    # Atualizar traços do gráfico (cor, borda)
    fig.update_traces(
        marker=dict(
            colors=cores_personalizadas,  # Aplicar paleta de cores
            line=dict(color="black", width=0),  # Borda preta nos segmentos
        ),
        textinfo="label+percent",  # Mostrar nome e porcentagem no gráfico
    )

    # Personalizar título
    fig.update_layout(
        title=dict(
            text=titulo,
            font=dict(size=25, color="white"),  # Tamanho e cor do título
            x=0,  # ajustar x ou y se quiser
        ),
        legend=dict(
            font=dict(size=14, color="white"),  # Personalizar fonte da legenda
            bgcolor="rgba(0,0,0,0.1)",  # Fundo semi-transparente para a legenda
        ),
        paper_bgcolor="rgba(0,0,0,0)",  # Fundo transparente
        plot_bgcolor="rgba(0,0,0,0)",  # Fundo do gráfico transparente
    )

    return fig


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

# Agrupar por Nome do Item para calcular as métricas
df_resumo = (
    df_filtrado_loja.groupby("Familia")
    .agg(
        Quantidade_Vendida=("Quantidade Comprada", "sum"),
        Dias_Ativado=("Data Cupom", pd.Series.nunique),
        Vezes_Ativado=(
            "Num.Cupom",
            lambda x: (
                df_filtrado_loja.loc[x.index, "Quantidade Comprada"]
                >= df_filtrado_loja.loc[x.index, "Ativacao Necessaria"]
            ).sum(),
        ),
        Faturamento=("Preco Venda Promocao", "sum"),
    )
    .reset_index()
)

# Exibir título
st.title(f"🏬 Análise da Loja {seletor_loja}")

# Criar gráficos para cada métrica

# 📊 Top 15 Itens por Quantidade Vendida
fig1 = criar_grafico_barras(
    df_resumo, "Familia", "Quantidade_Vendida", "📊 Top 15 Itens por Quantidade Vendida"
)
st.plotly_chart(fig1, use_container_width=True)

# 📅 Top 15 Itens por Dias Ativado
fig2 = criar_grafico_barras(
    df_resumo, "Familia", "Dias_Ativado", "📅 Top 15 Itens por Dias Ativado"
)
st.plotly_chart(fig2, use_container_width=True)

# 🔄 Top 15 Itens por Número de Vezes Ativado
fig3 = criar_grafico_barras(
    df_resumo, "Familia", "Vezes_Ativado", "🔄 Top 15 Itens por Número de Vezes Ativado"
)
st.plotly_chart(fig3, use_container_width=True)


fig4 = criar_grafico_pizza(df_resumo, "Familia", "Faturamento", "💰 Top 15 Itens por Faturamento")
st.plotly_chart(fig4, use_container_width=True)
