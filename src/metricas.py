"""KPIs do Dashboard 2. As fórmulas foram testadas antes em notebooks/metricas-dashboard2.ipynb."""

import math

import pandas as pd


def resumo_kpis(df, limite_risco):
    """Calcula os 4 KPIs do Dashboard 2. Com recorte vazio, as proporções e a mediana viram NaN.

    `limite_risco` é o limite superior do IQR do risco térmico: acima dele o valor é outlier (EDA, Seção 4).
    """
    vazio = df.empty
    return {
        "veiculos": len(df),
        "taxa_falha": math.nan if vazio else df["battery_failure"].mean(),
        "soh_mediano": math.nan if vazio else df["state_of_health"].median(),
        "risco_extremo": math.nan if vazio else (df["thermal_runaway_risk"] > limite_risco).mean(),
    }


def taxa_por_grupo(df, coluna, ordem):
    """Veículos e taxa de falha por categoria, mantendo todas as categorias na ordem dada."""
    tabela = (
        df.groupby(coluna)["battery_failure"]
        .agg(veiculos="size", falhas="sum")
        .reindex(ordem, fill_value=0)
        .rename_axis(coluna)
        .reset_index()
    )
    tabela["taxa"] = tabela["falhas"] / tabela["veiculos"].where(tabela["veiculos"] > 0)
    tabela["taxa_texto"] = tabela["taxa"].map(formatar_pct)
    return tabela


# Formatação no padrão brasileiro (vírgula decimal), usada nos cards e nos rótulos dos gráficos


def formatar_numero(valor, casas=1):
    if pd.isna(valor):
        return "—"
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_pct(valor, casas=1):
    if pd.isna(valor):
        return "—"
    return f"{formatar_numero(valor * 100, casas)}%"


def formatar_delta(atual, base, unidade, escala=1, casas=1):
    """Diferença entre o recorte e a base, com sinal e unidade (ex.: '+8,9 p.p.').

    Devolve também se a diferença é zero (ou indefinida), para o card mostrar o delta em cinza e sem seta.
    """
    if pd.isna(atual) or pd.isna(base):
        return "sem dados", True
    diferenca = round((atual - base) * escala, casas)
    if diferenca == 0:
        return f"0 {unidade}".strip(), True
    sinal = "+" if diferenca > 0 else "-"
    return f"{sinal}{formatar_numero(abs(diferenca), casas)} {unidade}".strip(), False
