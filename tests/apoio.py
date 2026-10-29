"""Funções de apoio dos testes de interface (esperas, leitura de KPIs e interação com os gráficos)."""

from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import expect

# Falhas ao baixar recursos de fora do app (a fonte Inter do Google Fonts) dependem da rede, não do app
FALHA_DE_RECURSO = "Failed to load resource"


def abrir_app(page, url):
    """Abre o app, espera a primeira execução terminar e devolve a lista (viva) de erros de console."""
    erros = []

    def registrar(msg):
        if msg.type != "error":
            return
        origem = (msg.location or {}).get("url", "")
        if FALHA_DE_RECURSO in msg.text and origem and not origem.startswith(url):
            return  # recurso externo: falha de rede, não do app
        erros.append(f"{msg.text} ({origem})" if origem else msg.text)

    page.on("console", registrar)
    page.on("pageerror", lambda erro: erros.append(str(erro)))
    page.goto(url)
    expect(page.get_by_test_id("stMetric").first).to_be_visible(timeout=60_000)
    esperar_rerun(page)
    return erros


def conferir_sem_erros(page, erros):
    excecoes = page.get_by_test_id("stException")
    assert excecoes.count() == 0, f"Exceção do Python na tela: {excecoes.first.inner_text()}"
    assert not erros, f"Erros no console do navegador: {erros}"


def esperar_rerun(page):
    """Espera o Streamlit terminar de reexecutar o script depois de uma interação."""
    status = page.get_by_test_id("stStatusWidget")
    try:
        status.wait_for(state="visible", timeout=1_500)  # o rerun pode ser rápido demais para ser visto
    except PlaywrightTimeout:
        pass
    status.wait_for(state="hidden", timeout=60_000)
    page.wait_for_timeout(400)  # os gráficos Vega terminam de desenhar logo depois


def abrir_aba(page, nome):
    page.get_by_role("tab", name=nome).click()
    esperar_rerun(page)


def metrica(page, rotulo):
    """Valor de um st.metric, localizado pelo rótulo."""
    return page.get_by_test_id("stMetric").filter(has_text=rotulo).get_by_test_id("stMetricValue")


def numero(texto):
    """Converte '4.770', '15,8%' ou '73,5%' em float."""
    return float(texto.replace(".", "").replace("%", "").replace(",", ".").split()[0])


def graficos_visiveis(page):
    return page.locator("[data-testid='stVegaLiteChart']:visible")


def caixa(locator):
    locator.scroll_into_view_if_needed()
    return locator.bounding_box()


def clicar_no_grafico(page, grafico, x, y, shift=False):
    """Clica numa posição relativa do gráfico (0 a 1 na largura e na altura) e espera o rerun."""
    box = caixa(grafico)
    if shift:
        page.keyboard.down("Shift")
    page.mouse.click(box["x"] + box["width"] * x, box["y"] + box["height"] * y)
    if shift:
        page.keyboard.up("Shift")
    esperar_rerun(page)


def arrastar_no_grafico(page, grafico, inicio, fim):
    """Arrasta uma área entre duas posições relativas do gráfico e espera o rerun."""
    box = caixa(grafico)
    x0, y0 = box["x"] + box["width"] * inicio[0], box["y"] + box["height"] * inicio[1]
    x1, y1 = box["x"] + box["width"] * fim[0], box["y"] + box["height"] * fim[1]
    page.mouse.move(x0, y0)
    page.mouse.down()
    page.mouse.move(x1, y1, steps=12)
    page.mouse.up()
    esperar_rerun(page)


def resumo_da_selecao(page):
    return page.get_by_test_id("stMarkdownContainer").filter(has_text="Seleção:")


def remover_ultimas_variaveis(page, quantidade):
    """Tira as últimas variáveis do seletor (Backspace no campo do multiselect)."""
    campo = page.get_by_test_id("stMultiSelect").locator("input")
    campo.click()
    for _ in range(quantidade):
        campo.press("Backspace")
    page.keyboard.press("Escape")
    esperar_rerun(page)


def esperar_texto(locator, texto, timeout=20_000):
    expect(locator).to_contain_text(texto, timeout=timeout)
