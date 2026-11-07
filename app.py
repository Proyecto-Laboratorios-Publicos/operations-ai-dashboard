import pandas as pd
import streamlit as st
from indec_data import obtener_datos_inflacion

st.set_page_config(page_title="Dashboard IPC - INDEC", page_icon="📊", layout="wide")

st.title("📊 Panel de Análisis Oficial - IPC INDEC")
st.markdown("Plataforma analítica conectada directamente al [Índice de Precios al Consumidor (IPC)](https://api.indec.gob.ar/datasets/ipc_nacional) del INDEC.")

@st.cache_data(ttl=3600)
def cargar():
    return obtener_datos_inflacion()

df = cargar()
if df.empty:
    st.error("No se pudieron recuperar datos de la API del INDEC.")
    st.stop()

st.sidebar.header("🎛️ Filtros Oficiales")
tipos = sorted(df["tipo_de_indicador_descripcion"].dropna().unique()) if "tipo_de_indicador_descripcion" in df else []
tipo_sel = st.sidebar.selectbox("Tipo de Indicador:", tipos) if tipos else "General"
df_f = df[df["tipo_de_indicador_descripcion"] == tipo_sel].copy() if tipos else df.copy()

regs = sorted(df_f["region"].dropna().unique()) if "region" in df_f else []
reg_sel = st.sidebar.selectbox("Región:", ["Todas"] + regs) if regs else "Todas"
if reg_sel != "Todas":
    df_f = df_f[df_f["region"] == reg_sel]

clas = sorted(df_f["clasificador"].dropna().unique()) if "clasificador" in df_f else []
clas_sel = st.sidebar.multiselect("Clasificador:", clas, default=clas) if clas else []
if clas_sel:
    df_f = df_f[df_f["clasificador"].isin(clas_sel)]

st.sidebar.divider()
st.sidebar.markdown(f"**Registros:** {len(df_f):,}")

t1, t2, t3 = st.tabs(["📈 Series Temporales", "📊 Niveles", "📋 Datos Crudos"])

with t1:
    st.subheader(f"Evolución Temporal ({tipo_sel})")
    if not df_f.empty and "valor" in df_f and "descripcion" in df_f:
        descs = sorted(df_f["descripcion"].dropna().unique())
        def_d = [d for d in descs if "nivel general" in d.lower()] or descs[:3]
        sel_d = st.multiselect("Categorías:", descs, default=def_d)
        if sel_d:
            sub = df_f[df_f["descripcion"].isin(sel_d)]
            pivot = sub.pivot_table(index=["periodo", "Periodo_Texto"], columns="descripcion", values="valor", aggfunc="first").reset_index()
            pivot = pivot.sort_values("periodo").set_index("Periodo_Texto")
            st.line_chart(pivot.drop(columns=["periodo"], errors="ignore"))
        else:
            st.info("Seleccione al menos una categoría.")
    else:
        st.warning("Sin datos disponibles.")

with t2:
    st.subheader("Estructura por Niveles")
    if not df_f.empty and "nivel" in df_f:
        nivs = sorted(df_f["nivel"].dropna().unique(), key=str)
        niv_sel = st.selectbox("Nivel:", ["Todos"] + nivs)
        df_n = df_f if niv_sel == "Todos" else df_f[df_f["nivel"] == niv_sel]
        cols = [c for c in ["clasificador", "nivel", "codigo", "descripcion", "unidad_de_medida", "valor"] if c in df_n]
        st.dataframe(df_n[cols].drop_duplicates(), use_container_width=True)

with t3:
    st.subheader("Explorador de Datos")
    st.dataframe(df_f, use_container_width=True)
    st.download_button("📥 Descargar CSV", df_f.to_csv(index=False).encode("utf-8"), "ipc_filtrado.csv", "text/csv")
