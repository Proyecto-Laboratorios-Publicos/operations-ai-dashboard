import streamlit as st
import pandas as pd
import datetime

# Configuración de la página
st.set_page_config(
    page_title="Dashboard de Inflación y Analítica - INDEC",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Panel de Análisis Económico y Operativo")
st.markdown("""
Bienvenido a este dashboard inteligente impulsado por datos oficiales del **INDEC**. 
Aquí podrás consultar métricas de inflación, evolución de precios por división y realizar análisis automatizados.
""")

# Barra lateral de navegación o filtros
st.sidebar.header("Panel de Control")
st.sidebar.info("Estado del sistema: Conectado a la base analítica.")

# Sección principal provisional
st.subheader("Indicadores Principales")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="Última Inflación Mensual (IPC)", value="--%", delta="--%")
with col2:
    st.metric(label="Variación Interanual", value="--%", delta="--%")
with col3:
    st.metric(label="Próxima Actualización INDEC", value="Pendiente")

st.divider()

# Área de interacción
st.info("💡 **Siguiente paso:** Vamos a configurar la carga automática de los datos oficiales y el panel de consultas en lenguaje natural.")
