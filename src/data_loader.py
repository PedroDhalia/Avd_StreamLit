from pathlib import Path

import pandas as pd
import streamlit as st

from src.constantes import VARS_QUANT

# Caminho relativo à raiz do repositório: funciona local e no Streamlit Community Cloud
CAMINHO_PADRAO = Path(__file__).resolve().parent.parent / "data" / "clean" / "dataset.csv"

# Só as colunas que o app usa: o CSV tratado tem 73, e ler todas gastaria memória à toa no deploy
COLUNAS = VARS_QUANT + [
    "vehicle_id",
    "vehicle_brand",
    "vehicle_model",
    "battery_chemistry",
    "fleet_or_private",
    "faixa_idade_veiculo",
    "battery_failure",
    "status_bateria",
]


@st.cache_data
def load_data(path=CAMINHO_PADRAO):
    """Lê o dataset já tratado (exportado ao final do notebook de EDA)."""
    return pd.read_csv(path, usecols=COLUNAS)
