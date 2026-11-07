import pandas as pd
import streamlit as st
from indec_data import obtener_datos_inflacion

# Configuración inicial de la página
st.set_page_config(
    page_title="Dashboard Oficial IPC - INDEC",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Panel Integral de Analítica - Índice de Precios al Consumidor (INDEC)")
st.markdown("""
Plataforma analítica avanzada conectada en tiempo real al **[Catálogo API-INDEC](https://api.indec.gob.ar/docs#tag/direcci%C3%B3n-de-%C3%ADndices-de-precios-de-consumo)**.
Explora y explota la totalidad de los campos oficiales disponibles (clasificadores, regiones, niveles, tipos de indicadores y series temporales).
""")

# Carga de datos crudos desde el módulo
df_raw = obtener_datos_inflacion()

if df_raw.empty:
    st.error("No se pudieron recuperar datos desde la API del INDEC. Verifique la conexión o el token de acceso.")
    st.stop()

# Barra lateral de filtros y control global
st.sidebar.header("🎛️ Filtros Oficiales API")

# 1. Filtro por Región
regiones_disponibles = sorted(df_raw["region"].dropna().unique().tolist())
region_seleccionada = st.sidebar.selectbox(
    "Región Estadística:",
    ["Todas"] + regiones_disponibles
)

# 2. Filtro por Tipo de Indicador
tipos_indicador = sorted(df_raw["tipo_de_indicador_descripcion"].dropna().unique().tolist())
tipo_ind_seleccionado = st.sidebar.multiselect(
    "Tipo de Indicador:",
    options=tipos_indicador,
    default=tipos_indicador[:1] if tipos_indicador else []
)

# 3. Filtro por Clasificador
clasificadores = sorted(df_raw["clasificador"].dropna().unique().tolist())
clasificador_seleccionado = st.sidebar.multiselect(
    "Clasificador:",
    options=clasificadores,
    default=clasificadores
)

# Aplicar filtros al DataFrame crudo
df_filtrado = df_raw.copy()

if region_seleccionada != "Todas":
    df_filtrado = df_filtrado[df_filtrado["region"] == region_seleccionada]

if tipo_ind_seleccionado:
    df_filtrado = df_filtrado[df_filtrado["tipo_de_indicador_descripcion"].isin(tipo_ind_seleccionado)]

if clasificador_seleccionado:
    df_filtrado = df_filtrado[df_filtrado["clasificador"].isin(clasificador_seleccionado)]

# Sidebar métricas de control
st.sidebar.divider()
st.sidebar.markdown(f"**Registros crudos totales:** {len(df_raw):,}")
st.sidebar.markdown(f"**Registros filtrados:** {len(df_filtrado):,}")

# Pestañas principales para explotar cada campo y dimensión de la API
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Series Temporales",
    "🗺️ Análisis Regional",
    "📂 Jerarquía y Clasificadores",
    "📋 Explorador de Datos Crudos"
])

with tab1:
    st.subheader("Evolución de Indicadores a lo Largo del Tiempo")
    st.markdown("Visualiza el comportamiento de los valores a través del campo **periodo** y **Periodo_Texto**.")
    
    if not df_filtrado.empty and "valor" in df_filtrado.columns:
        df_chart = df_filtrado.dropna(subset=["valor", "Periodo_Texto", "descripcion"])
        
        if not df_chart.empty:
            descripciones_disponibles = sorted(df_chart["descripcion"].unique().tolist())
            desc_elegidas = st.multiselect(
                "Seleccione descripciones/categorías para comparar en el gráfico:",
                options=descripciones_disponibles,
                default=descripciones_disponibles[:3] if len(descripciones_disponibles) >= 3 else descripciones_disponibles
            )
            
            if desc_elegidas:
                df_subset = df_chart[df_chart["descripcion"].isin(desc_elegidas)]
                pivot_chart = df_subset.pivot_table(
                    index=["periodo", "Periodo_Texto"],
                    columns="descripcion",
                    values="valor",
                    aggfunc="mean"
                ).reset_index()
                
                pivot_chart = pivot_chart.sort_values("periodo")
                pivot_chart.set_index("Periodo_Texto", inplace=True)
                
                st.line_chart(pivot_chart.drop(columns=["periodo"], errors="ignore"), width="stretch")
            else:
                st.info("Seleccione al menos una categoría para visualizar la tendencia temporal.")
        else:
            st.warning("No hay suficientes datos numéricos con los filtros actuales.")
    else:
        st.warning("Sin datos disponibles para el análisis temporal.")

with tab2:
    st.subheader("Comparativa por Regiones Estadísticas")
    st.markdown("Explota las diferencias en los valores del indicador agrupados por el campo **region**.")
    
    if not df_filtrado.empty and "region" in df_filtrado.columns:
        col_reg1, col_reg2 = st.columns(2)
        
        with col_reg1:
            st.markdown("#### Promedio de Valores por Región")
            df_reg_mean = df_filtrado.groupby("region")["valor"].mean().reset_index()
            st.bar_chart(df_reg_mean.set_index("region"), width="stretch")
            
        with col_reg2:
            st.markdown("#### Resumen Estadístico Regional")
            st.dataframe(df_filtrado.groupby("region")["valor"].agg(["count", "mean", "min", "max"]).reset_index(), width="stretch")
    else:
        st.warning("No hay datos regionales disponibles.")

with tab3:
    st.subheader("Estructura por Clasificadores, Niveles y Códigos")
    st.markdown("Aprovecha la jerarquía oficial utilizando **clasificador**, **nivel**, **codigo** y **unidad_de_medida**.")
    
    if not df_filtrado.empty:
        st.dataframe(
            df_filtrado[["clasificador", "nivel", "codigo", "descripcion", "unidad_de_medida", "valor", "observaciones"]].drop_duplicates(),
            width="stretch"
        )
    else:
        st.warning("No hay datos para la jerarquía seleccionada.")

with tab4:
    st.subheader("Explorador Multidimensional Completo")
    st.markdown("Tabla interactiva que contiene absolutamente todas las columnas y registros devueltos por la API.")
    
    if not df_filtrado.empty:
        st.dataframe(df_filtrado, width="stretch")
        
        csv_data = df_filtrado.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Descargar Datos Filtrados en CSV",
            data=csv_data,
            file_name="indec_datos_completos_filtrados.csv",
            mime="text/csv",
        )
    else:
        st.warning("No hay registros para mostrar.")
