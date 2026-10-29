"""Fixtures dos testes de interface: sobe o app numa porta livre e abre o navegador do Playwright."""

import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

from apoio import abrir_app, conferir_sem_erros

RAIZ = Path(__file__).resolve().parent.parent


def _porta_livre():
    with socket.socket() as s:
        s.bind(("localhost", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def url_app(tmp_path_factory):
    """Roda `streamlit run app.py` durante a sessão de testes e devolve a URL."""
    porta = _porta_livre()
    log = tmp_path_factory.mktemp("servidor") / "streamlit.log"
    with open(log, "w", encoding="utf-8") as saida:
        processo = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", str(porta),
             "--server.headless", "true", "--browser.gatherUsageStats", "false"],
            cwd=RAIZ,
            stdout=saida,
            stderr=subprocess.STDOUT,
        )
    url = f"http://localhost:{porta}"
    for _ in range(120):
        try:
            with urllib.request.urlopen(f"{url}/_stcore/health", timeout=2) as resposta:
                if resposta.read() == b"ok":
                    break
        except OSError:
            time.sleep(0.5)
    else:
        processo.kill()
        pytest.fail(f"O app não subiu em 60 s. Log: {log.read_text(encoding='utf-8')[-2000:]}")

    yield url

    processo.terminate()
    processo.wait(timeout=15)


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    # Tela de notebook grande: os testes de clique nos gráficos dependem desse layout
    return {**browser_context_args, "viewport": {"width": 1440, "height": 1600}, "locale": "pt-BR"}


@pytest.fixture
def app(page, url_app):
    """Página com o app carregado. Ao final de cada teste, confere que não houve exceção nem erro de console."""
    erros = abrir_app(page, url_app)
    yield page
    conferir_sem_erros(page, erros)


@pytest.fixture
def app_celular(browser, url_app):
    """Mesmo app numa tela de celular (390 x 844)."""
    contexto = browser.new_context(viewport={"width": 390, "height": 844}, locale="pt-BR", is_mobile=True)
    pagina = contexto.new_page()
    erros = abrir_app(pagina, url_app)
    yield pagina
    conferir_sem_erros(pagina, erros)
    contexto.close()
