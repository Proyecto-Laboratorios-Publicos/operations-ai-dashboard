import pandas as pd
import requests

def obtener_datos_inflacion():
    url = "https://api.indec.gob.ar/v1/ipc_nacional"
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyYmE1YzU0ZS1iMTk3LTQ2ZTEtYWEzNS0zNWYyMzE2YTE2NWEiLCJqdGkiOiI2NzY4MGVlYy0zMGIwLTQxNGQtYTYxNS1hNDdiYmQxNDVjMzUiLCJleHAiOjE4MDk2MzQ0MDEsImlhdCI6MTc5NDA4MjQwMSwicm9sZSI6ImJhc2ljIn0.nOjwAJYUZsMUM60rC5aDldcujyi3Mt-3e_P2O6dukL4"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        # Siguiendo estrictamente la documentación oficial: orden estable por la clave completa y paginación
        params = {
            "order": "clasificador,nivel,codigo,descripcion,periodo,anio,mes,indicador,tipo_de_indicador,tipo_de_indicador_descripcion,region,unidad_de_medida",
            "limit": 1000
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                df = pd.DataFrame(data)
                
                if not df.empty:
                    # Mapeo de meses según los valores numéricos de la columna 'mes' (1 a 12)
                    meses_dict = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun", 
                                  7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}
                    
                    if "mes" in df.columns and "anio" in df.columns:
                        df["Mes_Texto"] = df["mes"].map(meses_dict) + " " + df["anio"].astype(int).astype(str)
                    
                    if "descripcion" in df.columns:
                        df["descripcion"] = df["descripcion"].astype(str).str.strip()
                    
                    # Filtramos por nivel nacional general y variaciones mensuales para construir la matriz que espera el dashboard
                    df_nacional = df.copy()
                    if "region" in df_nacional.columns:
                        # Si existen regiones, filtramos el total nacional para la visualización principal, conservando el resto en crudo
                        mask_nacional = df_nacional["region"].str.contains("Total del país|Total Nacional", case=False, na=False)
                        if mask_nacional.any():
                            df_nacional = df_nacional[mask_nacional]
                    
                    if {"Mes_Texto", "descripcion", "valor"}.issubset(df_nacional.columns):
                        pivot = df_nacional.pivot_table(
                            index=["Mes_Texto", "anio", "mes"],
                            columns="descripcion",
                            values="valor",
                            aggfunc="mean"
                        ).reset_index()
                        
                        pivot.columns.name = None
                        
                        # Mapeo seguro de nombres de columnas para que app.py los reconozca en los gráficos
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
                        
                        # Garantizamos columnas mínimas para evitar errores de renderizado en Streamlit
                        for col_req in ["Mes", "Inflacion_Mensual", "Alimentos_Bebidas", "Vivienda_Servicios", "Transporte", "Salud"]:
                            if col_req not in pivot.columns and col_req != "Mes":
                                pivot[col_req] = 0.0
                                
                        if "Mes" in pivot.columns and "Inflacion_Mensual" in pivot.columns:
                            pivot = pivot.sort_values(by=["anio", "mes"]).dropna(subset=["Inflacion_Mensual"])
                            return pivot

    except Exception as e:
        print(f"Error procesando API INDEC: {e}")

    return pd.DataFrame()
