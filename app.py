import altair as alt
import pandas as pd
import streamlit as st

from src import graficos
from src.constantes import (
    COR_FALHA,
    COR_NORMAL,
    ORDEM_FAIXAS,
    ORDEM_QUIMICA,
    ROTULOS,
    ROTULOS_CURTOS,
    USOS,
    VARS_QUANT,
)
from src.data_loader import load_data
from src.estatisticas import comparar_correlacoes, estatisticas_descritivas, remover_outliers_iqr
from src.metricas import formatar_delta, formatar_numero, formatar_pct, resumo_kpis, taxa_por_grupo

# Abaixo disso a correlação fica instável demais para ser interpretada
MIN_VEICULOS_CORRELACAO = 30
# A dispersão desenha uma amostra fixa de pontos; os KPIs e a seleção usam todos os veículos
PONTOS_DISPERSAO = 4000

st.set_page_config(
    page_title="Baterias de VE: correlações e indicadores",
    page_icon=":material/battery_charging_full:",
    layout="wide",
)

df = load_data()


def ler_selecao_pontos(chave, nome, campo):
    """Valores clicados num gráfico de barras (lidos do Session State antes de o gráfico ser desenhado)."""
    estado = st.session_state.get(chave)
    if estado is None:
        return []
    return [item[campo] for item in estado.selection.get(nome, [])]


def ler_selecao_area(chave, nome):
    """Faixas {coluna: [mínimo, máximo]} da área arrastada na dispersão."""
    estado = st.session_state.get(chave)
    if estado is None:
        return {}
    return estado.selection.get(nome, {})


def limpar_selecoes():
    # Trocar a key dos gráficos cria widgets novos, sem seleção
    st.session_state.versao_graficos += 1


# Sidebar: filtros (amostra + Dashboard 1)

with st.sidebar:
    st.header("Filtros")

    usos = st.pills(
        "Tipo de uso",
        list(USOS),
        selection_mode="multi",
        default=list(USOS),
        format_func=USOS.get,
        help="Vale para os dois painéis. Sem nenhuma opção marcada, todos os veículos entram.",
    )

    st.subheader("Painel de correlação e distribuição")

    variaveis = st.multiselect(
        "Variáveis quantitativas",
        VARS_QUANT,
        default=VARS_QUANT,
        format_func=ROTULOS.get,
        help="Quais variáveis entram na matriz de correlação e nos histogramas.",
    )
    variaveis = [var for var in VARS_QUANT if var in variaveis]  # ordem fixa, independente da ordem de clique

    metodo = st.segmented_control(
        "Método de correlação",
        ["Spearman", "Pearson", "Kendall"],
        default="Spearman",
        required=True,
        help="Spearman é o padrão: na EDA nenhuma variável passou no teste de normalidade (Shapiro-Wilk).",
    )

    sem_outliers = st.toggle(
        "Remover outliers (regra do IQR)",
        help="Na EDA os outliers foram mantidos: os valores extremos são justamente os candidatos a falha. "
        "Ligue para ver o que muda sem eles.",
    )
    colorir = st.toggle("Separar por status", help="Colore os histogramas pelo status da bateria (Normal e Falha).")

    # Um slider de intervalo por variável selecionada, para excluir valores da análise
    intervalos = {}
    with st.expander("Intervalo de valores", expanded=True, icon=":material/tune:"):
        if not variaveis:
            st.caption("Selecione variáveis para ajustar os intervalos.")
        for var in variaveis:
            minimo, maximo = float(df[var].min()), float(df[var].max())
            passo, formato = {"cycle_count": (1.0, "%d"), "internal_resistance": (0.01, "%.2f")}.get(var, (0.1, "%.1f"))
            intervalos[var] = st.slider(
                ROTULOS[var],
                min_value=minimo,
                max_value=maximo,
                value=(minimo, maximo),
                step=passo,
                format=formato,
                key=f"intervalo_{var}",
            )

amostra = df[df["fleet_or_private"].isin(usos)] if usos else df

st.title("Saúde de baterias de veículos elétricos")
st.caption(
    f"Correlações e indicadores · EV Battery Health Prediction (Kaggle) · "
    f"{formatar_numero(len(df), 0)} veículos após o tratamento da EDA · "
    f"{formatar_numero(len(amostra), 0)} na amostra com o filtro de uso"
)

aba_correlacao, aba_indicadores = st.tabs(
    [":material/grid_on: Correlação e distribuição", ":material/monitoring: Indicadores"]
)

# Dashboard 1: correlação + distribuição das variáveis quantitativas

recorte_d1 = remover_outliers_iqr(amostra, variaveis) if sem_outliers else amostra
for var, (inicio, fim) in intervalos.items():
    recorte_d1 = recorte_d1[recorte_d1[var].between(inicio, fim)]

