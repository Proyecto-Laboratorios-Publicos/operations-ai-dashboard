import os
import requests
import streamlit as st

def consultar_agente_deepseek(prompt_usuario, contexto_datos=""):
    """
    Envía una consulta al modelo alojado en Groq junto con el contexto del DataFrame 
    filtrado del INDEC para que actúe como un analista de operaciones.
    """
    # Obtenemos la API Key desde los secretos de Streamlit (puedes nombrar la variable GROQ_API_KEY)
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        return "⚠️ **Atención:** No se encontró la variable de entorno `GROQ_API_KEY` en los secretos de Streamlit."

    # Endpoint oficial de Groq (100% compatible con OpenAI)
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    # System prompt para darle el rol de Analista de Operaciones e Inflación
    system_prompt = (
        "Eres el Agente IA de Operaciones del Dashboard Económico-Operativo de INDEC. "
        "Tu objetivo es ayudar a auditar y analizar los datos de inflación, series temporales "
        "y métricas del servicio de manera clara, profesional y basada estrictamente en los datos provistos."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Contexto de datos actuales del panel:\n{contexto_datos}\n\nPregunta del usuario: {prompt_usuario}"}
    ]

    payload = {
        "model": "llama-3.3-70b-versatile",  # Uno de los mejores modelos abiertos y gratuitos en Groq
        "messages": messages,
        "temperature": 0.3,
        "stream": False
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        else:
            return f"⚠️ Error en la API de Groq (Código {response.status_code}): {response.text}"
    except Exception as e:
        return f"⚠️ Excepción al conectar con el agente: {str(e)}"
