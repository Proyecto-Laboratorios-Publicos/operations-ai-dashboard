import pandas as pd
import requests

def obtener_datos_inflacion():
    # URL oficial obtenida de la documentación del catálogo de la API del INDEC
    url = "https://api.indec.gob.ar/v1/ipc_nacional"
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyYmE1YzU0ZS1iMTk3LTQ2ZTEtYWEzNS0zNWYyMzE2YTE2NWEiLCJqdGkiOiI2NzY4MGVlYy0zMGIwLTQxNGQtYTYxNS1hNDdiYmQxNDVjMzUiLCJleHAiOjE4MDk2MzQ0MDEsImlhdCI6MTc5NDA4MjQwMSwicm9sZSI6ImJhc2ljIn0.nOjwAJYUZsMUM60rC5aDldcujyi3Mt-3e_P2O6dukL4"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    all_data = []
    offset = 0
    limit = 1000
    
    # Clave primaria completa requerida por la documentación para un orden estable en la paginación
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
                if not data or len(data) == 0:
                    break
                all_data.extend(data)
                if len(data) < limit:
                    break
                offset += limit
            else:
                print(f"Error API INDEC - Status Code: {response.status_code}")
                break
                
        if not all_data:
            return pd.DataFrame()
            
        # Creación del DataFrame con la totalidad de registros crudos
        df = pd.DataFrame(all_data)
        
        # Garantizar la presencia de todos los campos disponibles según la documentación oficial
        campos_oficiales = [
            "clasificador", "nivel", "codigo", "descripcion", "periodo", 
            "anio", "mes", "indicador", "tipo_de_indicador", 
            "tipo_de_indicador_descripcion", "region", "unidad_de_medida", 
            "valor", "observaciones"
        ]
        
        for campo in campos_oficiales:
            if campo not in df.columns:
                df[campo] = None
                
        # Normalización y tipado estricto de columnas numéricas
        df["anio"] = pd.to_numeric(df["anio"], errors="coerce")
        df["mes"] = pd.to_numeric(df["mes"], errors="coerce")
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
        
        # Limpieza y normalización de campos de texto
        for campo in [
            "clasificador", "nivel", "codigo", "descripcion", "periodo", 
            "indicador", "tipo_de_indicador", "tipo_de_indicador_descripcion", 
            "region", "unidad_de_medida", "observaciones"
        ]:
            df[campo] = df[campo].astype(str).str.strip().replace("nan", None)
            
        # Generación de columna auxiliar temporal legible para análisis (Ej: "Ene 2024")
        meses_dict = {
            1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun", 
            7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
        }
        
        df["Mes_Texto"] = df["mes"].map(meses_dict)
        df["Anio_Int"] = df["anio"].fillna(0).astype(int)
        df["Periodo_Texto"] = df["Mes_Texto"] + " " + df["Anio_Int"].astype(str)
        
        return df

    except Exception as e:
        print(f"Excepción crítica en obtener_datos_inflacion: {e}")

    return pd.DataFrame()
