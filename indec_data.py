import pandas as pd
import requests

def obtener_datos_inflacion():
    url = "https://api.indec.gob.ar/v1/ipc_nacional"
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyYmE1YzU0ZS1iMTk3LTQ2ZTEtYWEzNS0zNWYyMzE2YTE2NWEiLCJqdGkiOiI2NzY4MGVlYy0zMGIwLTQxNGQtYTYxNS1hNDdiYmQxNDVjMzUiLCJleHAiOjE4MDk2MzQ0MDEsImlhdCI6MTc5NDA4MjQwMSwicm9sZSI6ImJhc2ljIn0.nOjwAJYUZsMUM60rC5aDldcujyi3Mt-3e_P2O6dukL4"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    all_data = []
    offset = 0
    limit = 1000
    order_params = "clasificador,nivel,codigo,descripcion,periodo,anio,mes,indicador,tipo_de_indicador,tipo_de_indicador_descripcion,region,unidad_de_medida"
    
    try:
        while True:
            params = {
                "order": order_params,
                "limit": limit,
                "offset": offset
            }
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                if not data:
                    break
                all_data.extend(data)
                if len(data) < limit:
                    break
                offset += limit
            else:
                break
                
        if not all_data:
            return pd.DataFrame()
            
        df = pd.DataFrame(all_data)
        
        df["anio"] = pd.to_numeric(df["anio"], errors="coerce")
        df["mes"] = pd.to_numeric(df["mes"], errors="coerce")
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
        
        if "region" in df.columns:
            mask_reg = df["region"].astype(str).str.contains("Total del país|Total Nacional", case=False, na=False)
            if mask_reg.any():
                df = df[mask_reg]
                
        if "tipo_de_indicador" in df.columns:
            mask_ind = df["tipo_de_indicador"].astype(str).str.contains("variacion|mensual", case=False, na=False)
            if mask_ind.any():
                df = df[mask_ind]
                
        meses_dict = {
            1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun", 
            7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
        }
        if "mes" in df.columns and "anio" in df.columns:
            df["Mes"] = df["mes"].map(meses_dict) + " " + df["anio"].astype(int).astype(str)
            
        if "descripcion" in df.columns:
            df["descripcion"] = df["descripcion"].astype(str).str.strip()
            
        def map_desc(desc):
            d = desc.lower()
            if "nivel general" in d:
                return "Inflacion_Mensual"
            elif "alimentos y bebidas" in d:
                return "Alimentos_Bebidas"
            elif "vivienda" in d or ("agua" in d and "electricidad" in d):
                return "Vivienda_Servicios"
            elif "transporte" in d:
                return "Transporte"
            elif "salud" in d:
                return "Salud"
            return None

        df["categoria_std"] = df["descripcion"].apply(map_desc)
        df = df.dropna(subset=["categoria_std", "anio", "mes", "valor"])
        df = df.drop_duplicates(subset=["periodo", "categoria_std", "region"])
        
        if {"Mes", "anio", "mes", "categoria_std", "valor", "periodo"}.issubset(df.columns):
            pivot = df.pivot_table(
                index=["periodo", "Mes", "anio", "mes"],
                columns="categoria_std",
                values="valor",
                aggfunc="first"
            ).reset_index()
            
            pivot.columns.name = None
            pivot = pivot.loc[:, ~pivot.columns.duplicated(keep="first")]
            
            for col_req in ["Inflacion_Mensual", "Alimentos_Bebidas", "Vivienda_Servicios", "Transporte", "Salud"]:
                if col_req not in pivot.columns:
                    pivot[col_req] = 0.0
                    
            if "Mes" in pivot.columns and "Inflacion_Mensual" in pivot.columns:
                return pivot.sort_values(by=["anio", "mes"]).reset_index(drop=True)
                
    except Exception as e:
        print(f"Error: {e}")
        
    return pd.DataFrame()
