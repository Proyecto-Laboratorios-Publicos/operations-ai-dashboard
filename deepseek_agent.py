import os
import requests
import streamlit as st

def consultar_agente_deepseek(prompt_usuario, contexto_datos=""):
    """
    Envía una consulta al modelo de DeepSeek junto con el contexto del DataFrame 
    filtrado del INDEC para que el agente actúe como un analista de operaciones.
    """
    # Obtenemos la API Key desde los secretos de Streamlit de forma segura
    api_key = os.getenv("DEEPSEEK_API_KEY")
    
    if not api_key:
        return "⚠️ **Atención:** No se encontró la variable de entorno `DEEPSEEK_API_KEY` en los secretos de Streamlit."

    # Endpoint oficial de DeepSeek (compatible con OpenAI)
    url = "https://api.deepseek.com/v1/chat/completions"
    
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
        "model": "deepseek-chat",  # O deepseek-reasoner según prefieras
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
            return f"⚠️ Error en la API de DeepSeek (Código {response.status_code}): {response.text}"
    except Exception as e:
        return f"⚠️ Excepción al conectar con el agente: {str(e)}"
