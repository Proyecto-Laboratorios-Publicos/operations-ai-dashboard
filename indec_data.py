import pandas as pd
import requests

def obtener_datos_inflacion():
    # URL oficial del endpoint IPC Nacional según la documentación
    url = "https://api.indec.gob.ar/v1/ipc_nacional"
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyYmE1YzU0ZS1iMTk3LTQ2ZTEtYWEzNS0zNWYyMzE2YTE2NWEiLCJqdGkiOiI2NzY4MGVlYy0zMGIwLTQxNGQtYTYxNS1hNDdiYmQxNDVjMzUiLCJleHAiOjE4MDk2MzQ0MDEsImlhdCI6MTc5NDA4MjQwMSwicm9sZSI6ImJhc2ljIn0.nOjwAJYUZsMUM60rC5aDldcujyi3Mt-3e_P2O6dukL4"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        # Orden estable requerido por la clave completa de la API del INDEC
        params = {
            "order": "clasificador,nivel,codigo,descripcion,periodo,anio,mes,indicador,tipo_de_indicador,tipo_de_indicador_descripcion,region,unidad_de_medida",
            "limit": 1000
        }
        
        response = requests.get(url, headers=headers, params=params)
        print(f"DEBUG INDEC API - Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data:
                df = pd.DataFrame(data)
                print(f"DEBUG INDEC API - Total registros crudos obtenidos: {len(df)}")
                
                if not df.empty:
                    # Mapeo amigable de meses
                    meses_dict = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun", 
                                  7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}
                    
                    if "mes" in df.columns and "anio" in df.columns:
                        df["Mes_Texto"] = df["mes"].map(meses_dict) + " " + df["anio"].astype(int).astype(str)
                    
                    # Nos aseguramos de unificar descripciones textuales para evitar colisiones
                    if "descripcion" in df.columns:
                        df["descripcion"] = df["descripcion"].astype(str).str.strip()
                    
                    # Filtramos por variaciones mensuales generales a nivel nacional por defecto para las métricas del dashboard,
                    # pero conservando la estructura general intacta
                    df_base = df.copy()
                    
                    # Si el DataFrame tiene el formato esperado, armamos el pivote de manera segura para los gráficos
                    if {"Mes_Texto", "descripcion", "valor"}.issubset(df_base.columns):
                        # Filtramos filas clave del nivel general y divisiones principales para la región nacional si existe
                        if "region" in df_base.columns:
                            df_nacional = df_base[df_base["region"].str.contains("Total del país|Total Nacional", case=False, na=False)].copy()
                            if df_nacional.empty:
                                df_nacional = df_base.copy()
                        else:
                            df_nacional = df_base.copy()
                        
                        # Tomamos variaciones mensuales o índices según disponibilidad
                        df_var = df_nacional[df_nacional["tipo_de_indicador"].str.contains("variacion|mensual", case=False, na=False)].copy()
                        if df_var.empty:
                            df_var = df_nacional.copy()
                            
                        pivot = df_var.pivot_table(
                            index=["Mes_Texto", "anio", "mes"],
                            columns="descripcion",
                            values="valor",
                            aggfunc="mean"
                        ).reset_index()
                        
                        pivot.columns.name = None
                        
                        # Diccionario flexible para mapear columnas sin perder datos
                        rename_dict = {"Mes_Texto": "Mes"}
                        for col in pivot.columns:
                            col_l = str(col).lower()
                            if "nivel general" in col_l and "Inflacion_Mensual" not in rename_dict.values():
                                rename_dict[col] = "Inflacion_Mensual"
                            elif "alimentos y bebidas" in col_l and "Alimentos_Bebidas" not in rename_dict.values():
                                rename_dict[col] = "Alimentos_Bebidas"
                            elif ("vivienda" in col_l or "agua" in col_l) and "Vivienda_Servicios" not in rename_dict.values():
                                rename_dict[col] = "Vivienda_Servicios"
                            elif "transporte" in col_l and "Transporte" not in rename_dict.values():
                                rename_dict[col] = "Transporte"
                            elif "salud" in col_l and "Salud" not in rename_dict.values():
                                rename_dict[col] = "Salud"
                                
                        pivot = pivot.rename(columns=rename_dict)
                        pivot = pivot.loc[:, ~pivot.columns.duplicated()]
                        
                        # Asegurar columnas mínimas requeridas por app.py
                        for col_req in ["Mes", "Inflacion_Mensual", "Alimentos_Bebidas", "Vivienda_Servicios", "Transporte", "Salud"]:
                            if col_req not in pivot.columns and col_req != "Mes":
                                pivot[col_req] = 0.0
                                
                        if "Mes" in pivot.columns and "Inflacion_Mensual" in pivot.columns:
                            pivot = pivot.sort_values(by=["anio", "mes"]).dropna(subset=["Inflacion_Mensual"])
                            return pivot

    except Exception as e:
        print(f"Error procesando API INDEC: {e}")

    return pd.DataFrame()
