import pandas as pd
import os
import locale

locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")


def formatar_moeda(valor, simbolo=True):
    """Formata um valor monetário em reais (R$)."""
    return locale.currency(valor, grouping=True, symbol=simbolo)


def formatar_float(valor):
    """Formata um número decimal com separadores brasileiros."""
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_inteiro(valor):
    """Formata um número inteiro com separadores de milhar brasileiros."""
    return format(valor, ",d").replace(",", "X").replace(".", ",").replace("X", ".")


def carregar_arquivo_csv(caminho):
    """Carrega um arquivo CSV, se existir."""
    if os.path.exists(caminho):
        return pd.read_csv(caminho, sep=";", decimal=",")
    return pd.DataFrame()


def carregar_arquivo_excel(caminho):
    """Carrega um arquivo Excel, se existir."""
    if os.path.exists(caminho):
        return pd.read_excel(caminho)
    return pd.DataFrame()
