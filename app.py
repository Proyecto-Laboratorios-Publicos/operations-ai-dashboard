import pandas as pd
import streamlit as st
from indec_data import obtener_datos_inflacion

st.set_page_config(
    page_title="Dashboard de Inflación y Analítica - INDEC",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Panel de Análisis Económico y Operativo")
st.markdown("""
Plataforma inteligente de analítica impulsada por series temporales históricas oficiales del **INDEC**. 
Explora la evolución macroeconómica completa, comparativas sectoriales y métricas en tiempo real.
""")

df_indec = obtener_datos_inflacion()

st.sidebar.header("Panel de Control & Filtros")
if not df_indec.empty:
    st.sidebar.success("Estado: Conectado a la API oficial en vivo.")
else:
    st.sidebar.error("Estado: Sin datos disponibles desde la API.")

opcion_historica = st.sidebar.selectbox(
    "Rango temporal de análisis:",
    [
        "Último año (12 meses)",
        "Últimos 2 años (24 meses)",
        "Histórico Completo",
    ],
)

if not df_indec.empty and "Mes" in df_indec.columns and "Inflacion_Mensual" in df_indec.columns:
    if "12 meses" in opcion_historica:
        df_filtrado = df_indec.tail(12)
    elif "24 meses" in opcion_historica:
        df_filtrado = df_indec.tail(24)
    else:
        df_filtrado = df_indec

    if len(df_indec) >= 2:
        ultimo_mes = df_indec.iloc[-1]["Mes"]
        ultima_inflacion = df_indec.iloc[-1]["Inflacion_Mensual"]
        inflacion_anterior = df_indec.iloc[-2]["Inflacion_Mensual"]
        delta_inflacion = round(ultima_inflacion - inflacion_anterior, 2)
    else:
        ultimo_mes = df_indec.iloc[-1]["Mes"]
        ultima_inflacion = df_indec.iloc[-1]["Inflacion_Mensual"]
        delta_inflacion = 0.0

    st.sidebar.markdown(f"**Última actualización:** {ultimo_mes}")
    st.sidebar.markdown(f"**Total períodos en sistema:** {len(df_indec)}")
else:
    df_filtrado = pd.DataFrame()
    ultimo_mes = "N/A"
    ultima_inflacion = 0.0
    delta_inflacion = 0.0

tab1, tab2, tab3 = st.tabs([
    "📈 Resumen General y Métricas",
    "📊 Análisis Sectorial",
    "📋 Explorador de Datos Completos",
])

with tab1:
    st.subheader("Indicadores Principales (IPC General)")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label=f"Inflación Mensual ({ultimo_mes})",
            value=f"{ultima_inflacion}%",
            delta=f"{delta_inflacion}%",
        )
    with col2:
        promedio_movil = round(df_filtrado["Inflacion_Mensual"].mean(), 2) if not df_filtrado.empty and "Inflacion_Mensual" in df_filtrado.columns else 0.0
        st.metric(
            label="Promedio Móvil (Período Seleccionado)",
            value=f"{promedio_movil}%",
        )
    with col3:
        max_mensual = df_filtrado["Inflacion_Mensual"].max() if not df_filtrado.empty and "Inflacion_Mensual" in df_filtrado.columns else 0.0
        st.metric(
            label="Máximo Mensual del Período",
            value=f"{max_mensual}%"
        )

    st.divider()
    st.subheader(f"📈 Evolución Histórica ({opcion_historica})")
    if not df_filtrado.empty and "Mes" in df_filtrado.columns and "Inflacion_Mensual" in df_filtrado.columns:
        st.line_chart(df_filtrado.set_index("Mes")[["Inflacion_Mensual"]], width="stretch")
    else:
        st.warning("No hay datos históricos para mostrar en el gráfico.")

with tab2:
    st.subheader("Comparativa y Tendencia Sectorial")
    st.markdown(f"### Desglose del Último Período ({ultimo_mes})")
    if not df_indec.empty:
        cols_sector = [c for c in ["Alimentos_Bebidas", "Vivienda_Servicios", "Transporte", "Salud"] if c in df_indec.columns]
        if cols_sector and len(df_indec) > 0:
            ultimo_reg = df_indec.iloc[-1][cols_sector].reset_index()
            ultimo_reg.columns = ["División", "Variación (%)"]
            st.bar_chart(ultimo_reg.set_index("División"), width="stretch")
        st.dataframe(df_indec, width="stretch")
    else:
        st.warning("Sin datos sectoriales para mostrar.")

with tab3:
    st.subheader("Base de Datos Histórica Oficial Normalizada")
    st.markdown("Visualiza la totalidad de los datos estructurados provenientes del endpoint oficial del INDEC:")
    if not df_indec.empty:
        st.dataframe(df_indec, width="stretch")
        csv = df_indec.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Descargar Histórico Completo en CSV",
            data=csv,
            file_name="indec_historico_completo.csv",
            mime="text/csv",
        )
    else:
        st.warning("La base de datos se encuentra vacía.")
