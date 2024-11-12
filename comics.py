import streamlit as st
import requests
import json
import base64
from typing import List
from io import BytesIO
from PIL import Image

# Set page configuration
st.set_page_config(
    page_title="Fábulas Ilustradas",
    page_icon="📖🎨",
    layout="wide",
)

# Title of the app
st.title("📖 Fábulas Ilustradas")

# Description
st.markdown("""
Esta aplicación permite a los usuarios pegar el texto de una fábula clásica. Utiliza la API de Together para extraer momentos clave de la fábula y generar ilustraciones a lápiz en blanco y negro para cada uno de ellos.
""")

# Input area for the fable
fable_text = st.text_area(
    "Pega el texto de la fábula aquí:",
    height=300,
    placeholder="Escribe o pega la fábula clásica que deseas ilustrar..."
)

# Function to extract key moments using Together's Chat Completions API
def get_key_moments(fable: str, api_key: str) -> List[str]:
    url = "https://api.together.xyz/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    messages = [
        {
            "role": "system",
            "content": "Extrae los momentos clave de la siguiente fábula. Devuelve una lista enumerada de momentos importantes."
        },
        {
            "role": "user",
            "content": fable
        }
    ]
    
    payload = {
        "model": "Qwen/Qwen2.5-7B-Instruct-Turbo",
        "messages": messages,
        "max_tokens": 1500,
        "temperature": 0.7,
        "top_p": 0.7,
        "top_k": 50,
        "repetition_penalty": 1,
        "stop": ["<|eot_id|>"],
        "stream": False
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code != 200:
        st.error(f"Error al extraer momentos clave: {response.text}")
        return []
    
    data = response.json()
    key_moments_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    # Procesar el texto para obtener una lista de momentos
    key_moments = []
    for line in key_moments_text.split('\n'):
        line = line.strip()
        if line and (line[0].isdigit() and line[1] == '.'):
            # Eliminar el número y el punto
            moment = line.split('.', 1)[1].strip()
            key_moments.append(moment)
    
    return key_moments

# Function to generate an image using Together's Image Generation API
def generate_image(prompt: str, api_key: str) -> Image.Image:
    url = "https://api.together.xyz/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Añadir detalles al prompt para asegurar el estilo deseado
    full_prompt = f"Dibujo a lápiz en blanco y negro de: {prompt}"
    
    payload = {
        "model": "black-forest-labs/FLUX.1.1-pro",
        "prompt": full_prompt,
        "width": 512,
        "height": 512,
        "steps": 50,  # Aumentar pasos para mejor calidad
        "n": 1,
        "response_format": "b64_json"
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code != 200:
        st.error(f"Error al generar la imagen: {response.text}")
        return None
    
    data = response.json()
    image_data = data.get("data", [])[0].get("b64_json", "")
    
    if not image_data:
        st.error("No se recibió imagen en la respuesta.")
        return None
    
    # Decodificar la imagen de base64
    image_bytes = base64.b64decode(image_data)
    image = Image.open(BytesIO(image_bytes))
    
    return image

# Check if API key is available
if "TOGETHER_API_KEY" not in st.secrets:
    st.error("Falta la clave API de Together. Por favor, agrega `TOGETHER_API_KEY` en los secretos de Streamlit.")
else:
    together_api_key = st.secrets["TOGETHER_API_KEY"]
    
    if st.button("Generar Ilustraciones"):
        if not fable_text.strip():
            st.warning("Por favor, pega el texto de una fábula para comenzar.")
        else:
            with st.spinner("Extrayendo momentos clave de la fábula..."):
                key_moments = get_key_moments(fable_text, together_api_key)
            
            if key_moments:
                st.success(f"Se han extraído {len(key_moments)} momentos clave.")
                
                st.markdown("### Ilustraciones Generadas")
                
                for idx, moment in enumerate(key_moments, 1):
                    st.markdown(f"**Momento {idx}:** {moment}")
                    with st.spinner(f"Generando imagen para el momento {idx}..."):
                        image = generate_image(moment, together_api_key)
                    
                    if image:
                        st.image(image, use_column_width=True)
            else:
                st.error("No se pudieron extraer momentos clave de la fábula.")

# Información adicional
st.markdown("""
---
**Nota:** Asegúrate de haber agregado tu clave API de Together en los secretos de Streamlit. Puedes hacerlo creando un archivo `secrets.toml` en la carpeta `.streamlit` con el siguiente contenido:

```toml
TOGETHER_API_KEY = "tu_clave_api_aquí"
