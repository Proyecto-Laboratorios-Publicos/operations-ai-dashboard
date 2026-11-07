import pandas as pd
import requests

def obtener_datos_inflacion():
    url = "https://api.indec.gob.ar/v1/ipc_nacional"
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyYmE1YzU0ZS1iMTk3LTQ2ZTEtYWEzNS0zNWYyMzE2YTE2NWEiLCJqdGkiOiI2NzY4MGVlYy0zMGIwLTQxNGQtYTYxNS1hNDdiYmQxNDVjMzUiLCJleHAiOjE4MDk2MzQ0MDEsImlhdCI6MTc5NDA4MjQwMSwicm9sZSI6ImJhc2ljIn0.nOjwAJYUZsMUM60rC5aDldcujyi3Mt-3e_P2O6dukL4"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        # Solicitamos los datos ordenados cronológicamente
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
                    # Filtramos la región nacional principal
                    df_nacional = df[df["region"].str.contains("Total del país", case=False, na=False)].copy()
                    if df_nacional.empty:
                        df_nacional = df.copy()
                    
                    # Diccionario para formatear el mes
                    meses_dict = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun", 
                                  7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}
                    
                    df_nacional["Mes_Texto"] = df_nacional["mes"].map(meses_dict) + " " + df_nacional["anio"].astype(int).astype(str)
                    
                    # Filtramos por variaciones porcentuales mensuales para asegurar limpieza en los gráficos
                    df_filtrado = df_nacional[df_nacional["tipo_de_indicador"].str.contains("variacion|mensual|indice", case=False, na=False)].copy()
                    
                    if not df_filtrado.empty:
                        pivot = df_filtrado.pivot_table(
                            index=["Mes_Texto", "anio", "mes"],
                            columns="descripcion",
                            values="valor",
                            aggfunc="first"
                        ).reset_index()
                        
                        # Limpiamos nombres de columnas de niveles jerárquicos si existen
                        pivot.columns = [str(c).strip() for c in pivot.columns]
                        
                        # Mapeo exacto basado en los nombres reales que entrega la API
                        rename_dict = {"Mes_Texto": "Mes"}
                        for col in pivot.columns:
                            if "nivel general" in col.lower():
                                rename_dict[col] = "Inflacion_Mensual"
                            elif "alimentos" in col.lower():
                                rename_dict[col] = "Alimentos_Bebidas"
                            elif "vivienda" in col.lower() or "agua" in col.lower():
                                rename_dict[col] = "Vivienda_Servicios"
                            elif "transporte" in col.lower():
                                rename_dict[col] = "Transporte"
                            elif "salud" in col.lower():
                                rename_dict[col] = "Salud"
                                
                        pivot = pivot.rename(columns=rename_dict)
                        
                        if "Mes" in pivot.columns and "Inflacion_Mensual" in pivot.columns:
                            pivot = pivot.sort_values(by=["anio", "mes"]).dropna(subset=["Inflacion_Mensual"])
                            
                            # Aseguramos que las columnas clave existan para no romper los gráficos de Streamlit
                            for col_req in ["Alimentos_Bebidas", "Vivienda_Servicios", "Transporte", "Salud"]:
                                if col_req not in pivot.columns:
                                    pivot[col_req] = 0.0 # Rellenamos con 0 si alguna división no viene en el lote
                                    
                            return pivot[["Mes", "Inflacion_Mensual", "Alimentos_Bebidas", "Vivienda_Servicios", "Transporte", "Salud"]]

    except Exception as e:
        print(f"Error procesando API INDEC: {e}")

    # Si ocurre algún fallo de red, retornamos un DataFrame vacío controlado
    return pd.DataFrame()
