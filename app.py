import html
import pandas as pd
import plotly.express as px
import streamlit as st
from indec_data import obtener_datos_inflacion
from groq_agent import consultar_agente_indec
from report_generator import generar_pdf_ejecutivo

# Configuración inicial de la página en modo ancho
st.set_page_config(
    page_title="Dashboard Oficial IPC - INDEC",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Panel de Análisis Oficial - IPC INDEC")
st.markdown("""
Plataforma analítica conectada directamente al [Índice de Precios al Consumidor (IPC)](https://api.indec.gob.ar/datasets/ipc_nacional) del INDEC.
Explora las series temporales oficiales explotando todos los campos disponibles y potenciada con Inteligencia Artificial.
""")

@st.cache_data(ttl=2592000)  # Caché por 30 días
def cargar_datos():
    with st.spinner("Cargando base de datos oficial del IPC (volando)..."):
        df = pd.read_csv("ipc_indec_filtrado.csv")
        return df

df_raw = cargar_datos()

if df_raw.empty:
    st.error("⚠️ **No se pudieron recuperar datos desde la API del INDEC.**")
    st.stop()

# Barra lateral de filtros oficiales
st.sidebar.header("🎛️ Filtros Oficiales API")

if "tipo_de_indicador_descripcion" in df_raw.columns:
    tipos_ind = sorted(df_raw["tipo_de_indicador_descripcion"].dropna().unique().astype(str).tolist())
    tipo_ind_sel = st.sidebar.selectbox("Tipo de Indicador:", options=tipos_ind) if tipos_ind else "General"
    df_filtrado = df_raw[df_raw["tipo_de_indicador_descripcion"] == tipo_ind_sel].copy() if tipos_ind else df_raw.copy()
else:
    df_filtrado = df_raw.copy()
    tipo_ind_sel = "General"

if "region" in df_filtrado.columns:
    regiones = sorted(df_filtrado["region"].dropna().unique().astype(str).tolist())
    region_sel = st.sidebar.selectbox("Región Estadística:", options=["Todas"] + regiones)
    if region_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado["region"] == region_sel]

if "clasificador" in df_filtrado.columns:
    clasificadores = sorted(df_filtrado["clasificador"].dropna().unique().astype(str).tolist())
    clasificador_sel = st.sidebar.multiselect("Clasificador:", options=clasificadores, default=clasificadores)
    if clasificador_sel:
        df_filtrado = df_filtrado[df_filtrado["clasificador"].isin(clasificador_sel)]

st.sidebar.divider()
st.sidebar.markdown(f"**Registros totales:** {len(df_raw):,}")
st.sidebar.markdown(f"**Registros filtrados:** {len(df_filtrado):,}")

resumen_contexto = (
    f"Indicador seleccionado: {tipo_ind_sel}. "
    f"Total de registros filtrados: {len(df_filtrado)}. "
    f"Muestra reciente de datos: {df_filtrado.tail(15).to_string()}"
)

# Pestañas de análisis estructuradas
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Series Temporales", 
    "📊 Niveles y Códigos", 
    "📋 Datos Crudos", 
    "💬 Asistente IA (Chat)", 
    "📝 Reportes Ejecutivos"
])

with tab1:
    st.subheader(f"Evolución Temporal ({tipo_ind_sel})")
    st.markdown("Comportamiento histórico agrupado mediante los campos **periodo** y **Periodo_Texto**.")
    if not df_filtrado.empty and "valor" in df_filtrado.columns and "descripcion" in df_filtrado.columns:
        descripciones = sorted(df_filtrado["descripcion"].dropna().unique().astype(str).tolist())
        default_desc = [d for d in descripciones if "nivel general" in d.lower()]
        if not default_desc:
            default_desc = descripciones[:3] if len(descripciones) >= 3 else descripciones
        desc_elegidas = st.multiselect("Seleccionar Categorías / Descripciones:", options=descripciones, default=default_desc)
        if desc_elegidas:
            df_subset = df_filtrado[df_filtrado["descripcion"].isin(desc_elegidas)].copy()
            if not df_subset.empty:
                df_subset = df_subset.sort_values("periodo")
                fig = px.line(
                    df_subset, x="Periodo_Texto", y="valor", color="descripcion", markers=True,
                    labels={"Periodo_Texto": "Período", "valor": "Valor del Indicador", "descripcion": "Categoría"}
                )
                fig.update_layout(
                    xaxis_tickangle=-45,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig, use_container_width=True)
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
        st.dataframe(df_nivel[columnas_mostrar].drop_duplicates(), use_container_width=True)
    else:
        st.warning("Sin datos para mostrar en este nivel.")

