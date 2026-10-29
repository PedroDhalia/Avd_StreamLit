"""Dashboard 1: correlação e distribuição, com os cenários de borda pedidos na Aula 22."""

from playwright.sync_api import expect

from apoio import esperar_rerun, esperar_texto, metrica, remover_ultimas_variaveis


def painel(app):
    return app.get_by_test_id("stTabPanel").nth(0)


def test_estado_inicial(app):
    expect(app.get_by_role("heading", name="Correlação (Spearman)")).to_be_visible()
    expect(metrica(app, "Par mais correlacionado")).to_have_text("-0,94 (forte)")
    esperar_texto(app.get_by_test_id("stMetric").first, "Perda cap. × SoH")
    esperar_texto(painel(app), "20.000 de 20.000 veículos da amostra dentro dos filtros deste painel (6,9% com falha)")


def test_zero_variaveis_mostra_avisos(app):
    remover_ultimas_variaveis(app, 5)
    esperar_texto(painel(app), "Selecione pelo menos 2 variáveis para calcular a correlação.")
    esperar_texto(painel(app), "Selecione pelo menos 1 variável para ver a distribuição.")
    expect(painel(app).get_by_test_id("stVegaLiteChart")).to_have_count(0)


def test_uma_variavel_mostra_so_o_histograma(app):
    remover_ultimas_variaveis(app, 4)  # sobra o SoH
    esperar_texto(painel(app), "Selecione pelo menos 2 variáveis para calcular a correlação.")
    expect(painel(app).get_by_test_id("stVegaLiteChart")).to_have_count(1)


def test_duas_variaveis_recalculam_correlacao(app):
    remover_ultimas_variaveis(app, 3)  # sobram SoH e ciclos
    expect(painel(app).get_by_test_id("stVegaLiteChart")).to_have_count(3)  # heatmap + 2 histogramas
    esperar_texto(app.get_by_test_id("stMetric").first, "Ciclos × SoH")
    expect(metrica(app, "Par mais correlacionado")).to_have_text("-0,47 (moderada)")


def test_troca_de_metodo_de_correlacao(app):
    for metodo in ["Pearson", "Kendall", "Spearman"]:
        opcao = app.get_by_test_id("stSidebar").get_by_role("radio", name=metodo, exact=True)  # st.segmented_control
        opcao.click()
        esperar_rerun(app)
        expect(opcao).to_have_attribute("aria-checked", "true")
        expect(app.get_by_role("heading", name=f"Correlação ({metodo})")).to_be_visible()
        expect(metrica(app, "Par mais correlacionado")).to_contain_text("(forte)")


def test_remover_outliers_muda_o_recorte(app):
    app.get_by_test_id("stCheckbox").filter(has_text="Remover outliers").click()
    esperar_rerun(app)
    esperar_texto(painel(app), "18.496 de 20.000 veículos")
    esperar_texto(painel(app), "(4,8% com falha)")


def test_separar_por_status_mostra_legenda(app):
    app.get_by_test_id("stCheckbox").filter(has_text="Separar por status").click()
    esperar_rerun(app)
    esperar_texto(painel(app), "mediana de cada status")
    expect(painel(app).get_by_test_id("stVegaLiteChart")).to_have_count(6)


def test_slider_de_intervalo_estreito_mostra_aviso(app):
    # Leva o fim do intervalo de SoH até o início: sobram só os veículos com o menor SoH
    fim = app.get_by_role("slider", name="Saúde da bateria, SoH (%) — end")
    fim.focus()
    fim.press("Home")
    esperar_rerun(app)
    esperar_texto(painel(app), "poucos para uma correlação confiável")
    expect(painel(app).get_by_test_id("stVegaLiteChart")).to_have_count(5)  # sem heatmap, com histogramas


def test_expanders_abrem_as_tabelas(app):
    for titulo in ["Todos os pares", "Estatísticas descritivas"]:
        expander = painel(app).get_by_test_id("stExpander").filter(has_text=titulo)
        expander.get_by_text(titulo).click()
        expect(expander.get_by_test_id("stDataFrame")).to_be_visible()
