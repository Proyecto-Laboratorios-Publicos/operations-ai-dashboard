import pandas as pd
import requests

def obtener_datos_inflacion():
    url = "https://api.indec.gob.ar/v1/ipc_nacional"
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyYmE1YzU0ZS1iMTk3LTQ2ZTEtYWEzNS0zNWYyMzE2YTE2NWEiLCJqdGkiOiI2NzY4MGVlYy0zMGIwLTQxNGQtYTYxNS1hNDdiYmQxNDVjMzUiLCJleHAiOjE4MDk2MzQ0MDEsImlhdCI6MTc5NDA4MjQwMSwicm9sZSI6ImJhc2ljIn0.nOjwAJYUZsMUM60rC5aDldcujyi3Mt-3e_P2O6dukL4"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        params = {
            "limit": 1000,
            "order": "periodo.asc"
        }
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                df = pd.DataFrame(data)
                
                if {"periodo", "descripcion", "valor", "anio", "mes", "region"}.issubset(df.columns):
                    # Filtramos exclusivamente la región nacional
                    df_nacional = df[df["region"].str.contains("Total del país", case=False, na=False)].copy()
                    if df_nacional.empty:
                        df_nacional = df.copy()
                    
                    # Formateamos el mes a texto (ej: "Ene 2024")
                    meses_dict = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun", 
                                  7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}
                    
                    df_nacional["Mes_Texto"] = df_nacional["mes"].map(meses_dict) + " " + df_nacional["anio"].astype(int).astype(str)
                    
                    # Filtramos variaciones mensuales y eliminamos duplicados exactos en origen
                    df_filtrado = df_nacional[df_nacional["tipo_de_indicador"].str.contains("variacion|mensual|indice", case=False, na=False)].copy()
                    df_filtrado = df_filtrado.drop_duplicates(subset=["periodo", "descripcion"])
                    
                    if not df_filtrado.empty:
                        pivot = df_filtrado.pivot_table(
                            index=["Mes_Texto", "anio", "mes"],
                            columns="descripcion",
                            values="valor",
                            aggfunc="mean"  # Usamos mean por seguridad ante posibles solapamientos
                        ).reset_index()
                        
                        # Limpiamos nombres de columnas
                        pivot.columns = [str(c).strip() for c in pivot.columns]
                        
                        # Mapeo estricto y seguro de columnas clave
                        rename_dict = {"Mes_Texto": "Mes"}
                        for col in pivot.columns:
                            col_lower = col.lower()
                            if "nivel general" in col_lower and "Inflacion_Mensual" not in rename_dict.values():
                                rename_dict[col] = "Inflacion_Mensual"
                            elif "alimentos y bebidas" in col_lower and "Alimentos_Bebidas" not in rename_dict.values():
                                rename_dict[col] = "Alimentos_Bebidas"
                            elif ("vivienda" in col_lower or "agua" in col_lower) and "Vivienda_Servicios" not in rename_dict.values():
                                rename_dict[col] = "Vivienda_Servicios"
                            elif "transporte" in col_lower and "Transporte" not in rename_dict.values():
                                rename_dict[col] = "Transporte"
                            elif "salud" in col_lower and "Salud" not in rename_dict.values():
                                rename_dict[col] = "Salud"
                                
                        pivot = pivot.rename(columns=rename_dict)
                        
                        # Nos aseguramos de conservar solo las columnas mapeadas y únicas
                        cols_finales = ["Mes", "Inflacion_Mensual", "Alimentos_Bebidas", "Vivienda_Servicios", "Transporte", "Salud"]
                        cols_existentes = [c for c in cols_finales if c in pivot.columns]
                        
                        pivot = pivot[cols_existentes]
                        
                        # Eliminamos cualquier columna duplicada remanente en el DataFrame final
                        pivot = pivot.loc[:, ~pivot.columns.duplicated()]
                        
                        if "Mes" in pivot.columns and "Inflacion_Mensual" in pivot.columns:
                            pivot = pivot.sort_values(by=["Mes"]).dropna(subset=["Inflacion_Mensual"])
                            return pivot

    except Exception as e:
        print(f"Error procesando API INDEC: {e}")

    return pd.DataFrame()
