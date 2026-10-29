"""Cálculos do Dashboard 1 (correlação e distribuição), reaproveitando as decisões da EDA."""

import pandas as pd


def limites_iqr(serie):
    """Limites da regra clássica do IQR: [Q1 - 1,5*IQR, Q3 + 1,5*IQR] (mesma função da EDA)."""
    q1, q3 = serie.quantile([0.25, 0.75])
    iqr = q3 - q1
    return q1 - 1.5 * iqr, q3 + 1.5 * iqr


def remover_outliers_iqr(df, variaveis):
    """Remove as linhas com outlier em qualquer uma das variáveis escolhidas."""
    mascara = pd.Series(True, index=df.index)
    for var in variaveis:
        inicio, fim = limites_iqr(df[var])
        mascara &= df[var].between(inicio, fim)
    return df[mascara]


def correlacao_pares(df, variaveis, metodo):
    """Correlação de cada par de variáveis (triângulo inferior, sem a diagonal), em formato longo."""
    matriz = df[variaveis].corr(method=metodo.lower())
    linhas = [
        {"var_x": var_x, "var_y": var_y, "correlacao": matriz.loc[var_y, var_x]}
        for i, var_y in enumerate(variaveis)
        for var_x in variaveis[:i]
    ]
    return pd.DataFrame(linhas, columns=["var_x", "var_y", "correlacao"])


def intensidade(r):
    """Classificação usada na EDA: |r| < 0,3 fraca; até 0,7 moderada; acima disso forte."""
    if pd.isna(r):
        return "indefinida"
    if abs(r) < 0.3:
        return "fraca"
    if abs(r) <= 0.7:
        return "moderada"
    return "forte"


def comparar_correlacoes(recorte, referencia, variaveis, metodo):
    """Compara a correlação de cada par no recorte com a da amostra sem recorte."""
    pares = correlacao_pares(recorte, variaveis, metodo)
    pares["referencia"] = correlacao_pares(referencia, variaveis, metodo)["correlacao"]
    pares["diferenca"] = pares["correlacao"] - pares["referencia"]
    pares["intensidade"] = pares["correlacao"].map(intensidade)
    return pares.sort_values("correlacao", key=lambda r: r.abs(), ascending=False, na_position="last")


def estatisticas_descritivas(df, variaveis):
    """Tabela descritiva da EDA (Seções 3 e 5): tendência central, dispersão, assimetria e curtose."""
    tabela = df[variaveis].agg(["count", "mean", "median", "std", "min", "max", "skew", "kurt"]).T
    return tabela.rename(
        columns={
            "count": "Veículos",
            "mean": "Média",
            "median": "Mediana",
            "std": "Desvio padrão",
            "min": "Mínimo",
            "max": "Máximo",
            "skew": "Assimetria",
            "kurt": "Curtose",
        }
    )
