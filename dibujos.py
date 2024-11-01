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
Ingresa una descripción de la escena que deseas ilustrar y selecciona un estilo artístico. 
La aplicación transformará esta información en un prompt adecuado para el modelo FLUX de Stable Diffusion, 
incluyendo un prompt negativo para controlar la calidad y características de la imagen, 
y generará una imagen de 1024x768 píxeles.
""")

def transform_description_and_style_to_prompt(description, style):
    """
    Transforma la descripción de la escena y el estilo artístico en un prompt optimizado para el modelo FLUX 
    utilizando la API de OpenRouter, incluyendo un prompt negativo.
    """
    api_key = st.secrets["OPENROUTER_API_KEY"]
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Prompt negativo definido
    negative_prompt = "(no text, no hard edges, no vibrant colors, no harsh lighting, no digital art, no watermarks, no low resolution, no pixelation, no bad art, no beginner, no amateur)"
    
    # Prompt positivo basado en la entrada del usuario
    positive_prompt = f"{description}, {style}"
    
    # Construcción del prompt para OpenRouter siguiendo la estructura recomendada
    prompt_for_openrouter = (
        f"Transforma la siguiente descripción y estilo en un prompt detallado y optimizado para el modelo FLUX de Stable Diffusion:\n\n"
        f"Descripción: {description}\n"
        f"Estilo artístico: {style}\n\n"
        f"Prompt: {positive_prompt} {negative_prompt}"
    )
    
    data = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": prompt_for_openrouter
            }
        ]
    }
    
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        prompt = response.json()["choices"][0]["message"]["content"].strip()
        return prompt
    except requests.exceptions.HTTPError as http_err:
        st.error(f"Error HTTP al transformar la descripción y estilo: {http_err} - {response.text}")
    except Exception as e:
        st.error(f"Error al transformar la descripción y estilo: {e}")
    return None

def generate_image(prompt):
    """
    Genera una imagen utilizando la API de Together (Stable Diffusion) a partir de un prompt.
    La imagen tendrá un tamaño de 1024x768 píxeles utilizando el modelo FLUX.
    """
    api_key = st.secrets["TOGETHER_API_KEY"]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "black-forest-labs/FLUX.1-pro",
        "prompt": prompt,
        "width": 1024,
        "height": 768,
        "steps": 28,
        "n": 1,
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

# Opciones de estilos artísticos predefinidos
predefined_styles = [
    "realismo",
    "impresionismo",
    "expresionismo",
    "surrealismo",
    "arte abstracto",
    "arte digital",
    "estilo manga",
    "estilo de cómic",
    "arte minimalista",
    "arte pop",
    "cyberpunk",
    "arte gótico",
    "arte steampunk",
    "arte deco",
    "arte futurista"
]

# Entrada del usuario: Descripción de la escena
scene_description = st.text_area(
    "Descripción de la Escena",
    height=150,
    placeholder="Ingresa la descripción de la escena que deseas ilustrar aquí..."
)

# Selección del estilo artístico
st.markdown("**Selecciona un estilo artístico para la ilustración:**")
selected_style = st.selectbox(
    "Estilo Artístico",
    options=predefined_styles,
    index=0,
    help="Selecciona un estilo artístico para guiar la generación de la ilustración."
)

# Alternativamente, permitir que el usuario ingrese un estilo personalizado
custom_style = st.text_input(
    "O ingresa un estilo artístico personalizado",
    placeholder="Por ejemplo: cyberpunk, arte gótico, etc."
)

# Botón para generar la ilustración
if st.button("Generar Ilustración"):
    if not scene_description.strip():
        st.warning("Por favor, ingresa una descripción de la escena.")
    elif not (selected_style.strip() or custom_style.strip()):
        st.warning("Por favor, selecciona un estilo artístico o ingresa uno personalizado.")
    else:
        # Determinar el estilo a utilizar
        style_to_use = custom_style.strip() if custom_style.strip() else selected_style.strip()
        
        with st.spinner("Transformando la descripción y estilo en un prompt para el modelo FLUX..."):
            prompt = transform_description_and_style_to_prompt(scene_description, style_to_use)
        
        if prompt:
            st.subheader("Prompt Generado para el Modelo FLUX de Stable Diffusion")
            st.write(prompt)
            
            with st.spinner("Generando la imagen con el modelo FLUX de Stable Diffusion..."):
                image = generate_image(prompt)
        
            if image:
                st.subheader("Ilustración Generada")
                st.image(image, caption="Imagen generada por FLUX de Stable Diffusion", use_column_width=True)
            else:
                st.error("No se pudo generar la imagen.")
