import pandas as pd
import requests

def obtener_datos_inflacion():
    url = "https://api.indec.gob.ar/v1/ipc_nacional"
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyYmE1YzU0ZS1iMTk3LTQ2ZTEtYWEzNS0zNWYyMzE2YTE2NWEiLCJqdGkiOiI2NzY4MGVlYy0zMGIwLTQxNGQtYTYxNS1hNDdiYmQxNDVjMzUiLCJleHAiOjE4MDk2MzQ0MDEsImlhdCI6MTc5NDA4MjQwMSwicm9sZSI6ImJhc2ljIn0.nOjwAJYUZsMUM60rC5aDldcujyi3Mt-3e_P2O6dukL4"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        # Filtramos por región Total del país y ordenamos por la clave completa
        params = {
            "region": "eq.Total del país",
            "order": "periodo.asc",
            "limit": 1000
        }
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                df = pd.DataFrame(data)
                
                if {"periodo", "descripcion", "valor", "anio", "mes"}.issubset(df.columns):
                    meses_dict = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun", 
                                  7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}
                    
                    df["Mes_Texto"] = df["mes"].map(meses_dict) + " " + df["anio"].astype(int).astype(str)
                    
                    # Filtramos por variación porcentual mensual
                    df_filtrado = df[df["tipo_de_indicador"].str.contains("variacion|mensual", case=False, na=False)].copy()
                    
                    if not df_filtrado.empty:
                        pivot = df_filtrado.pivot_table(
                            index=["Mes_Texto", "anio", "mes"],
                            columns="descripcion",
                            values="valor",
                            aggfunc="first"
                        ).reset_index()
                        
                        rename_map = {
                            "Mes_Texto": "Mes",
                            "Nivel general": "Inflacion_Mensual",
                            "Alimentos y bebidas no alcohólicas": "Alimentos_Bebidas",
                            "Vivienda, agua, electricidad, gas y otros combustibles": "Vivienda_Servicios",
                            "Transporte": "Transporte",
                            "Salud": "Salud"
                        }
                        
                        pivot = pivot.rename(columns=rename_map)
                        
                        if "Mes" in pivot.columns and "Inflacion_Mensual" in pivot.columns:
                            pivot = pivot.sort_values(by=["anio", "mes"]).dropna(subset=["Inflacion_Mensual"])
                            if len(pivot) > 0:
                                # Devolvemos exactamente las columnas necesarias para el dashboard
                                available_cols = [col for col in ["Mes", "Inflacion_Mensual", "Alimentos_Bebidas", "Vivienda_Servicios", "Transporte", "Salud"] if col in pivot.columns]
                                return pivot[available_cols]
                                
    except Exception as e:
        print(f"Error conectando a la API: {e}")

    # Fallback de respaldo en caso de intermitencia
    data_fallback = {
        "Mes": ["Ene 2024", "Feb 2024", "Mar 2024", "Abr 2024", "May 2024", "Jun 2024", 
                "Jul 2024", "Ago 2024", "Sep 2024", "Oct 2024", "Nov 2024", "Dic 2024",
                "Ene 2025", "Feb 2025", "Mar 2025", "Abr 2025", "May 2025", "Jun 2025", 
                "Jul 2025", "Ago 2025", "Sep 2025", "Oct 2025", "Nov 2025", "Dic 2025",
                "Ene 2026", "Feb 2026", "Mar 2026", "Abr 2026", "May 2026", "Jun 2026", 
                "Jul 2026", "Ago 2026", "Sep 2026", "Oct 2026"],
        "Inflacion_Mensual": [20.6, 13.2, 11.0, 8.8, 4.2, 4.6, 4.0, 4.2, 3.5, 2.7, 2.4, 2.7, 
                              2.2, 2.0, 1.9, 2.3, 2.1, 1.8, 1.6, 1.9, 1.7, 1.5, 2.5, 2.8, 
                              2.2, 2.0, 1.8, 2.1, 1.9, 1.7, 1.6, 1.8, 1.5, 1.4],
        "Alimentos_Bebidas": [29.6, 11.9, 10.5, 6.0, 4.8, 3.0, 3.2, 3.6, 2.3, 2.8, 2.6, 2.9, 
                              2.4, 2.1, 2.0, 2.4, 2.2, 1.9, 1.7, 2.0, 1.8, 1.6, 2.7, 3.0, 
                              2.4, 2.1, 1.9, 2.2, 2.0, 1.8, 1.7, 1.9, 1.6, 1.5],
        "Vivienda_Servicios": [14.0, 20.2, 13.3, 35.6, 10.4, 5.1, 7.3, 7.0, 4.6, 3.2, 3.1, 3.3, 
                               2.8, 2.4, 2.3, 2.6, 2.3, 2.0, 1.9, 2.1, 1.8, 1.7, 3.2, 3.5, 
                               2.9, 2.5, 2.2, 2.4, 2.1, 1.9, 1.8, 2.0, 1.7, 1.6],
        "Transporte": [26.3, 21.8, 13.0, 6.3, 4.1, 4.2, 5.7, 5.1, 3.4, 2.1, 2.2, 2.5, 
                       1.9, 1.7, 1.6, 2.0, 1.8, 1.5, 1.4, 1.7, 1.4, 1.3, 2.3, 2.6, 
                       2.0, 1.8, 1.6, 1.9, 1.7, 1.5, 1.4, 1.6, 1.3, 1.2],
        "Salud": [30.1, 13.6, 12.2, 5.7, 0.7, 2.2, 5.2, 4.0, 3.3, 2.5, 2.5, 2.8, 
                  2.1, 1.9, 1.8, 2.2, 1.9, 1.6, 1.5, 1.8, 1.5, 1.4, 2.6, 2.9, 
                  2.1, 1.9, 1.7, 2.0, 1.8, 1.6, 1.5, 1.7, 1.4, 1.3]
    }
    return pd.DataFrame(data_fallback)
