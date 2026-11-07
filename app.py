import streamlit as st
import pandas as pd
from indec_data import obtener_datos_inflacion

# Configuración de la página
st.set_page_config(
    page_title="Dashboard de Inflación y Analítica - INDEC",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Panel de Análisis Económico y Operativo")
st.markdown("""
Bienvenido a este dashboard inteligente impulsado por datos oficiales del **INDEC**. 
Aquí podrás consultar métricas de inflación, evolución de precios por división y realizar análisis de datos en tiempo real.
""")

# Cargar datos del INDEC
df_indec = obtener_datos_inflacion()

# Obtener el último valor disponible
ultimo_mes = df_indec.iloc[-1]["Mes"]
ultima_inflacion = df_indec.iloc[-1]["Inflacion_Mensual"]
inflacion_anterior = df_indec.iloc[-2]["Inflacion_Mensual"]
delta_inflacion = round(ultima_inflacion - inflacion_anterior, 2)

# Barra lateral
st.sidebar.header("Panel de Control")
st.sidebar.success("Estado: Conectado a la API analítica del INDEC.")
st.sidebar.markdown(f"**Última actualización registrada:** {ultimo_mes}")

# Sección de métricas principales
st.subheader("Indicadores Principales (IPC)")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label=f"Inflación Mensual ({ultimo_mes})", 
        value=f"{ultima_inflacion}%", 
        delta=f"{delta_inflacion}%", 
    )
with col2:
    st.metric(
        label="Promedio Móvil (Últimos 3 meses)", 
        value=f"{round(df_indec['Inflacion_Mensual'].tail(3).mean(), 2)}%"
    )
with col3:
    st.metric(
        label="Próxima Publicación INDEC", 
        value="Medizados de mes"
    )

st.divider()

# Gráfico interactivo y tabla
st.subheader("📈 Evolución Histórica de la Inflación Mensual")
st.line_chart(df_indec.set_index("Mes")[["Inflacion_Mensual", "Alimentos_Bebidas"]])

with st.expander("Ver tabla de datos detallados"):
    st.dataframe(df_indec, use_container_width=True)
