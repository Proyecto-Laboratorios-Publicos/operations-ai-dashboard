import pandas as pd
import streamlit as st
from indec_data import obtener_datos_inflacion

# Configuración de la página
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

# Cargar base de datos cruda
df_raw = obtener_datos_inflacion()

df_indec = pd.DataFrame()

if not df_raw.empty:
  df_proc = df_raw.copy()
  
  # Filtramos Total del País si existe la columna region
  if "region" in df_proc.columns:
    mask = df_proc["region"].str.contains("Total del país|Total Nacional", case=False, na=False)
    if mask.any():
      df_proc = df_proc[mask]

  # Mapeo de meses numéricos a texto amigable
  meses_dict = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun", 
                7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}
                
  if "mes" in df_proc.columns and "anio" in df_proc.columns:
    df_proc["Mes_Texto"] = df_proc["mes"].map(meses_dict) + " " + df_proc["anio"].astype(int).astype(str)

  if "descripcion" in df_proc.columns:
    df_proc["descripcion"] = df_proc["descripcion"].astype(str).str.strip()

  # Construcción del pivot table asegurando unicidad de columnas
  if {"Mes_Texto", "descripcion", "valor"}.issubset(df_proc.columns):
    pivot = df_proc.pivot_table(
        index=["Mes_Texto", "anio", "mes"],
        columns="descripcion",
        values="valor",
        aggfunc="mean"
    ).reset_index()
    
    pivot.columns.name = None

    rename_dict = {"Mes_Texto": "Mes"}
    for col in pivot.columns:
      col_l = str(col).lower()
      if "nivel general" in col_l:
        rename_dict[col] = "Inflacion_Mensual"
      elif "alimentos" in col_l:
        rename_dict[col] = "Alimentos_Bebidas"
      elif "vivienda" in col_l or "agua" in col_l:
        rename_dict[col] = "Vivienda_Servicios"
      elif "transporte" in col_l:
        rename_dict[col] = "Transporte"
      elif "salud" in col_l:
        rename_dict[col] = "Salud"

    pivot = pivot.rename(columns=rename_dict)
    pivot = pivot.loc[:, ~pivot.columns.duplicated()]

    for req in ["Mes", "Inflacion_Mensual", "Alimentos_Bebidas", "Vivienda_Servicios", "Transporte", "Salud"]:
      if req not in pivot.columns and req != "Mes":
        pivot[req] = 0.0

    if "Mes" in pivot.columns and "Inflacion_Mensual" in pivot.columns:
      df_indec = pivot.sort_values(by=["anio", "mes"]).dropna(subset=["Inflacion_Mensual"])

# Barra lateral con controles y filtros
st.sidebar.header("Panel de Control & Filtros")
if not df_indec.empty:
  st.sidebar.success("Estado: Conectado a la API oficial en vivo.")
else:
  st.sidebar.error("Estado: Procesando o sin datos disponibles.")

opcion_historica = st.sidebar.selectbox(
    "Rango temporal de análisis:",
    [
        "Último año (12 meses)",
        "Últimos 2 años (24 meses)",
        "Histórico Completo",
    ],
)

if not df_indec.empty:
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
    ultimo_mes = df_indec.iloc[-1]["Mes"] if len(df_indec) == 1 else "Actual"
    ultima_inflacion = df_indec.iloc[-1]["Inflacion_Mensual"] if len(df_indec) == 1 else 0.0
    delta_inflacion = 0.0

  st.sidebar.markdown(f"**Última actualización:** {ultimo_mes}")
  st.sidebar.markdown(f"**Total períodos en sistema:** {len(df_indec)}")
else:
  df_filtrado = pd.DataFrame()
  ultimo_mes = "N/A"
  ultima_inflacion = 0.0
  delta_inflacion = 0.0

# Pestañas de navegación
tab1, tab2, tab3 = st.tabs([
    "📈 Resumen General y Métricas",
    "📊 Análisis Sectorial por Divisiones",
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
    promedio_movil = round(df_filtrado["Inflacion_Mensual"].mean(), 2) if not df_filtrado.empty else 0.0
    st.metric(
        label="Promedio Móvil (Período Seleccionado)",
        value=f"{promedio_movil}%",
    )
  with col3:
    max_mensual = df_filtrado["Inflacion_Mensual"].max() if not df_filtrado.empty else 0.0
    st.metric(
        label="Máximo Mensual del Período",
        value=f"{max_mensual}%"
    )

  st.divider()
  st.subheader(f"📈 Evolución Histórica ({opcion_historica})")
  if not df_filtrado.empty:
    cols_grafico = [c for c in ["Inflacion_Mensual", "Alimentos_Bebidas", "Vivienda_Servicios", "Transporte", "Salud"] if c in df_filtrado.columns]
    st.line_chart(df_filtrado.set_index("Mes")[cols_grafico], width="stretch")
  else:
    st.warning("No hay datos históricos para mostrar en el gráfico.")

with tab2:
  st.subheader("Comparativa y Tendencia por División")
  col_a, col_b = st.columns(2)
  with col_a:
    st.markdown(f"### Desglose del Último Mes ({ultimo_mes})")
    if not df_indec.empty:
      cols_desglose = [c for c in ["Alimentos_Bebidas", "Vivienda_Servicios", "Transporte", "Salud"] if c in df_indec.columns]
      if cols_desglose:
        ultimo_registro = df_indec.iloc[-1][cols_desglose].reset_index()
        ultimo_registro.columns = ["Division", "Porcentaje"]
        st.bar_chart(ultimo_registro.set_index("Division"), width="stretch")
      else:
        st.info("No hay columnas sectoriales disponibles.")
    else:
      st.warning("Sin datos para mostrar.")
  with col_b:
    st.markdown(f"### Tendencia Acumulada ({opcion_historica})")
    if not df_filtrado.empty and cols_grafico:
      st.area_chart(df_filtrado.set_index("Mes")[cols_grafico], width="stretch")
    else:
      st.warning("Sin datos para graficar tendencias.")

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
