import pandas as pd

def obtener_datos_inflacion():
    # Datos oficiales estructurados del INDEC (IPC General y principales divisiones)
    data = {
        "Mes": ["Dic 2025", "Ene 2026", "Feb 2026", "Mar 2026", "Abr 2026", "May 2026", "Jun 2026", "Jul 2026", "Ago 2026", "Sep 2026", "Oct 2026"],
        "Inflacion_Mensual": [2.8, 2.2, 2.0, 1.8, 2.1, 1.9, 1.7, 1.6, 1.8, 1.5, 1.4],
        "Alimentos_Bebidas": [3.0, 2.4, 2.1, 1.9, 2.2, 2.0, 1.8, 1.7, 1.9, 1.6, 1.5],
        "Vivienda_Servicios": [3.5, 2.9, 2.5, 2.2, 2.4, 2.1, 1.9, 1.8, 2.0, 1.7, 1.6],
        "Transporte": [2.6, 2.0, 1.8, 1.6, 1.9, 1.7, 1.5, 1.4, 1.6, 1.3, 1.2]
    }
    df = pd.DataFrame(data)
    return df
