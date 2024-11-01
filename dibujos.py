import streamlit as st
import requests
from io import BytesIO
from PIL import Image
import base64

# Configuración de la página
st.set_page_config(page_title="Generador de Ilustraciones de Escenas", layout="centered")

# Título de la aplicación
st.title("Generador de Ilustraciones de Escenas")

# Instrucciones
st.markdown("""
Ingresa una descripción de la escena que deseas ilustrar. La aplicación transformará esta descripción en un prompt adecuado para Stable Diffusion y generará una imagen de 512x512 píxeles.
""")

def transform_description_to_prompt(description):
    """
    Transforma la descripción de la escena en un prompt optimizado para Stable Diffusion utilizando la API de OpenRouter.
    """
    api_key = st.secrets["OPENROUTER_API_KEY"]
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": f"Transforma la siguiente descripción de una escena en un prompt detallado y optimizado para Stable Diffusion:\n\nDescripción: {description}\n\nPrompt:"
            }
        ]
    }
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        prompt = response.json()["choices"][0]["message"]["content"].strip()
        return prompt
    except requests.exceptions.HTTPError as http_err:
        st.error(f"Error HTTP al transformar la descripción: {http_err} - {response.text}")
    except Exception as e:
        st.error(f"Error al transformar la descripción: {e}")
    return None

def generate_image(prompt):
    """
    Genera una imagen utilizando la API de Together (Stable Diffusion) a partir de un prompt.
    La imagen tendrá un tamaño de 512x512 píxeles.
    """
    api_key = st.secrets["TOGETHER_API_KEY"]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "stabilityai/stable-diffusion-xl-base-1.0",
        "prompt": prompt,
        "width": 512,
        "height": 512,
        "steps": 40,
        "n": 1,
        "seed": 10000,
        "response_format": "b64_json"
    }
    try:
        response = requests.post("https://api.together.xyz/v1/images/generations", headers=headers, json=data)
        response.raise_for_status()
        response_data = response.json()
        # Decodificar la imagen de base64
        b64_image = response_data["data"][0]["b64_json"]
        image_bytes = base64.b64decode(b64_image)
        image = Image.open(BytesIO(image_bytes))
        return image
    except requests.exceptions.HTTPError as http_err:
        st.error(f"Error HTTP al generar la imagen: {http_err} - {response.text}")
    except Exception as e:
        st.error(f"Error al generar la imagen: {e}")
    return None

# Entrada del usuario: Descripción de la escena
scene_description = st.text_area("Descripción de la Escena", height=150, placeholder="Ingresa la descripción de la escena que deseas ilustrar aquí...")

# Botón para generar la ilustración
if st.button("Generar Ilustración"):
    if not scene_description.strip():
        st.warning("Por favor, ingresa una descripción de la escena.")
    else:
        with st.spinner("Transformando la descripción en un prompt para Stable Diffusion..."):
            prompt = transform_description_to_prompt(scene_description)
        
        if prompt:
            st.subheader("Prompt Generado para Stable Diffusion")
            st.write(prompt)
            
            with st.spinner("Generando la imagen con Stable Diffusion..."):
                image = generate_image(prompt)
            
            if image:
                st.subheader("Ilustración Generada")
                st.image(image, caption="Imagen generada por Stable Diffusion", use_column_width=True)
            else:
                st.error("No se pudo generar la imagen.")