with aba_correlacao:
    st.caption(
        f"**{formatar_numero(len(recorte_d1), 0)}** de {formatar_numero(len(amostra), 0)} veículos da amostra "
        f"dentro dos filtros deste painel ({formatar_pct(recorte_d1['battery_failure'].mean())} com falha)."
    )

    col_correlacao, col_distribuicao = st.columns([1, 1.35])

    with col_correlacao, st.container(border=True):
        st.subheader(f"Correlação ({metodo})")

        if len(variaveis) < 2:
            st.info("Selecione pelo menos 2 variáveis para calcular a correlação.", icon=":material/info:")
        elif len(recorte_d1) < MIN_VEICULOS_CORRELACAO:
            st.warning(
                f"Só {len(recorte_d1)} veículo(s) dentro dos filtros: poucos para uma correlação confiável. "
                "Amplie os intervalos.",
                icon=":material/warning:",
            )
        else:
            pares = comparar_correlacoes(recorte_d1, amostra, variaveis, metodo)
            st.altair_chart(
                graficos.heatmap_correlacao(pares, variaveis, metodo),
                alt=f"Mapa de calor da correlação de {metodo} entre as variáveis quantitativas selecionadas",
            )

            mais_forte = pares.iloc[0]
            if pd.isna(mais_forte["correlacao"]):
                st.warning("Alguma variável ficou constante nos filtros e a correlação não pôde ser calculada.")
            else:
                delta, sem_mudanca = formatar_delta(mais_forte["correlacao"], mais_forte["referencia"], "", casas=2)
                st.metric(
                    f"Par mais correlacionado: {ROTULOS_CURTOS[mais_forte['var_y']]} × "
                    f"{ROTULOS_CURTOS[mais_forte['var_x']]}",
                    f"{formatar_numero(mais_forte['correlacao'], 2)} ({mais_forte['intensidade']})",
                    delta,
                    delta_color="off",
                    delta_arrow="off" if sem_mudanca else "auto",
                    delta_description="vs. amostra sem os filtros deste painel",
                    help="Intensidade pela regra da EDA: |r| < 0,3 fraca; até 0,7 moderada; acima disso forte.",
                )

            with st.expander("Todos os pares: filtros deste painel vs. amostra"):
                tabela_pares = pd.DataFrame(
                    {
                        "Par": pares["var_y"].map(ROTULOS_CURTOS) + " × " + pares["var_x"].map(ROTULOS_CURTOS),
                        "Com filtros": pares["correlacao"],
                        "Sem filtros": pares["referencia"],
                        "Diferença": pares["diferenca"],
                        "Intensidade": pares["intensidade"],
                    }
                )
                st.dataframe(
                    tabela_pares,
                    hide_index=True,
                    column_config={
                        col: st.column_config.NumberColumn(format="%.2f")
                        for col in ["Com filtros", "Sem filtros", "Diferença"]
                    },
                    alt="Correlação de cada par de variáveis com e sem os filtros do painel",
                )

    with col_distribuicao, st.container(border=True):
        st.subheader("Distribuição")

        if not variaveis:
            st.info("Selecione pelo menos 1 variável para ver a distribuição.", icon=":material/info:")
        elif recorte_d1.empty:
            st.warning("Nenhum veículo dentro dos filtros. Amplie os intervalos.", icon=":material/warning:")
        else:
            if colorir:
                st.markdown(
                    f':color[■]{{foreground="{COR_NORMAL}"}} Normal   '
                    f':color[■]{{foreground="{COR_FALHA}"}} Falha   '
                    "· ▼ mediana de cada status"
                )
            else:
                st.caption("Linha vertical: mediana do recorte.")

            dados_hist = recorte_d1[variaveis + ["status_bateria"]]
            # Um histograma por variável, em grade de 2 colunas (cada um com a sua escala)
            for inicio in range(0, len(variaveis), 2):
                for coluna, var in zip(st.columns(2), variaveis[inicio : inicio + 2]):
                    with coluna:
                        st.altair_chart(
                            graficos.histograma(dados_hist, var, colorir),
                            alt=f"Histograma de {ROTULOS[var]}",
                        )

            with st.expander("Estatísticas descritivas dos veículos filtrados"):
                st.dataframe(
                    estatisticas_descritivas(recorte_d1, variaveis).rename(index=ROTULOS),
                    column_config={"Veículos": st.column_config.NumberColumn(format="%d")},
                    alt="Média, mediana, dispersão, assimetria e curtose de cada variável selecionada",
                )

# Dashboard 2: KPIs, com seleção cruzada entre os gráficos

