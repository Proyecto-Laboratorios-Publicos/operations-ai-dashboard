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
Plataforma inteligente de analítica impulsada por series temporales históricas oficiales del **INDEC**. 
Explora la evolución macroeconómica completa, comparativas sectoriales y métricas en tiempo real.
""")

# Cargar base de datos histórica completa
df_indec = obtener_datos_inflacion()

# Barra lateral con filtros avanzados de histórico
st.sidebar.header("Panel de Control & Filtros")
st.sidebar.success("Estado: Conectado al histórico oficial.")

# Selector de rango de registros a visualizar en los gráficos
opcion_historica = st.sidebar.selectbox(
    "Rango temporal de análisis:",
    ["Último año (12 meses)", "Últimos 2 años (24 meses)", "Histórico Completo (Desde 2024)"]
)

if "12 meses" in opcion_historica:
    df_filtrado = df_indec.tail(12)
elif "24 meses" in opcion_historica:
    df_filtrado = df_indec.tail(24)
else:
    df_filtrado = df_indec

ultimo_mes = df_indec.iloc[-1]["Mes"]
ultima_inflacion = df_indec.iloc[-1]["Inflacion_Mensual"]
inflacion_anterior = df_indec.iloc[-2]["Inflacion_Mensual"]
delta_inflacion = round(ultima_inflacion - inflacion_anterior, 2)

st.sidebar.markdown(f"**Última actualización:** {ultimo_mes}")
st.sidebar.markdown(f"**Total registros en sistema:** {len(df_indec)} meses")

# Pestañas de navegación
tab1, tab2, tab3 = st.tabs(["📈 Resumen General y Métricas", "📊 Análisis Sectorial por Divisiones", "📋 Explorador de Datos Completos"])

with tab1:
    st.subheader("Indicadores Principales (IPC General)")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label=f"Inflación Mensual ({ultimo_mes})", 
            value=f"{ultima_inflacion}%", 
            delta=f"{delta_inflacion}%"
        )
    with col2:
        st.metric(
            label="Promedio Móvil (Período Seleccionado)", 
            value=f"{round(df_filtrado['Inflacion_Mensual'].mean(), 2)}%"
        )
    with col3:
        st.metric(
            label="Máximo Mensual del Período", 
            value=f"{df_filtrado['Inflacion_Mensual'].max()}%"
        )

    st.divider()
    
    st.subheader(f"📈 Evolución Histórica ({opcion_historica})")
    st.line_chart(df_filtrado.set_index("Mes")[["Inflacion_Mensual", "Alimentos_Bebidas", "Vivienda_Servicios", "Transporte", "Salud"]])

with tab2:
    st.subheader("Comparativa y Tendencia por División")
    
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown(f"### Desglose del Último Mes ({ultimo_mes})")
        ultimo_registro = df_indec.iloc[-1][["Alimentos_Bebidas", "Vivienda_Servicios", "Transporte", "Salud"]].reset_index()
        ultimo_registro.columns = ["Division", "Porcentaje"]
        st.bar_chart(ultimo_registro.set_index("Division"))

    with col_b:
        st.markdown(f"### Tendencia Acumulada ({opcion_historica})")
        st.area_chart(df_filtrado.set_index("Mes")[["Alimentos_Bebidas", "Vivienda_Servicios", "Transporte", "Salud"]])

with tab3:
    st.subheader("Base de Datos Histórica Oficial Normalizada")
    st.markdown("Visualiza y exporta la totalidad del repositorio de series temporales del INDEC:")
    
    st.dataframe(df_indec, use_container_width=True)
    
    # Botón de descarga CSV con todo el histórico
    csv = df_indec.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar Histórico Completo en CSV",
        data=csv,
        file_name='indec_historico_completo.csv',
        mime='text/csv',
    )
