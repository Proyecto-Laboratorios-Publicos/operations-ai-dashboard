import pandas as pd
import requests

def obtener_datos_inflacion():
    # Endpoint oficial del IPC Nacional del INDEC
    url = "https://api.indec.gob.ar/v1/ipc_nacional"
    
    # Tu token JWT seguro verificado desde tu cuenta
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyYmE1YzU0ZS1iMTk3LTQ2ZTEtYWEzNS0zNWYyMzE2YTE2NWEiLCJqdGkiOiI2NzY4MGVlYy0zMGIwLTQxNGQtYTYxNS1hNDdiYmQxNDVjMzUiLCJleHAiOjE4MDk2MzQ0MDEsImlhdCI6MTc5NDA4MjQwMSwicm9sZSI6ImJhc2ljIn0.nOjwAJYUZsMUM60rC5aDldcujyi3Mt-3e_P2O6dukL4"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        # Petición paginada solicitando el histórico completo ordenado por clave primaria
        params = {
            "limit": 1000,
            "order": "periodo.asc"
        }
        response = requests.get(url, headers=headers, params=params)
        
        print(f"DEBUG INDEC API - Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data:
                df = pd.DataFrame(data)
                print(f"DEBUG INDEC API - Total registros obtenidos: {len(df)}")
                
                # Verificamos que contenga las columnas esenciales de la API
                if {"periodo", "descripcion", "valor", "anio", "mes", "region"}.issubset(df.columns):
                    
                    # Filtramos exclusivamente para la región Total del país
                    df_nacional = df[df["region"].str.contains("Total del país", case=False, na=False)].copy()
                    if df_nacional.empty:
                        df_nacional = df.copy() # Respaldo interno si varía la cadena exacta de región
                    
                    # Diccionario para mapear los números de mes a texto amigable (ej: "Ene 2024")
                    meses_dict = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun", 
                                  7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}
                    
                    df_nacional["Mes_Texto"] = df_nacional["mes"].map(meses_dict) + " " + df_nacional["anio"].astype(int).astype(str)
                    
                    # Filtramos por variaciones porcentuales mensuales o nivel general
                    df_filtrado = df_nacional[df_nacional["tipo_de_indicador"].str.contains("variacion|mensual|indice", case=False, na=False)].copy()
                    
                    if not df_filtrado.empty:
                        # Pivotamos la tabla para llevar las descripciones de las divisiones a columnas
                        pivot = df_filtrado.pivot_table(
                            index=["Mes_Texto", "anio", "mes"],
                            columns="descripcion",
                            values="valor",
                            aggfunc="first"
                        ).reset_index()
                        
                        # Mapeo de nombres oficiales devueltos por la API hacia las variables del dashboard
                        rename_map = {
                            "Mes_Texto": "Mes",
                            "Nivel general": "Inflacion_Mensual",
                            "Alimentos y bebidas no alcohólicas": "Alimentos_Bebidas",
                            "Vivienda, agua, electricidad, gas y otros combustibles": "Vivienda_Servicios",
                            "Transporte": "Transporte",
                            "Salud": "Salud"
                        }
                        
                        pivot = pivot.rename(columns=rename_map)
                        
                        # Validamos que las columnas mínimas existan
                        if "Mes" in pivot.columns and "Inflacion_Mensual" in pivot.columns:
                            pivot = pivot.sort_values(by=["anio", "mes"]).dropna(subset=["Inflacion_Mensual"])
                            
                            # Seleccionamos las columnas requeridas por el dashboard
                            available_cols = [col for col in ["Mes", "Inflacion_Mensual", "Alimentos_Bebidas", "Vivienda_Servicios", "Transporte", "Salud"] if col in pivot.columns]
                            print("DEBUG INDEC API - ¡Datos procesados y estructurados con éxito desde la API oficial!")
                            return pivot[available_cols]

    except Exception as e:
        print(f"Error crítico procesando la API del INDEC: {e}")

    # Si por alguna razón la API no retorna el set mapeable, levantamos un DataFrame vacío para depuración transparente
    print("DEBUG INDEC API - Advertencia: No se pudo mapear la estructura completa de la API.")
    return pd.DataFrame()
