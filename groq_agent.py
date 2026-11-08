import os
import streamlit as st
from groq import Groq

def inicializar_cliente_groq():
    """Inicializa el cliente de Groq utilizando los secrets de Streamlit."""
    api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    return Groq(api_key=api_key)

def consultar_agente_indec(prompt_usuario, dataframe_resumen=""):
    """Envía el contexto de los datos del INDEC y la consulta del usuario a Groq."""
    cliente = inicializar_cliente_groq()
    if not cliente:
        return "⚠️ Falta configurar la GROQ_API_KEY en los secretos de Streamlit."
    
    system_prompt = (
        "Eres un analista económico senior experto en datos del INDEC (Argentina). "
        "Ayudas a interpretar series temporales de inflación, variaciones de precios y métricas operativas. "
        "Responde de forma clara, profesional y concisa basándote en los datos disponibles."
    )
    
    try:
        completion = cliente.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": f"{system_prompt}\n\nContexto de datos recientes:\n{dataframe_resumen}"},
                {"role": "user", "content": prompt_usuario}
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"❌ Error al consultar con Groq: {str(e)}"