if "versao_graficos" not in st.session_state:
    st.session_state.versao_graficos = 0
versao = st.session_state.versao_graficos
CHAVE_FAIXA, CHAVE_QUIMICA, CHAVE_AREA = (f"{nome}_{versao}" for nome in ("faixa", "quimica", "area"))

# Lê as seleções da interação anterior para filtrar KPIs e os outros gráficos
faixas = ler_selecao_pontos(CHAVE_FAIXA, "faixa", "faixa_idade_veiculo")
quimicas = ler_selecao_pontos(CHAVE_QUIMICA, "quimica", "battery_chemistry")
area = ler_selecao_area(CHAVE_AREA, "area")

todos = pd.Series(True, index=amostra.index)
na_faixa = amostra["faixa_idade_veiculo"].isin(faixas) if faixas else todos
na_quimica = amostra["battery_chemistry"].isin(quimicas) if quimicas else todos
na_area = todos.copy()
for coluna, (inicio, fim) in area.items():
    na_area &= amostra[coluna].between(inicio, fim)
recorte_d2 = amostra[na_faixa & na_quimica & na_area]

# Acima deste limite o risco térmico é outlier pela regra do IQR. É o valor da EDA (Seção 4), calculado
# antes da imputação: recalcular nos dados imputados estreitaria o IQR e mudaria o corte
LIMITE_RISCO = 53.92

