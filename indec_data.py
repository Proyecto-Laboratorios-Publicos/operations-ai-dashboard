import pandas as pd
import requests

def obtener_datos_inflacion():
    url = "https://api.indec.gob.ar/v1/ipc_nacional"
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyYmE1YzU0ZS1iMTk3LTQ2ZTEtYWEzNS0zNWYyMzE2YTE2NWEiLCJqdGkiOiI2NzY4MGVlYy0zMGIwLTQxNGQtYTYxNS1hNDdiYmQxNDVjMzUiLCJleHAiOjE4MDk2MzQ0MDEsImlhdCI6MTc5NDA4MjQwMSwicm9sZSI6ImJhc2ljIn0.nOjwAJYUZsMUM60rC5aDldcujyi3Mt-3e_P2O6dukL4"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        # Solicitamos los datos ordenados por período según clave primaria
        params = {
            "limit": 1000,
            "order": "periodo.asc"
        }
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                df = pd.DataFrame(data)
                
                if {"periodo", "descripcion", "valor", "anio", "mes", "region", "nivel"}.issubset(df.columns):
                    # 1. Filtramos estrictamente la región nacional
                    df_nacional = df[df["region"].str.contains("Total del país", case=False, na=False)].copy()
                    if df_nacional.empty:
                        df_nacional = df.copy()
                    
                    # 2. Nos quedamos únicamente con el nivel macroeconómico principal (Divisiones / Nivel general)
                    # Esto evita duplicados masivos de clases, grupos y subclases.
                    df_nacional = df_nacional[df_nacional["nivel"].str.contains("División|Nivel general", case=False, na=False)].copy()
                    
                    # 3. Formateamos el mes a texto (ej: "Ene 2024")
                    meses_dict = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun", 
                                  7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}
                    
                    df_nacional["Mes_Texto"] = df_nacional["mes"].map(meses_dict) + " " + df_nacional["anio"].astype(int).astype(str)
                    
                    # 4. Filtramos variaciones mensuales
                    df_filtrado = df_nacional[df_nacional["tipo_de_indicador"].str.contains("variacion|mensual", case=False, na=False)].copy()
                    
                    # Eliminamos cualquier posible duplicado previo al pivot
                    df_filtrado = df_filtrado.drop_duplicates(subset=["periodo", "descripcion"])
                    
                    if not df_filtrado.empty:
                        pivot = df_filtrado.pivot_table(
                            index=["Mes_Texto", "anio", "mes"],
                            columns="descripcion",
                            values="valor",
                            aggfunc="first"
                        ).reset_index()
                        
                        # Limpiamos nombres de columnas
                        pivot.columns = [str(c).strip() for c in pivot.columns]
                        
                        # Diccionario de remapeo seguro e inteligente
                        rename_dict = {"Mes_Texto": "Mes"}
                        for col in pivot.columns:
                            col_l = col.lower()
                            if "nivel general" in col_l:
                                rename_dict[col] = "Inflacion_Mensual"
                            elif "alimentos y bebidas" in col_l and "Alimentos" in col:
                                rename_dict[col] = "Alimentos_Bebidas"
                            elif "vivienda" in col_l or "agua" in col_l:
                                rename_dict[col] = "Vivienda_Servicios"
                            elif "transporte" in col_l:
                                rename_dict[col] = "Transporte"
                            elif "salud" in col_l:
                                rename_dict[col] = "Salud"
                                
                        pivot = pivot.rename(columns=rename_dict)
                        
                        # Garantizamos columnas únicas eliminando duplicados de nombres si ocurren
                        pivot = pivot.loc[:, ~pivot.columns.duplicated()]
                        
                        cols_deseadas = ["Mes", "Inflacion_Mensual", "Alimentos_Bebidas", "Vivienda_Servicios", "Transporte", "Salud"]
                        cols_presentes = [c for c in cols_deseadas if c in pivot.columns]
                        
                        pivot = pivot[cols_presentes]
                        
                        if "Mes" in pivot.columns and "Inflacion_Mensual" in pivot.columns:
                            pivot = pivot.sort_values(by=["anio", "mes"]).dropna(subset=["Inflacion_Mensual"])
                            return pivot

    except Exception as e:
        print(f"Error en API INDEC: {e}")

    return pd.DataFrame()