with tab3:
    st.subheader("Explorador de Datos Crudos Oficiales")
    st.markdown("Visualización directa de la totalidad de columnas devueltas por la API del INDEC.")
    st.dataframe(df_filtrado, use_container_width=True)
    csv = df_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button(label="📥 Descargar CSV Filtrado", data=csv, file_name="ipc_indec_filtrado.csv", mime="text/css")

with tab4:
    col1, col2 = st.columns([6, 1])
    with col1:
        st.subheader("💬 Asistente Inteligente de Datos (Groq)")
    with col2:
        if st.button("🔄 Reiniciar"):
            st.session_state.messages = []
            st.rerun()
    st.markdown("Interactúa en lenguaje natural para analizar los registros y tendencias actuales del INDEC.")
    if "messages" not in st.session_state:
        st.session_state.messages = []
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    if prompt := st.chat_input("Ej: ¿Cuál es el comportamiento de los rubros principales en este dataset?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Analizando series temporales con Groq..."):
                respuesta = consultar_agente_indec(prompt, resumen_contexto)
                st.markdown(respuesta)
                st.session_state.messages.append({"role": "assistant", "content": respuesta})

with tab5:
    st.subheader("📝 Generador de Reportes Ejecutivos en PDF")
    st.markdown("Crea resúmenes automáticos con gráficos integrados y descárgalos en un documento formal de nivel ejecutivo.")
    tipo_reporte = st.selectbox("Selecciona el enfoque del reporte:", [
        "Resumen ejecutivo mensual de inflación", 
        "Análisis técnico de variaciones de precios para LinkedIn", 
        "Nota analítica sobre el comportamiento histórico"
    ])
    
    if st.button("🚀 Generar Reporte con IA y PDF"):
        with st.spinner("Redactando informe, generando gráficos analíticos y compilando PDF corporativo..."):
            prompt_reporte = (
                f"Redacta un informe profesional titulado '{tipo_reporte}' "
                "basado estrictamente en los datos del INDEC proporcionados. "
                "Mantén un tono formal, técnico y analítico. "
                "REGLA ESTRICTA: NO utilices tablas de texto con barras (|) ni caracteres gráficos extraños. "
                "Utiliza únicamente títulos claros (con prefijo ###), párrafos explicativos bien desarrollados "
                "y listas con viñetas o guiones cortos para los datos cuantitativos."
            )
            informe_generado = consultar_agente_indec(prompt_reporte, resumen_contexto)
            st.session_state["ultimo_informe"] = informe_generado
            st.success("¡Informe generado con éxito!")
            
    if "ultimo_informe" in st.session_state and st.session_state["ultimo_informe"]:
        img_bytes = None
        if not df_filtrado.empty and "valor" in df_filtrado.columns and "Periodo_Texto" in df_filtrado.columns:
            df_chart = df_filtrado.tail(12)
            fig_pdf = px.line(
                df_chart, x="Periodo_Texto", y="valor", markers=True,
                title=f"<b>Tendencia Reciente - {tipo_ind_sel}</b>",
                labels={"Periodo_Texto": "Período", "valor": "Valor"}
            )
            fig_pdf.update_layout(
                width=650, height=240,
                margin=dict(l=30, r=30, t=40, b=30),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(size=10)
            )
            try:
                img_bytes = fig_pdf.to_image(format="png", scale=2)
            except Exception:
                img_bytes = None

        pdf_bytes = generar_pdf_ejecutivo(tipo_reporte, st.session_state["ultimo_informe"], img_bytes)
        
        st.success("¡PDF corporativo con gráficos integrados listo para descargar!")
        st.download_button(
            label="📥 Descargar Reporte Ejecutivo con Gráfico en PDF", 
            data=pdf_bytes, 
            file_name="reporte_ejecutivo_indec_con_grafico.pdf", 
            mime="application/pdf"
        )
