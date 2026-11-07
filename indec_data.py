import os
import pandas as pd
import requests

def obtener_datos_inflacion():
    # URL absoluta oficial correcta según la documentación de la API del INDEC
    url = "https://api.indec.gob.ar/v1/ipc_nacional"
    
    # Token JWT oficial de tu cuenta
    token = os.getenv(
        "INDEC_API_TOKEN", 
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyYmE1YzU0ZS1iMTk3LTQ2ZTEtYWEzNS0zNWYyMzE2YTE2NWEiLCJqdGkiOiJiNWU4ZTFhZC1kYzAzLTQ2MGEtYWI1Ni03MGM5YmJmNzRlNTUiLCJleHAiOjE4MDk2NDQxNTIsImlhdCI6MTc5NDA5MjE1Miwicm9sZSI6ImJhc2ljIn0.ijTrMytJVAndFhlUoCF7mJn0L7lQZcOK80saHbc9ovQ"
    )
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Prefer": "count=exact"
    }
    
    all_data = []
    offset = 0
    limit = 1000
    
    # Clave primaria completa obligatoria exigida por el INDEC para orden estable en paginación
    order_params = (
        "clasificador,nivel,codigo,descripcion,periodo,anio,mes,"
        "indicador,tipo_de_indicador,tipo_de_indicador_descripcion,region,unidad_de_medida"
    )
    
    try:
        while True:
            params = {
                "order": order_params,
                "limit": limit,
                "offset": offset
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            # PostgREST del INDEC devuelve 200 (OK) o 206 (Partial Content con count=exact)
            if response.status_code in [200, 206]:
                data = response.json()
                if not data or not isinstance(data, list) or len(data) == 0:
                    break
                
                all_data.extend(data)
                
                if len(data) < limit:
                    break
                offset += limit
            else:
                print(f"[ERROR API INDEC] Status Code: {response.status_code}")
                print(f"[DETALLES RESPUESTA]: {response.text}")
                break
                
        if not all_data:
            return pd.DataFrame()
            
        df = pd.DataFrame(all_data)
        
        # Tipado numérico estricto
        for col in ["anio", "mes", "valor", "nivel"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        
        # Limpieza de espacios y normalización de nulos en campos de texto
        campos_texto = [
            "clasificador", "nivel", "codigo", "descripcion", "periodo", 
            "indicador", "tipo_de_indicador", "tipo_de_indicador_descripcion", 
            "region", "unidad_de_medida", "observaciones"
        ]
        for campo in campos_texto:
            if campo in df.columns:
                df[campo] = df[campo].astype(str).str.strip().replace(["nan", "None", ""], None)
                
        # Columnas auxiliares temporales oficiales
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
            
        # Blindaje contra duplicados de columnas para evitar excepciones de PyArrow / Streamlit
        df = df.loc[:, ~df.columns.duplicated()].copy()
            
        return df

    except Exception as e:
        print(f"[EXCEPCIÓN CRÍTICA CONEXIÓN INDEC]: {e}")
        return pd.DataFrame()
