import pandas as pd
import streamlit as st
from indec_data import obtener_datos_inflacion

# Configuración inicial de la página
st.set_page_config(
    page_title="Dashboard Oficial IPC - INDEC",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Panel de Análisis Oficial - IPC INDEC")
st.markdown("""
Plataforma analítica conectada directamente al [Índice de Precios al Consumidor (IPC)](https://api.indec.gob.ar/datasets/ipc_nacional) del INDEC.
Explora las series temporales oficiales explotando todos los campos disponibles.
""")

@st.cache_data(ttl=3600)
def cargar_datos():
    return obtener_datos_inflacion()

df_raw = cargar_datos()

if df_raw.empty:
    st.error("No se pudieron recuperar datos desde la API del INDEC. Verifique el token de autent
