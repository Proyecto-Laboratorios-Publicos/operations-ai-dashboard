import pandas as pd
import streamlit as st
from indec_data import obtener_datos_inflacion

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

df_raw = obtener_datos_inflacion()

if df_raw.empty:
    st.error("No se pudieron recuperar datos desde la API del INDEC.")
    st.stop()

# Barra lateral de filtros oficiales basados estrictamente en la documentación
st.sidebar.header("🎛️ Filtros Oficiales API")

# 1. Filtro por Tipo de Indicador Descripcion
tipos_ind = sorted(df_raw["tipo_de_indicador_descripcion"].dropna().unique().tolist())
tipo_ind_sel = st.sidebar.selectbox(
    "Tipo de Indicador:",
    options=tipos_ind
)

df_filtrado = df_raw[df_raw["tipo_de_indicador_descripcion"] == tipo_ind_sel]

# 2. Filtro por Región Estadística
regiones = sorted(df_filtrado["region"].dropna().unique().tolist())
region_sel = st.sidebar.selectbox(
    "Región Estadística:",
    options=["Todas"] + regiones
)

if region_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado["region"] == region_sel]

# 3. Filtro por Clasificador
clasificadores = sorted(df_filtrado["clasificador"].dropna().unique().tolist())
clasificador_sel = st.sidebar.multiselect(
    "Clasificador:",
    options=clasificadores,
    default=clasificadores
)

if clasificador_sel:
    df_filtrado = df_filtrado[df_filtrado["clasificador"].isin(clasificador_sel)]

st.sidebar.divider()
st.sidebar.markdown(f"**Registros totales:** {len(df_raw):,}")
st.sidebar.markdown(f"**Registros filtrados:** {len(df_filtrado):,}")

# Pestañas de análisis estructuradas sin mezclar métricas
tab1, tab2, tab3 = st.tabs([
    "📈 Series Temporales por Descripción",
    "📊 Desglose de Niveles y Códigos",
    "📋 Explorador de Datos Crudos"
])

with tab1:
    st.subheader(f"Evolución Temporal ({tipo_ind_sel})")
    st.markdown("Comportamiento histórico agrupado mediante los campos **periodo** y **Periodo_Texto**.")
    
    if not df_filtrado.empty and "valor" in df_filtrado.columns:
        descripciones = sorted(df_filtrado["descripcion"].dropna().unique().tolist())
        
        default_desc = [d for d in descripciones if "nivel general" in d.lower()]
        if not default_desc:
            default_desc = descripciones[:3]
            
        desc_elegidas = st.multiselect(
            "Seleccionar Categorías / Descripciones:",
            options=descripciones,
            default=default_desc
        )
        
        if desc_elegidas:
            df_subset = df_filtrado[df_filtrado["descripcion"].isin(desc_elegidas)]
            
            pivot_chart = df_subset.pivot_table(
                index=["periodo", "Periodo_Texto"],
                columns="descripcion",
                values="valor",
                aggfunc="first"
            ).reset_index()
            
            pivot_chart = pivot_chart.sort_values("periodo")
            pivot_chart.set_index("Periodo_Texto", inplace=True)
            
            st.line_chart(pivot_chart.drop(columns=["periodo"], errors="ignore"), width="stretch")
        else:
            st.info("Seleccione al menos una categoría para graficar la serie temporal.")
    else:
        st.warning("No hay datos disponibles para los filtros seleccionados.")

with tab2:
    st.subheader("Estructura por Niveles y Clasificadores")
    st.markdown("Aprovecha los campos de la clave primaria: **clasificador**, **nivel**, **codigo**, **unidad_de_medida**.")
    
    if not df_filtrado.empty:
        niveles_disp = sorted(df_filtrado["nivel"].dropna().unique().tolist(), key=str)
        nivel_sel = st.selectbox("Filtrar por Nivel:", options=["Todos"] + niveles_disp)
        
        df_nivel = df_filtrado.copy()
        if nivel_sel != "Todos":
            df_nivel = df_nivel[df_nivel["nivel"] == nivel_sel]
            
        st.dataframe(
            df_nivel[["clasificador", "nivel", "codigo", "descripcion", "unidad_de_medida", "valor", "observaciones"]].drop_duplicates(),
            width="stretch"
        )
    else:
        st.warning("Sin datos para mostrar.")

with tab3:
    st.subheader("Explorador de Datos Crudos Oficiales")
    st.markdown("Visualización directa de la totalidad de columnas devueltas por la API del INDEC.")
    st.dataframe(df_filtrado, width="stretch")
    
    csv = df_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Descargar CSV Filtrado",
        data=csv,
        file_name="ipc_indec_filtrado.csv",
        mime="text/csv",
    )
