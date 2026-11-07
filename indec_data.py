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
                    # 1. Filtramos la región nacional
                    df_nacional = df[df["region"].str.contains("Total del país", case=False, na=False)].copy()
                    if df_nacional.empty:
                        df_nacional = df.copy()
                    
                    # 2. Formatear mes a texto
                    meses_dict = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun", 
                                  7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}
                    df_nacional["Mes_Texto"] = df_nacional["mes"].map(meses_dict) + " " + df_nacional["anio"].astype(int).astype(str)
                    
                    # 3. Filtrar variaciones mensuales o índices generales
                    df_filtrado = df_nacional[df_nacional["tipo_de_indicador"].str.contains("variacion|mensual", case=False, na=False)].copy()
                    
                    if not df_filtrado.empty:
                        # Limpiamos y normalizamos la descripción para evitar duplicados por mayúsculas/espacios
                        df_filtrado["descripcion"] = df_filtrado["descripcion"].astype(str).str.strip()
                        
                        # Creamos un pivote seguro agrupando por promedio si hay colisiones
                        pivot = df_filtrado.pivot_table(
                            index=["Mes_Texto", "anio", "mes"],
                            columns="descripcion",
                            values="valor",
                            aggfunc="mean"
                        ).reset_index()
                        
                        # Aplanamos los nombres de columnas por seguridad
                        pivot.columns.name = None
                        
                        # Buscamos dinámicamente las columnas clave basadas en coincidencias parciales
                        rename_dict = {"Mes_Texto": "Mes"}
                        for col in pivot.columns:
                            col_l = str(col).lower()
                            if "nivel general" in col_l:
                                rename_dict[col] = "Inflacion_Mensual"
                            elif "alimentos y bebidas" in col_l:
                                rename_dict[col] = "Alimentos_Bebidas"
                            elif "vivienda" in col_l or "agua" in col_l:
                                rename_dict[col] = "Vivienda_Servicios"
                            elif "transporte" in col_l:
                                rename_dict[col] = "Transporte"
                            elif "salud" in col_l:
                                rename_dict[col] = "Salud"
                                
                        pivot = pivot.rename(columns=rename_dict)
                        
                        # Eliminamos cualquier columna duplicada remanente en el eje de columnas
                        pivot = pivot.loc[:, ~pivot.columns.duplicated()]
                        
                        # Seleccionamos estrictamente solo las columnas que existan
                        cols_deseadas = ["Mes", "Inflacion_Mensual", "Alimentos_Bebidas", "Vivienda_Servicios", "Transporte", "Salud"]
                        cols_presentes = [c for c in cols_deseadas if c in pivot.columns]
                        
                        pivot = pivot[cols_presentes]
                        
                        if "Mes" in pivot.columns and "Inflacion_Mensual" in pivot.columns:
                            pivot = pivot.sort_values(by=["anio", "mes"]).dropna(subset=["Inflacion_Mensual"])
                            return pivot

    except Exception as e:
        print(f"Error procesando API INDEC: {e}")

    return pd.DataFrame()
