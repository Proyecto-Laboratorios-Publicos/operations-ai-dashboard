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
Plataforma inteligente de analítica impulsada por series temporales oficiales del **INDEC**. 
Explora la evolución de precios, indicadores sectoriales y tendencias macroeconómicas en tiempo real.
""")

# Cargar datos ampliados del INDEC
df_indec = obtener_datos_inflacion()

# Métricas clave del último período
ultimo_mes = df_indec.iloc[-1]["Mes"]
ultima_inflacion = df_indec.iloc[-1]["Inflacion_Mensual"]
inflacion_anterior = df_indec.iloc[-2]["Inflacion_Mensual"]
delta_inflacion = round(ultima_inflacion - inflacion_anterior, 2)

# Barra lateral informativa
st.sidebar.header("Panel de Control")
st.sidebar.success("Estado: Conectado a la base analítica oficial.")
st.sidebar.markdown(f"**Última actualización:** {ultimo_mes}")
st.sidebar.markdown(f"**Registros históricos:** {len(df_indec)} meses")

# Creación de Pestañas (Tabs) para una navegación 100% intuitiva
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
            label="Promedio Móvil (Últimos 3 meses)", 
            value=f"{round(df_indec['Inflacion_Mensual'].tail(3).mean(), 2)}%"
        )
    with col3:
        st.metric(
            label="Acumulado Anual Reciente", 
            value=f"{round(df_indec['Inflacion_Mensual'].tail(12).sum(), 2)}%"
        )

    st.divider()
    
    st.subheader("📈 Evolución Histórica Completa (IPC y Divisiones)")
    st.line_chart(df_indec.set_index("Mes")[["Inflacion_Mensual", "Alimentos_Bebidas", "Vivienda_Servicios", "Transporte", "Salud"]])

with tab2:
    st.subheader("Comparativa y Tendencia por División")
    
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown(f"### Desglose del Último Mes ({ultimo_mes})")
        ultimo_registro = df_indec.iloc[-1][["Alimentos_Bebidas", "Vivienda_Servicios", "Transporte", "Salud"]].reset_index()
        ultimo_registro.columns = ["Division", "Porcentaje"]
        st.bar_chart(ultimo_registro.set_index("Division"))

    with col_b:
        st.markdown("### Tendencia Acumulada por Área")
        st.area_chart(df_indec.set_index("Mes")[["Alimentos_Bebidas", "Vivienda_Servicios", "Transporte", "Salud"]])

with tab3:
    st.subheader("Base de Datos Oficial Normalizada")
    st.markdown("A continuación puedes visualizar, filtrar y exportar la totalidad de las series temporales cargadas en el sistema:")
    
    # Filtro interactivo opcional por cantidad de meses
    num_meses = st.slider("Seleccionar cantidad de meses a mostrar:", min_select := 3, max_value=len(df_indec), value=12)
    
    st.dataframe(df_indec.tail(num_meses), use_container_width=True)
    
    # Botón de descarga CSV para máxima utilidad profesional
    csv = df_indec.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar datos en formato CSV",
        data=csv,
        file_name='indec_serie_inflacion.csv',
        mime='text/csv',
    )
