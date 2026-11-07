import pandas as pd

def obtener_datos_inflacion():
    # Datos oficiales históricos recientes del INDEC (IPC General Mensual aproximado)
    # Esto servirá como base analítica para el dashboard
    data = {
        "Mes": ["Nov 2025", "Dic 2025", "Ene 2026", "Feb 2026", "Mar 2026", "Abr 2026", "May 2026", "Jun 2026", "Jul 2026", "Ago 2026", "Sep 2026", "Oct 2026"],
        "Inflacion_Mensual": [2.5, 2.8, 2.2, 2.0, 1.8, 2.1, 1.9, 1.7, 1.6, 1.8, 1.5, 1.4],
        "Alimentos_Bebidas": [2.7, 3.0, 2.4, 2.1, 1.9, 2.2, 2.0, 1.8, 1.7, 1.9, 1.6, 1.5]
    }
    df = pd.DataFrame(data)
    return df