with aba_indicadores:
    kpis = resumo_kpis(recorte_d2, LIMITE_RISCO)
    base = resumo_kpis(df, LIMITE_RISCO)
    nota_base = f"Abaixo, a diferença para a base completa ({formatar_numero(base['veiculos'], 0)} veículos)."

    # Grade fixa de 4 colunas: os cards não mudam de linha quando os deltas ficam mais largos
    col_veiculos, col_falha, col_soh, col_risco = st.columns(4)

    with col_veiculos:
        parcela = kpis["veiculos"] / base["veiculos"]
        st.metric(
            "Veículos no recorte",
            formatar_numero(kpis["veiculos"], 0),
            formatar_pct(parcela, 0 if parcela >= 0.1 else 1),  # recortes pequenos não viram "0%"
            delta_color="off",
            delta_arrow="off",
            delta_description="da base",
            border=True,
            help="Quantos veículos atendem ao filtro de uso e às seleções feitas nos gráficos.",
        )

    with col_falha:
        delta, sem_mudanca = formatar_delta(kpis["taxa_falha"], base["taxa_falha"], "p.p.", escala=100)
        st.metric(
            "Taxa de falha",
            formatar_pct(kpis["taxa_falha"]),
            delta,
            delta_color="off" if sem_mudanca else "inverse",
            delta_arrow="off" if sem_mudanca else "auto",
            delta_description="vs. base",
            border=True,
            help="Proporção de veículos com falha de bateria (battery_failure = 1). " + nota_base,
        )

    with col_soh:
        delta, sem_mudanca = formatar_delta(kpis["soh_mediano"], base["soh_mediano"], "p.p.")
        st.metric(
            "SoH mediano",
            f"{formatar_numero(kpis['soh_mediano'])}%",
            delta,
            delta_color="off" if sem_mudanca else "normal",
            delta_arrow="off" if sem_mudanca else "auto",
            delta_description="vs. base",
            border=True,
            help="Mediana da saúde da bateria (state_of_health): quanto da capacidade original ela ainda tem. "
            "Mediana, e não média, porque a variável não é normal (EDA). " + nota_base,
        )

    with col_risco:
        delta, sem_mudanca = formatar_delta(kpis["risco_extremo"], base["risco_extremo"], "p.p.", escala=100)
        st.metric(
            "Risco térmico extremo",
            formatar_pct(kpis["risco_extremo"]),
            delta,
            delta_color="off" if sem_mudanca else "inverse",
            delta_arrow="off" if sem_mudanca else "auto",
            delta_description="vs. base",
            border=True,
            help=f"Proporção de veículos com risco de thermal runaway acima de {formatar_numero(LIMITE_RISCO)}, "
            "o limite superior do IQR (os outliers mantidos na EDA). " + nota_base,
        )

    # Resumo das seleções ativas, com botão para limpar
    partes = []
    if faixas:
        partes.append("idade " + ", ".join(faixas))
    if quimicas:
        partes.append("química " + ", ".join(quimicas))
    if area:
        soh, risco = area.get("state_of_health", [None, None]), area.get("thermal_runaway_risk", [None, None])
        partes.append(f"SoH {soh[0]:.0f}–{soh[1]:.0f}% e risco térmico {risco[0]:.0f}–{risco[1]:.0f}")

    with st.container(horizontal=True, vertical_alignment="center"):
        if partes:
            st.markdown(":material/filter_alt: **Seleção:** " + " · ".join(partes))
        else:
            st.caption(
                "Clique nas barras (Shift + clique para várias) ou arraste uma área na dispersão "
                "para filtrar os indicadores e os outros gráficos."
            )
        st.space("stretch")
        st.button(
            "Limpar seleções",
            icon=":material/filter_alt_off:",
            on_click=limpar_selecoes,
            disabled=not partes,
        )

    tabela_faixas = taxa_por_grupo(amostra[na_quimica & na_area], "faixa_idade_veiculo", ORDEM_FAIXAS)
    tabela_quimicas = taxa_por_grupo(amostra[na_faixa & na_area], "battery_chemistry", ORDEM_QUIMICA)
    # Mesmo eixo nos dois gráficos de barras, para as taxas serem comparáveis entre eles
    maior_taxa = pd.concat([tabela_faixas["taxa"], tabela_quimicas["taxa"]]).max()
    taxa_maxima = max(0.2, (0 if pd.isna(maior_taxa) else maior_taxa) * 1.15)

    st.subheader("Taxa de falha")
    col_faixa, col_quimica = st.columns(2)

    with col_faixa, st.container(border=True, height="stretch"):
        st.markdown("**Por idade do veículo**")
        st.altair_chart(
            graficos.barras_taxa(
                tabela_faixas,
                "faixa_idade_veiculo",
                ORDEM_FAIXAS,
                alt.selection_point(name="faixa", fields=["faixa_idade_veiculo"]),
                "Idade do veículo",
                horizontal=False,
                taxa_maxima=taxa_maxima,
            ),
            key=CHAVE_FAIXA,
            on_select="rerun",
            alt="Taxa de falha por faixa de idade do veículo, crescente com a idade",
        )
        sem_idade = amostra["faixa_idade_veiculo"].isna().sum()
        st.caption(f"{formatar_numero(sem_idade, 0)} veículos sem idade registrada ficam fora deste gráfico.")

    with col_quimica, st.container(border=True, height="stretch"):
        st.markdown("**Por química da bateria**")
        st.altair_chart(
            graficos.barras_taxa(
                tabela_quimicas,
                "battery_chemistry",
                ORDEM_QUIMICA,
                alt.selection_point(name="quimica", fields=["battery_chemistry"]),
                "Química",
                horizontal=True,
                taxa_maxima=taxa_maxima,
            ),
            key=CHAVE_QUIMICA,
            on_select="rerun",
            alt="Taxa de falha por química da bateria, parecida entre as químicas",
        )
        st.caption(
            "As taxas quase não mudam entre químicas: na EDA o Qui-quadrado não encontrou associação "
            "entre química e falha."
        )

    st.subheader("Saúde da bateria × risco térmico")
    with st.container(border=True):
        pontos = amostra.sample(n=min(PONTOS_DISPERSAO, len(amostra)), random_state=42)
        st.altair_chart(
            graficos.dispersao_soh_risco(
                pontos.assign(no_recorte=(na_faixa & na_quimica).loc[pontos.index]),
                alt.selection_interval(name="area", encodings=["x", "y"]),
                graficos.dominio_com_folga(df["state_of_health"]),
                graficos.dominio_com_folga(df["thermal_runaway_risk"]),
            ),
            key=CHAVE_AREA,
            on_select="rerun",
            alt="Dispersão de saúde da bateria por risco térmico: as falhas se concentram com SoH baixo "
            "e risco alto",
        )
        st.caption(
            f"Amostra aleatória de {formatar_numero(len(pontos), 0)} veículos no gráfico, para o app ficar leve. "
            "A área arrastada filtra todos os veículos da amostra. As linhas de pontos em SoH ≈ 83% e risco ≈ 14,5 "
            "são os valores imputados pela mediana na EDA."
        )

    with st.expander("Veículos do recorte", icon=":material/table:"):
        st.dataframe(
            recorte_d2[
                [
                    "vehicle_id",
                    "vehicle_brand",
                    "vehicle_model",
                    "faixa_idade_veiculo",
                    "battery_chemistry",
                    "state_of_health",
                    "thermal_runaway_risk",
                    "status_bateria",
                ]
            ].rename(
                columns={
                    "vehicle_id": "Veículo",
                    "vehicle_brand": "Marca",
                    "vehicle_model": "Modelo",
                    "faixa_idade_veiculo": "Idade",
                    "battery_chemistry": "Química",
                    "state_of_health": "SoH (%)",
                    "thermal_runaway_risk": "Risco térmico",
                    "status_bateria": "Status",
                }
            ),
            hide_index=True,
            alt="Veículos que atendem ao filtro e às seleções dos gráficos",
        )
