import pandas as pd
import requests

def obtener_datos_inflacion():
    url = "https://api.indec.gob.ar/v1/ipc_nacional"
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyYmE1YzU0ZS1iMTk3LTQ2ZTEtYWEzNS0zNWYyMzE2YTE2NWEiLCJqdGkiOiI2NzY4MGVlYy0zMGIwLTQxNGQtYTYxNS1hNDdiYmQxNDVjMzUiLCJleHAiOjE4MDk2MzQ0MDEsImlhdCI6MTc5NDA4MjQwMSwicm9sZSI6ImJhc2ljIn0.nOjwAJYUZsMUM60rC5aDldcujyi3Mt-3e_P2O6dukL4"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        # Orden estable y paginación según la documentación oficial de la API del INDEC
        params = {
            "order": "clasificador,nivel,codigo,descripcion,periodo,anio,mes,indicador,tipo_de_indicador,tipo_de_indicador_descripcion,region,unidad_de_medida",
            "limit": 1000
        }
        
        response = requests.get(url, headers=headers, params=params)
        print(f"DEBUG INDEC API - Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data:
                df = pd.DataFrame(data)
                print(f"DEBUG INDEC API - Total registros crudos obtenidos: {len(df)}")
                return df

    except Exception as e:
        print(f"Error conectando con la API del INDEC: {e}")

    return pd.DataFrame()
