import html
import pandas as pd
import plotly.express as px
import streamlit as st
from indec_data import obtener_datos_inflacion
from groq_agent import consultar_agente_indec

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
        # Lee directamente el archivo estático ubicado en la raíz del repositorio
        df = pd.read_csv("ipc_indec_filtrado.csv")
        return df

# Llamas a la función tal como lo hacías antes
df_raw = cargar_datos()

# Diagnóstico visual amigable y detallado en caso de fallo de conexión o token
if df_raw.empty:
    st.error("⚠️ **No se pudieron recuperar datos desde la API del INDEC.**")
    with st.expander("🔍 Guía de resolución de problemas y posibles causas"):
        st.markdown("""
        Esto suele ocurrir por las siguientes razones:
        1. **Token JWT Expirado o Inválido:** El token Bearer configurado en el entorno o en el código ha caducado. Debe generar uno nuevo desde su perfil en el [Catálogo API-INDEC](https://api.indec.gob.ar/account).
        2. **Límite de cuota o caídas temporales:** El servidor de la API del INDEC podría estar experimentando mantenimiento temporal.
        3. **Configuración de Variables de Entorno:** Verifique que la variable `INDEC_API_TOKEN` esté configurada correctamente en los secretos de su despliegue en Streamlit Cloud.
        """)
    st.stop()

# Barra lateral de filtros oficiales basados estrictamente en la documentación
st.sidebar.header("🎛️ Filtros Oficiales API")

# 1. Selector obligatorio de Tipo de Indicador
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

# Contexto resumido para alimentar a Groq con los datos actuales filtrados
resumen_contexto = (
    f"Indicador seleccionado: {tipo_ind_sel}. "
    f"Total de registros filtrados: {len(df_filtrado)}. "
    f"Muestra reciente de datos: {df_filtrado.tail(15).to_string()}"
)

# Pestañas de análisis estructuradas (incluyendo el Dashboard original + Módulos de IA)
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
            
        desc_elegidas = st.multiselect(
            "Seleccionar Categorías / Descripciones:",
            options=descripciones,
            default=default_desc
        )
        
        if desc_elegidas:
            df_subset = df_filtrado[df_filtrado["descripcion"].isin(desc_elegidas)].copy()
            if not df_subset.empty:
                df_subset = df_subset.sort_values("periodo")
                
                # Gráfico interactivo con Plotly
                fig = px.line(
                    df_subset,
                    x="Periodo_Texto",
                    y="valor",
                    color="descripcion",
                    markers=True,
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
    st.download_button(
        label="📥 Descargar CSV Filtrado",
        data=csv,
        file_name="ipc_indec_filtrado.csv",
        mime="text/csv",
    )

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
    st.markdown("Crea resúmenes automáticos y descárgalos directamente en un documento formal listo para compartir.")
    tipo_reporte = st.selectbox("Selecciona el enfoque del reporte:", [
        "Resumen ejecutivo mensual de inflación", 
        "Análisis técnico de variaciones de precios para LinkedIn", 
        "Nota analítica sobre el comportamiento histórico"
    ])
    
    if st.button("🚀 Generar Reporte con IA y PDF"):
        with st.spinner("Redactando informe ejecutivo y compilando PDF corporativo..."):
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
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        import io

        # Generación elegante del PDF con ReportLab (sin errores de librerías externas)
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter, 
            rightMargin=50, 
            leftMargin=50, 
            topMargin=50, 
            bottomMargin=50
        )
        
        styles = getSampleStyleSheet()

        estilo_titulo = ParagraphStyle('TituloPDF', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=15, spaceAfter=2, textColor='#111827')
        estilo_subtitulo = ParagraphStyle('SubTituloPDF', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=11, spaceAfter=6, spaceBefore=10, textColor='#1d4ed8')
        estilo_cuerpo = ParagraphStyle('CuerpoPDF', parent=styles['Normal'], fontName='Helvetica', fontSize=9.5, leading=14, spaceAfter=6, textColor='#374151')
        estilo_meta = ParagraphStyle('MetaPDF', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=9, leading=12, spaceAfter=14, textColor='#6b7280')

        story = []
        
        # Encabezado formal corporativo
        story.append(Paragraph("<b>INFORME TÉCNICO OFICIAL - INDEC</b>", estilo_titulo))
        story.append(Paragraph(f"<b>Enfoque del análisis:</b> {tipo_reporte}", estilo_meta))
        story.append(Spacer(1, 6))

        # Procesamiento limpio y estructurado del texto del informe
        for linea in st.session_state["ultimo_informe"].split("\n"):
            linea_limpia = linea.strip()
            if linea_limpia:
                if "|" in linea_limpia or "---" in linea_limpia:
                    continue
                
                if linea_limpia.startswith("###") or linea_limpia.startswith("##"):
                    sub_txt = linea_limpia.replace("#", "").strip()
                    story.append(Paragraph(f"<b>{html.escape(sub_txt)}</b>", estilo_subtitulo))
                else:
                    formateado = linea_limpia.replace("**", "<b>", 1).replace("**", "</b>", 1)
                    formateado = formateado.replace("*", "•")
                    texto_seguro = html.escape(formateado).replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")
                    story.append(Paragraph(texto_seguro, estilo_cuerpo))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        st.success("¡PDF ejecutivo optimizado y listo para descargar!")
        st.download_button(
            label="📥 Descargar Reporte Ejecutivo en PDF", 
            data=pdf_bytes, 
            file_name="reporte_ejecutivo_indec.pdf", 
            mime="application/pdf"
        )
