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
    
    # Orden estable obligatorio según la documentación oficial del Catálogo API-INDEC
    order_params = "clasificador,nivel,codigo,descripcion,periodo,anio,mes,indicador,tipo_de_indicador,tipo_de_indicador_descripcion,region,unidad_de_medida"
    
    try:
        while True:
            params = {
                "order": order_params,
                "limit": limit,
                "offset": offset
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if not data or not isinstance(data, list) or len(data) == 0:
                    break
                
                all_data.extend(data)
                
                if len(data) < limit:
                    break
                offset += limit
            else:
                print(f"DEBUG API INDEC - Status Code: {response.status_code}")
                break
                
        if not all_data:
            return pd.DataFrame()
            
        df = pd.DataFrame(all_data)
        
        # Tipado estricto exigido
        for col in ["anio", "mes", "valor", "nivel"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        
        # Limpieza de espacios en blanco en columnas de texto y nulos
        campos_texto = [
            "clasificador", "nivel", "codigo", "descripcion", "periodo", 
            "indicador", "tipo_de_indicador", "tipo_de_indicador_descripcion", 
            "region", "unidad_de_medida", "observaciones"
        ]
        for campo in campos_texto:
            if campo in df.columns:
                df[campo] = df[campo].astype(str).str.strip().replace(["nan", "None", ""], None)
                
        # Columnas auxiliares de lectura limpia para la traza temporal
        meses_dict = {
            1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun", 
            7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
        }
        
        if "mes" in df.columns and "anio" in df.columns:
            df["Mes_Texto"] = df["mes"].map(meses_dict).fillna("")
            df["Anio_Int"] = df["anio"].fillna(0).astype(int)
            df["Periodo_Texto"] = df["Mes_Texto"] + " " + df["Anio_Int"].astype(str)
        else:
            df["Periodo_Texto"] = df.get("periodo", "")
            
        # PREVENCIÓN CRÍTICA: Eliminar columnas duplicadas si existieran para evitar fallos de PyArrow
        df = df.loc[:, ~df.columns.duplicated()].copy()
            
        return df

    except Exception as e:
        print(f"Excepción crítica al conectar con la API del INDEC: {e}")
        return pd.DataFrame()
