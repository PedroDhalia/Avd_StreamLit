"""Dashboard 2: KPIs e seleção cruzada entre os gráficos.

Os cliques usam posições relativas dentro de cada gráfico, calibradas para a tela de 1440 px do conftest.
Cada teste confere o resumo da seleção, então um clique fora do lugar aparece como falha clara.
"""

import pytest
from playwright.sync_api import expect

from apoio import (
    abrir_aba,
    arrastar_no_grafico,
    caixa,
    clicar_no_grafico,
    esperar_rerun,
    esperar_texto,
    graficos_visiveis,
    metrica,
    numero,
    resumo_da_selecao,
)

# Centro de cada barra no gráfico de idade (x) e uma altura logo acima da base do eixo (y)
BARRA_IDADE = {"<4 anos": 0.24, "4-6 anos": 0.46, "7-8 anos": 0.67, "9+ anos": 0.88}
ALTURA_BASE_BARRAS = 0.72
# Linha da química NMC (a primeira) no gráfico de barras horizontais
LINHA_NMC = (0.2, 0.12)


@pytest.fixture
def indicadores(app):
    abrir_aba(app, "Indicadores")
    return app


def grafico_idade(page):
    return graficos_visiveis(page).nth(0)


def grafico_quimica(page):
    return graficos_visiveis(page).nth(1)


def grafico_dispersao(page):
    return graficos_visiveis(page).nth(2)


def botao_limpar(page):
    return page.get_by_role("button", name="Limpar seleções")


def test_kpis_iniciais(indicadores):
    expect(metrica(indicadores, "Veículos no recorte")).to_have_text("20.000")
    expect(metrica(indicadores, "Taxa de falha")).to_have_text("6,9%")
    expect(metrica(indicadores, "SoH mediano")).to_have_text("82,9%")
    expect(metrica(indicadores, "Risco térmico extremo")).to_have_text("3,5%")
    expect(botao_limpar(indicadores)).to_be_disabled()
    esperar_texto(indicadores.get_by_test_id("stTabPanel").nth(1), "Clique nas barras")


def test_clique_na_barra_filtra_os_kpis(indicadores):
    clicar_no_grafico(indicadores, grafico_idade(indicadores), BARRA_IDADE["9+ anos"], ALTURA_BASE_BARRAS)
    esperar_texto(resumo_da_selecao(indicadores), "idade 9+ anos")
    expect(metrica(indicadores, "Veículos no recorte")).to_have_text("4.770")
    expect(metrica(indicadores, "Taxa de falha")).to_have_text("15,8%")
    expect(metrica(indicadores, "SoH mediano")).to_have_text("73,5%")
    expect(botao_limpar(indicadores)).to_be_enabled()


def test_shift_clique_seleciona_varias_barras(indicadores):
    clicar_no_grafico(indicadores, grafico_idade(indicadores), BARRA_IDADE["9+ anos"], ALTURA_BASE_BARRAS)
    clicar_no_grafico(indicadores, grafico_idade(indicadores), BARRA_IDADE["7-8 anos"], ALTURA_BASE_BARRAS, shift=True)
    esperar_texto(resumo_da_selecao(indicadores), "9+ anos")
    esperar_texto(resumo_da_selecao(indicadores), "7-8 anos")
    expect(metrica(indicadores, "Veículos no recorte")).to_have_text("8.617")  # 4.770 + 3.847


def test_selecao_cruzada_entre_idade_e_quimica(indicadores):
    clicar_no_grafico(indicadores, grafico_idade(indicadores), BARRA_IDADE["9+ anos"], ALTURA_BASE_BARRAS)
    clicar_no_grafico(indicadores, grafico_quimica(indicadores), *LINHA_NMC)
    esperar_texto(resumo_da_selecao(indicadores), "química NMC")
    expect(metrica(indicadores, "Veículos no recorte")).to_have_text("1.933")
    expect(metrica(indicadores, "Taxa de falha")).to_have_text("16,7%")


def test_area_na_dispersao_encontra_a_zona_de_falha(indicadores):
    # Canto superior esquerdo: SoH baixo e risco térmico alto
    arrastar_no_grafico(indicadores, grafico_dispersao(indicadores), (0.1, 0.2), (0.32, 0.45))
    esperar_texto(resumo_da_selecao(indicadores), "risco térmico")
    taxa = numero(metrica(indicadores, "Taxa de falha").inner_text())
    assert taxa > 50, f"Na zona de SoH baixo e risco alto a taxa de falha deveria passar de 50%, veio {taxa}%"


def test_rolar_sobre_a_dispersao_rola_a_pagina_sem_mudar_a_selecao(indicadores):
    # Regressão: a roda do mouse sobre a área selecionada prendia a rolagem e redimensionava a seleção
    indicadores.set_viewport_size({"width": 1440, "height": 900})  # tela menor: a página precisa rolar
    grafico = grafico_dispersao(indicadores)
    expect(grafico.locator("canvas")).to_have_count(1)  # desenhado em canvas, não em milhares de nós SVG

    arrastar_no_grafico(indicadores, grafico, (0.35, 0.35), (0.6, 0.6))
    selecao = resumo_da_selecao(indicadores).inner_text()

    principal = indicadores.get_by_test_id("stMain")
    principal.evaluate("m => { m.scrollTop = Math.max(0, m.scrollTop - 250); }")  # folga para rolar para baixo
    box = caixa(grafico)
    indicadores.mouse.move(box["x"] + box["width"] * 0.47, box["y"] + box["height"] * 0.47)  # dentro da área
    antes = principal.evaluate("m => m.scrollTop")
    for _ in range(3):
        indicadores.mouse.wheel(0, 100)
    indicadores.wait_for_timeout(800)
    esperar_rerun(indicadores)

    assert principal.evaluate("m => m.scrollTop") > antes, "A página não rolou com o mouse sobre a dispersão"
    expect(resumo_da_selecao(indicadores)).to_have_text(selecao)


def test_limpar_selecoes_volta_a_base(indicadores):
    clicar_no_grafico(indicadores, grafico_idade(indicadores), BARRA_IDADE["9+ anos"], ALTURA_BASE_BARRAS)
    expect(metrica(indicadores, "Veículos no recorte")).to_have_text("4.770")
    botao_limpar(indicadores).click()
    expect(metrica(indicadores, "Veículos no recorte")).to_have_text("20.000", timeout=20_000)
    expect(botao_limpar(indicadores)).to_be_disabled()
    expect(resumo_da_selecao(indicadores)).to_have_count(0)


def test_tabela_de_veiculos_do_recorte(indicadores):
    clicar_no_grafico(indicadores, grafico_idade(indicadores), BARRA_IDADE["9+ anos"], ALTURA_BASE_BARRAS)
    expander = indicadores.get_by_test_id("stExpander").filter(has_text="Veículos do recorte")
    expander.get_by_text("Veículos do recorte").click()
    tabela = expander.get_by_test_id("stDataFrame")
    expect(tabela).to_be_visible()
    # A tabela acessível do st.dataframe fica oculta na tela (o grid é desenhado em canvas)
    grade = tabela.get_by_role("grid", include_hidden=True).first
    expect(grade).to_have_attribute("aria-rowcount", "4771")  # 4.770 veículos + linha de cabeçalho
