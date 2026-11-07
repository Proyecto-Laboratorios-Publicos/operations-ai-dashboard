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
            "region": "eq.Total del país",
            "limit": 10000,
            "order": "periodo.asc"
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                df = pd.DataFrame(data)
                
                if not df.empty:
                    df["anio"] = pd.to_numeric(df["anio"], errors="coerce")
                    df["mes"] = pd.to_numeric(df["mes"], errors="coerce")
                    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
                    df["descripcion"] = df["descripcion"].astype(str).str.strip()
                    
                    if "tipo_de_indicador" in df.columns:
                        df = df[df["tipo_de_indicador"].str.contains("variacion|mensual", case=False, na=False)]
                    
                    meses_dict = {
                        1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun", 
                        7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
                    }
                    df["Mes"] = df["mes"].map(meses_dict) + " " + df["anio"].astype(int).astype(str)
                    
                    df = df.drop_duplicates(subset=["periodo", "descripcion"])
                    
                    pivot = df.pivot_table(
                        index=["Mes", "anio", "mes"],
                        columns="descripcion",
                        values="valor",
                        aggfunc="mean"
                    ).reset_index()
                    
                    pivot.columns.name = None
                    
                    rename_dict = {}
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
                    pivot = pivot.loc[:, ~pivot.columns.duplicated()]
                    
                    for col_req in ["Inflacion_Mensual", "Alimentos_Bebidas", "Vivienda_Servicios", "Transporte", "Salud"]:
                        if col_req not in pivot.columns:
                            pivot[col_req] = 0.0
                            
                    if "Mes" in pivot.columns and "Inflacion_Mensual" in pivot.columns:
                        return pivot.sort_values(by=["anio", "mes"]).reset_index(drop=True)

    except Exception as e:
        print(f"Error: {e}")

    return pd.DataFrame()
