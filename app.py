import pandas as pd
import streamlit as st
from indec_data import obtener_datos_inflacion

st.set_page_config(
    page_title="Dashboard Oficial IPC - INDEC",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Panel Oficial de Análisis - IPC INDEC")
st.markdown("""
Plataforma analítica conectada directamente a la API oficial del **INDEC**. 
Explora las series temporales separando adecuadamente los tipos de indicadores (variaciones, índices, etc.) para garantizar métricas coherentes.
""")

df_raw = obtener_datos_inflacion()

if df_raw.empty:
    st.error("No se pudieron recuperar datos desde la API del INDEC.")
    st.stop()

# Sidebar de control y filtros estrictos
st.sidebar.header("🎛️ Filtros Oficiales")

# 1. Selector de Tipo de Indicador (Evita mezclar índices absolutos con variaciones porcentuales)
tipos_ind = sorted(df_raw["tipo_de_indicador_descripcion"].dropna().unique().tolist())
tipo_ind_sel = st.sidebar.selectbox(
    "Tipo de Indicador (Obligatorio):",
    options=tipos_ind
)

# Filtrar por el tipo de indicador seleccionado
df_ind = df_raw[df_raw["tipo_de_indicador_descripcion"] == tipo_ind_sel]

# 2. Filtro por Región
regiones = sorted(df_ind["region"].dropna().unique().tolist())
region_sel = st.sidebar.selectbox(
    "Región Estadística:",
    ["Todas"] + regiones
)

if region_sel != "Todas":
    df_ind = df_ind[df_ind["region"] == region_sel]

st.sidebar.divider()
st.sidebar.markdown(f"**Registros filtrados:** {len(df_ind):,}")

# Pestañas de análisis
tab1, tab2, tab3 = st.tabs([
    "📈 Series Temporales por Categoría",
    "📊 Comparativa por División (Último Período)",
    "📋 Explorador de Datos Crudos"
])

with tab1:
    st.subheader(f"Evolución Temporal - {tipo_ind_sel}")
    st.markdown("Gráfico de líneas limpio que compara las categorías seleccionadas bajo el mismo tipo de indicador.")
    
    if not df_ind.empty and "valor" in df_ind.columns:
        descripciones = sorted(df_ind["descripcion"].dropna().unique().tolist())
        
        # Seleccionar por defecto categorías de nivel general si existen
        default_desc = [d for d in descripciones if "nivel general" in d.lower()]
        if not default_desc:
            default_desc = descripciones[:3]
            
        desc_elegidas = st.multiselect(
            "Seleccionar Categorías / Divisiones:",
            options=descripciones,
            default=default_desc
        )
        
        if desc_elegidas:
            df_subset = df_ind[df_ind["descripcion"].isin(desc_elegidas)]
            
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
            st.info("Seleccione al menos una categoría para graficar.")
    else:
        st.warning("No hay datos disponibles para el filtro actual.")

with tab2:
    st.subheader("Desglose del Último Período")
    if not df_ind.empty and "periodo" in df_ind.columns:
        periodos_disp = sorted(df_ind["periodo"].dropna().unique().tolist(), reverse=True)
        if periodos_disp:
            p_sel = st.selectbox("Seleccionar Período (AAAAMM):", options=periodos_disp)
            
            df_periodo = df_ind[(df_ind["periodo"] == p_sel) & (df_ind["nivel"].astype(str).isin(["2", "2.0"]))]
            if df_periodo.empty:
                df_periodo = df_ind[df_ind["periodo"] == p_sel]
                
            st.bar_chart(df_periodo.set_index("descripcion")["valor"], width="stretch")
            st.dataframe(df_periodo[["clasificador", "nivel", "codigo", "descripcion", "unidad_de_medida", "valor"]], width="stretch")
    else:
        st.warning("Sin datos para mostrar.")

with tab3:
    st.subheader("Explorador de Datos")
    st.dataframe(df_ind, width="stretch")
    csv = df_ind.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Descargar CSV", data=csv, file_name="ipc_indec_filtrado.csv", mime="text/csv")
