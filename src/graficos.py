"""Gráficos Altair dos dois dashboards."""

import altair as alt

from src.constantes import (
    CLASSES,
    COR_FALHA,
    COR_FORA,
    COR_NEUTRA,
    COR_NORMAL,
    COR_TINTA,
    CORES_CLASSE,
    CORES_CORRELACAO,
    ROTULOS,
    ROTULOS_CURTOS,
)
from src.metricas import formatar_numero

ESCALA_CLASSE = alt.Scale(domain=CLASSES, range=CORES_CLASSE)

# Números dos eixos e tooltips no padrão brasileiro (1.000,5), como nos cards
LOCALE_PT_BR = {"number": {"decimal": ",", "thousands": ".", "grouping": [3], "currency": ["R$ ", ""]}}


def em_portugues(grafico):
    return grafico.configure(locale=LOCALE_PT_BR)


# Dashboard 1: correlação e distribuição


def heatmap_correlacao(pares, variaveis, metodo):
    """Mapa de calor do triângulo inferior da matriz de correlação (a matriz é simétrica)."""
    dados = pares.assign(
        rotulo_x=pares["var_x"].map(ROTULOS_CURTOS),
        rotulo_y=pares["var_y"].map(ROTULOS_CURTOS),
        texto=pares["correlacao"].map(lambda r: formatar_numero(r, 2)),
    )
    rotulos = [ROTULOS_CURTOS[v] for v in variaveis]

    base = alt.Chart(dados).encode(
        # A última variável só aparece nas linhas e a primeira só nas colunas
        # labelOverlap=False: os rótulos cabem na largura da célula, e o Vega escondia alguns por precaução
        x=alt.X(
            "rotulo_x:N",
            sort=rotulos[:-1],
            title=None,
            axis=alt.Axis(labelAngle=0, orient="top", labelOverlap=False, labelLimit=80),
        ),
        y=alt.Y("rotulo_y:N", sort=rotulos[1:], title=None),
    )
    celulas = base.mark_rect(stroke="white", strokeWidth=2, cornerRadius=4).encode(
        color=alt.Color(
            "correlacao:Q",
            title=f"Correlação de {metodo}",
            # Interpolação em Lab: o caminho azul -> cinza não passa por tons de roxo/rosa
            scale=alt.Scale(domain=[-1, 0, 1], range=CORES_CORRELACAO, interpolate="lab"),
            legend=alt.Legend(orient="bottom", direction="horizontal", gradientLength=240, titleOrient="top"),
        ),
        tooltip=[
            alt.Tooltip("rotulo_y:N", title="Variável"),
            alt.Tooltip("rotulo_x:N", title="Com"),
            alt.Tooltip("texto:N", title="Correlação"),
        ],
    )
    valores = base.mark_text(fontSize=15, fontWeight=600).encode(
        text="texto:N",
        color=alt.condition("abs(datum.correlacao) > 0.6", alt.value("white"), alt.value(COR_TINTA)),
    )
    # Folga à esquerda: os rótulos do eixo y não são cortados se a fonte do tema carregar depois da medição
    return em_portugues(
        (celulas + valores).properties(height=alt.Step(64), padding={"left": 16, "top": 5, "right": 5, "bottom": 5})
    )


def histograma(dados, var, colorir):
    """Histograma de uma variável, com a mediana marcada (por classe, se colorir=True).

    A legenda das classes fica fora do gráfico, uma vez só acima da grade de histogramas.
    """
    # Bins calculados num transform (e não no encoding): o eixo vira numérico comum, com poucos ticks
    # que não se sobrepõem, em vez de um rótulo por borda de bin
    base = alt.Chart(dados).transform_bin(["inicio", "fim"], var, bin=alt.Bin(maxbins=25))
    eixo_x = alt.X(
        "inicio:Q", title=ROTULOS[var], scale=alt.Scale(zero=False), axis=alt.Axis(tickCount=5, labelOverlap=True)
    )
    eixo_y = alt.Y("count():Q", title="Veículos")
    faixa = [alt.Tooltip("inicio:Q", title="De", format=",.2~f"), alt.Tooltip("fim:Q", title="Até", format=",.2~f")]

    if colorir:
        barras = base.mark_bar(stroke="white", strokeWidth=1).encode(
            x=eixo_x,
            x2="fim:Q",
            y=eixo_y,
            color=alt.Color("status_bateria:N", title="Status", scale=ESCALA_CLASSE, legend=None),
            order=alt.Order("status_bateria:N", sort="descending"),  # Normal embaixo, Falha em cima
            tooltip=[alt.Tooltip("status_bateria:N", title="Status"), *faixa, alt.Tooltip("count():Q", title="Veículos")],
        )
        # Uma linha da cor da classe some sobre a barra da mesma cor: a mediana vira um marcador no topo
        medianas = base.mark_point(shape="triangle-down", filled=True, size=140, stroke="white", strokeWidth=1).encode(
            x=alt.X(f"median({var}):Q"),
            y=alt.value(0),
            color=alt.Color("status_bateria:N", scale=ESCALA_CLASSE, legend=None),
            opacity=alt.value(1),
            tooltip=[
                alt.Tooltip("status_bateria:N", title="Mediana de"),
                alt.Tooltip(f"median({var}):Q", title="Valor", format=",.2~f"),
            ],
        )
    else:
        barras = base.mark_bar(
            color=COR_NEUTRA, stroke="white", strokeWidth=1, cornerRadiusTopLeft=3, cornerRadiusTopRight=3
        ).encode(
            x=eixo_x,
            x2="fim:Q",
            y=eixo_y,
            tooltip=[*faixa, alt.Tooltip("count():Q", title="Veículos")],
        )
        medianas = base.mark_rule(color=COR_TINTA, strokeWidth=2).encode(
            x=alt.X(f"median({var}):Q"),
            tooltip=[alt.Tooltip(f"median({var}):Q", title="Mediana", format=",.2~f")],
        )
    return em_portugues((barras + medianas).properties(height=210))


