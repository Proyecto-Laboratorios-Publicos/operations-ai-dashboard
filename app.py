import pandas as pd
import streamlit as st
from indec_data import obtener_datos_inflacion

# Configuración inicial de la página en modo ancho
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

# Diagnóstico visual amigable y detallado en caso de fallo de conexión o token
if df_raw.empty:
    st.error("⚠️ **No se pudieron recuperar datos desde la API del INDEC.**")
    with st.expander("🔍 Guía de resolución de problemas y posibles causas"):
        st.markdown("""
        Esto suele ocurrir por las siguientes razones:
        1. **Token JWT Expirado o Inválido:** El token Bearer configurado en el entorno o en el código ha caducado. Debe generar uno nuevo desde su perfil en el [Catálogo API-INDEC](https://api.indec.gob.ar/docs).
        2. **Límite de cuota o caídas temporales:** El servidor de la API del INDEC podría estar experimentando mantenimiento temporal.
        3. **Configuración de Variables de Entorno:** Verifique que la variable `INDEC_API_TOKEN` esté configurada correctamente en los secretos o ajustes de su despliegue en Streamlit Cloud.
        """)
    st.stop()

# Barra lateral de filtros oficiales basados estrictamente en la documentación
st.sidebar.header("🎛️ Filtros Oficiales API")

# 1. Selector obligatorio de Tipo de Indicador para evitar mezclar métricas heterogéneas
if "tipo_de_indicador_descripcion" in df_raw.columns:
    tipos_ind = sorted(df_raw["tipo_de_indicador_descripcion"].dropna().unique().astype(str).tolist())
    tipo_ind_sel = st.sidebar.selectbox("Tipo de Indicador:", options=tipos_ind) if tipos_ind else "General"
    df_filtrado = df_raw[df_raw["tipo_de_indicador_descripcion"] == tipo_ind_sel].copy() if tipos_ind else df_raw.copy()
else:
    df_filtrado = df_raw.copy()
    tipo_ind_sel = "General"

# 2. Selector de Región Estadística
if "region" in df_filtrado.columns:
    regiones = sorted(df_filtrado["region"].dropna().unique().astype(str).tolist())
    region_sel = st.sidebar.selectbox("Región Estadística:", options=["Todas"] + regiones)
    if region_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado["region"] == region_sel]

# 3. Multiselector de Clasificadores
if "clasificador" in df_filtrado.columns:
    clasificadores = sorted(df_filtrado["clasificador"].dropna().unique().astype(str).tolist())
    clasificador_sel = st.sidebar.multiselect("Clasificador:", options=clasificadores, default=clasificadores)
    if clasificador_sel:
        df_filtrado = df_filtrado[df_filtrado["clasificador"].isin(clasificador_sel)]

st.sidebar.divider()
st.sidebar.markdown(f"**Registros totales:** {len(df_raw):,}")
st.sidebar.markdown(f"**Registros filtrados:** {len(df_filtrado):,}")

# Pestañas de análisis estructuradas
tab1, tab2, tab3 = st.tabs([
    "📈 Series Temporales por Descripción",
    "📊 Desglose de Niveles y Códigos",
    "📋 Explorador de Datos Crudos"
])

with tab1:
    st.subheader(f"Evolución Temporal ({tipo_ind_sel})")
    st.markdown("Comportamiento histórico agrupado mediante los campos **periodo** y **Periodo_Texto**.")
    
    if not df_filtrado.empty and "valor" in df_filtrado.columns and "descripcion" in df_filtrado.columns:
        descripciones = sorted(df_filtrado["descripcion"].dropna().unique().astype(str).tolist())
        
        default_desc = [d for d in descripciones if "nivel general" in d.lower()]
        if not default_desc:
            default_desc = descripciones[:3] if len(descripciones) >= 3 else descripciones
            
        desc_elegidas = st.multiselect(
            "Seleccionar Categorías / Descripciones:",
            options=descripciones,
            default=default_desc
        )
        
        if desc_elegidas:
            df_subset = df_filtrado[df_filtrado["descripcion"].isin(desc_elegidas)].copy()
            
            if not df_subset.empty:
                pivot_chart = df_subset.pivot_table(
                    index=["periodo", "Periodo_Texto"],
                    columns="descripcion",
                    values="valor",
                    aggfunc="first"
                ).reset_index()
                
                pivot_chart = pivot_chart.sort_values("periodo")
                pivot_chart.set_index("Periodo_Texto", inplace=True)
                
                # Sintaxis actualizada recomendada (Streamlit 1.40+)
                st.line_chart(pivot_chart.drop(columns=["periodo"], errors="ignore"), width="stretch")
            else:
                st.warning("No hay registros para las categorías seleccionadas.")
        else:
            st.info("Seleccione al menos una categoría para graficar la serie temporal.")
    else:
        st.warning("No hay datos disponibles para los filtros seleccionados.")

with tab2:
    st.subheader("Estructura por Niveles y Clasificadores")
    st.markdown("Aprovecha los campos de la clave primaria: **clasificador**, **nivel**, **codigo**, **unidad_de_medida**.")
    
    if not df_filtrado.empty and "nivel" in df_filtrado.columns:
        nivs_unicos = sorted(df_filtrado["nivel"].dropna().unique().tolist(), key=lambda x: str(x))
        niveles_disp = [str(n) for n in nivs_unicos]
        nivel_sel = st.selectbox("Filtrar por Nivel:", options=["Todos"] + niveles_disp)
        
        df_nivel = df_filtrado.copy()
        if nivel_sel != "Todos":
            df_nivel = df_nivel[df_nivel["nivel"].astype(str) == nivel_sel]
            
        columnas_mostrar = [col for col in ["clasificador", "nivel", "codigo", "descripcion", "unidad_de_medida", "valor", "observaciones"] if col in df_nivel.columns]
        st.dataframe(df_nivel[columnas_mostrar].drop_duplicates(), width="stretch")
    else:
        st.warning("Sin datos para mostrar en este nivel.")

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
