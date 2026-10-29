"""Testes gerais: carregamento, abas, filtro global da sidebar e layout em tela de celular."""

from playwright.sync_api import expect

from apoio import abrir_aba, abrir_app, conferir_sem_erros, esperar_rerun, esperar_texto, metrica


def test_app_carrega_com_titulo_e_duas_abas(app):
    expect(app.get_by_role("heading", name="Saúde de baterias de veículos elétricos")).to_be_visible()
    abas = app.get_by_role("tab")
    expect(abas).to_have_count(2)
    expect(abas.nth(0)).to_contain_text("Correlação e distribuição")
    expect(abas.nth(1)).to_contain_text("Indicadores")
    esperar_texto(app.get_by_test_id("stCaptionContainer").first, "20.000 veículos após o tratamento da EDA")


def test_as_duas_abas_carregam_seus_graficos(app):
    painel_1 = app.get_by_test_id("stTabPanel").nth(0)
    expect(painel_1.get_by_test_id("stVegaLiteChart")).to_have_count(6)  # heatmap + 5 histogramas

    abrir_aba(app, "Indicadores")
    painel_2 = app.get_by_test_id("stTabPanel").nth(1)
    expect(painel_2.get_by_test_id("stVegaLiteChart")).to_have_count(3)
    expect(painel_2.get_by_test_id("stMetric")).to_have_count(4)


def test_filtro_tipo_de_uso_vale_para_os_dois_paineis(app):
    sidebar = app.get_by_test_id("stSidebar")

    sidebar.get_by_role("button", name="Particular").click()  # desmarca: sobra só Frota
    esperar_rerun(app)
    esperar_texto(app.get_by_test_id("stCaptionContainer").first, "6.748 na amostra")
    esperar_texto(app.get_by_test_id("stTabPanel").nth(0), "6.748 de 6.748 veículos")
    abrir_aba(app, "Indicadores")
    expect(metrica(app, "Veículos no recorte")).to_have_text("6.748")

    sidebar.get_by_role("button", name="Frota").click()  # nada marcado: todos os veículos entram
    esperar_rerun(app)
    expect(metrica(app, "Veículos no recorte")).to_have_text("20.000")


def test_app_funciona_sem_a_fonte_externa(page, url_app):
    # Simula rede sem acesso ao Google Fonts: o app deve cair na fonte padrão e continuar funcionando
    page.route("**/fonts.googleapis.com/**", lambda rota: rota.abort("namenotresolved"))
    page.route("**/fonts.gstatic.com/**", lambda rota: rota.abort("namenotresolved"))
    erros = abrir_app(page, url_app)
    abrir_aba(page, "Indicadores")
    expect(metrica(page, "Veículos no recorte")).to_have_text("20.000")
    conferir_sem_erros(page, erros)


def test_layout_de_celular_sem_rolagem_horizontal(app_celular):
    pagina = app_celular
    expect(pagina.get_by_role("heading", name="Saúde de baterias de veículos elétricos")).to_be_visible()
    abrir_aba(pagina, "Indicadores")
    expect(metrica(pagina, "Taxa de falha")).to_have_text("6,9%")
    sobra = pagina.evaluate(
        "() => { const m = document.querySelector('[data-testid=\"stMain\"]'); return m.scrollWidth - m.clientWidth; }"
    )
    assert sobra <= 1, f"A página rola na horizontal no celular ({sobra}px a mais)"