# Dashboard 2: KPIs com seleção cruzada


def barras_taxa(tabela, campo, ordem, selecao, titulo_categoria, horizontal, taxa_maxima):
    """Taxa de falha por categoria. Clicar numa barra seleciona a categoria.

    `taxa_maxima` fixa o fim do eixo: as taxas ficam perto de 7%, e um eixo até 100% achataria as barras.
    """
    destaque = alt.when(selecao).then(alt.value(1)).otherwise(alt.value(0.35))
    eixo_categoria = alt.X if not horizontal else alt.Y
    eixo_valor = alt.Y if not horizontal else alt.X
    # O título do card já nomeia a categoria; o eixo fica só com os rótulos
    categoria = eixo_categoria(f"{campo}:N", sort=ordem, title=None, axis=alt.Axis(labelAngle=0, labelFontSize=12))
    valor = eixo_valor(
        "taxa:Q",
        title="Taxa de falha",
        scale=alt.Scale(domain=[0, taxa_maxima]),
        axis=alt.Axis(format="%", tickCount=5),
    )
    tooltip = [
        alt.Tooltip(f"{campo}:N", title=titulo_categoria),
        alt.Tooltip("taxa_texto:N", title="Taxa de falha"),
        alt.Tooltip("veiculos:Q", title="Veículos", format=",d"),
        alt.Tooltip("falhas:Q", title="Com falha", format=",d"),
    ]

    canto = {"cornerRadiusTopRight": 4, "cornerRadiusBottomRight": 4} if horizontal else {
        "cornerRadiusTopLeft": 4,
        "cornerRadiusTopRight": 4,
    }
    base = alt.Chart(tabela).encode(categoria, valor, tooltip=tooltip)
    barras = base.mark_bar(color=COR_FALHA, **canto).encode(opacity=destaque).add_params(selecao)
    rotulos = (
        base.mark_text(align="left", dx=6, fontSize=13, color=COR_TINTA)
        if horizontal
        else base.mark_text(baseline="bottom", dy=-6, fontSize=13, color=COR_TINTA)
    ).encode(text="taxa_texto:N")

    tamanho = {"height": alt.Step(44)} if horizontal else {"height": 280}
    return em_portugues((barras + rotulos).properties(**tamanho))


def dispersao_soh_risco(dados, selecao, dominio_soh, dominio_risco):
    """SoH x risco térmico por status. Arrastar uma área seleciona os veículos dentro dela.

    Pontos fora da seleção dos outros gráficos (coluna `no_recorte`) ficam em cinza, como pano de fundo.
    """
    grupos = ["Fora da seleção", "Normal", "Falha"]
    dados = dados.assign(grupo=dados["status_bateria"].where(dados["no_recorte"], "Fora da seleção"))
    # Ordem de desenho: cinza por baixo, depois Normal, e as falhas (7% da base) por cima de tudo
    dados = dados.assign(camada=dados["grupo"].map({g: i for i, g in enumerate(grupos)})).sort_values("camada")

    return em_portugues(
        alt.Chart(dados)
        .mark_circle(size=40, stroke="white", strokeWidth=0.6)
        .encode(
            x=alt.X(
                "state_of_health:Q", title=ROTULOS["state_of_health"], scale=alt.Scale(domain=dominio_soh, nice=False)
            ),
            y=alt.Y(
                "thermal_runaway_risk:Q",
                title=ROTULOS["thermal_runaway_risk"],
                scale=alt.Scale(domain=dominio_risco, nice=False),
            ),
            color=alt.Color(
                "grupo:N",
                title="Status",
                scale=alt.Scale(domain=["Normal", "Falha", "Fora da seleção"], range=[COR_NORMAL, COR_FALHA, COR_FORA]),
                legend=alt.Legend(orient="top"),
            ),
            opacity=alt.when(selecao).then(alt.value(0.85)).otherwise(alt.value(0.2)),
            tooltip=[
                alt.Tooltip("vehicle_id:N", title="Veículo"),
                alt.Tooltip("status_bateria:N", title="Status"),
                alt.Tooltip("state_of_health:Q", title="SoH (%)", format=".1f"),
                alt.Tooltip("thermal_runaway_risk:Q", title="Risco térmico", format=".1f"),
                alt.Tooltip("faixa_idade_veiculo:N", title="Idade do veículo"),
                alt.Tooltip("battery_chemistry:N", title="Química"),
            ],
        )
        .add_params(selecao)
        .properties(height=380)
    )


def dominio_com_folga(serie, folga=0.03):
    """Domínio fixo do eixo (mínimo e máximo da base, com uma pequena folga nas pontas)."""
    minimo, maximo = float(serie.min()), float(serie.max())
    margem = (maximo - minimo) * folga
    return [minimo - margem, maximo + margem]
