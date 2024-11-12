import streamlit as st
import requests
import base64
from io import StringIO
from datetime import datetime
import json

# Configuración de la página
st.set_page_config(
    page_title="Generador de Ilustraciones para Cuentos",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Título de la aplicación
st.title("Generador de Ilustraciones para Cuentos con Streamlit y Together API")

# Instrucciones
st.markdown("""
Esta aplicación permite subir un archivo de texto que contiene varios cuentos. Para cada cuento, se extraen momentos clave utilizando la API de Together y se generan ilustraciones de arte digital imitando el estilo del siglo XVIII, a lápiz y en blanco y negro.

**Pasos:**
1. Sube un archivo de texto con tus cuentos.
2. Para cada cuento, haz clic en "Extraer Momentos Clave".
3. Una vez extraídos los momentos clave, haz clic en "Generar Ilustración".
4. Visualiza y descarga las ilustraciones generadas.
""")

# Inicializar el estado de sesión para almacenar momentos clave y imágenes
if 'key_moments' not in st.session_state:
    st.session_state['key_moments'] = {}
if 'images' not in st.session_state:
    st.session_state['images'] = {}

# Función para extraer momentos clave utilizando la API de Together
def extract_key_moments_with_together(cuento, api_key, cuento_id):
    url = "https://api.together.xyz/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    prompt = (
        "Analiza el siguiente cuento y extrae los tres momentos más importantes o destacados. "
        "Proporciona una lista numerada con cada momento.\n\n"
        f"Cuento:\n{cuento}\n\nMomentos Clave:"
    )
    payload = {
        "model": "Qwen/Qwen2.5-7B-Instruct-Turbo",
        "messages": [
            {"role": "system", "content": "Eres un asistente que ayuda a extraer los momentos clave de un cuento."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 512,
        "temperature": 0.7,
        "top_p": 0.7,
        "top_k": 50,
        "repetition_penalty": 1,
        "stop": ["<|im_end|>"],
        "stream": False
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        # Verificar la estructura de la respuesta
        if "choices" in data and len(data["choices"]) > 0:
            key_moments = data['choices'][0]['message']['content'].strip()
            # Almacenar los momentos clave en el estado de la sesión
            st.session_state['key_moments'][cuento_id] = key_moments
            return key_moments
        else:
            st.error("Respuesta inesperada de la API de extracción de momentos clave.")
            return None
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred al extraer momentos clave: {http_err}")
        return None
    except Exception as err:
        st.error(f"Error al extraer momentos clave: {err}")
        return None

# Función para generar prompt para la ilustración
def generate_prompt(key_moments):
    prompt = (
        f"Ilustración en estilo de arte del siglo XVIII, a lápiz, en blanco y negro. "
        f"Escena que representa: {key_moments}"
    )
    return prompt

# Función para generar imagen utilizando la API de Together
def generate_image(prompt, api_key, cuento_id):
    url = "https://api.together.xyz/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "black-forest-labs/FLUX.1-schnell-Free",
        "prompt": prompt,
        "width": 512,
        "height": 512,
        "steps": 4,
        "n": 1,
        "response_format": "b64_json"
        # Eliminado 'update_at' ya que no es necesario
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        if "data" in data and len(data["data"]) > 0:
            image_b64 = data["data"][0]["b64_json"]
            # Almacenar la imagen en el estado de la sesión
            st.session_state['images'][cuento_id] = image_b64
            return image_b64
        else:
            st.error("Respuesta inesperada de la API de generación de imágenes.")
            return None
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred al generar la imagen: {http_err}")
        return None
    except Exception as err:
        st.error(f"Error al generar la imagen: {err}")
        return None

# Sección para subir el archivo
uploaded_file = st.file_uploader("Sube un archivo de texto con tus cuentos", type=["txt"])

if uploaded_file is not None:
    # Leer el contenido del archivo
    content = uploaded_file.read().decode("utf-8")
    
    # Suponiendo que los cuentos están separados por dos saltos de línea
    # Puedes ajustar esto según el formato de tu archivo
    cuentos = [cuento.strip() for cuento in content.split("\n\n") if cuento.strip()]
    
    st.success(f"Archivo cargado exitosamente. Número de cuentos detectados: {len(cuentos)}")
    
    # Obtener la clave de la API de los secretos de Streamlit
    TOGETHER_API_KEY = st.secrets["TOGETHER_API_KEY"]
    
    if not TOGETHER_API_KEY:
        st.error("La clave de la API de Together no está configurada en los secretos de Streamlit.")
    else:
        # Crear una sección para mostrar los resultados
        for idx, cuento in enumerate(cuentos, 1):
            cuento_id = f"cuento_{idx}"
            st.markdown(f"### Cuento {idx}")
            with st.expander(f"Cuento {idx}", expanded=False):
                st.text_area(f"Cuento {idx}:", cuento, height=150)
            
            # Extraer momentos clave usando la API de Together
            if st.button(f"Extraer Momentos Clave para Cuento {idx}", key=f"extract_{idx}"):
                with st.spinner("Extrayendo momentos clave..."):
                    key_moments = extract_key_moments_with_together(cuento, TOGETHER_API_KEY, cuento_id)
                    if key_moments:
                        st.markdown(f"**Momentos Clave:**\n{key_moments}")
            
            # Verificar si los momentos clave ya han sido extraídos y almacenados
            key_moments = st.session_state['key_moments'].get(cuento_id, None)
            
            if key_moments:
                prompt = generate_prompt(key_moments)
                st.markdown(f"**Prompt para la API de Imagen:** {prompt}")
                
                # Generar la ilustración solo si no se ha generado previamente
                if cuento_id not in st.session_state['images']:
                    if st.button(f"Generar Ilustración para Cuento {idx}", key=f"generate_{idx}"):
                        with st.spinner("Generando ilustración..."):
                            b64_image = generate_image(prompt, TOGETHER_API_KEY, cuento_id)
                            if b64_image:
                                # Decodificar la imagen
                                image_bytes = base64.b64decode(b64_image)
                                encoded_image = base64.b64encode(image_bytes).decode()
                                image_uri = f"data:image/png;base64,{encoded_image}"
                                
                                st.image(image_uri, caption=f"Ilustración para Cuento {idx}", use_column_width=True)
                                
                                # Opción para descargar la imagen
                                st.markdown(f"### Descargar Ilustración {idx}")
                                st.download_button(
                                    label="Descargar Imagen",
                                    data=image_bytes,
                                    file_name=f"ilustracion_cuento_{idx}.png",
                                    mime="image/png"
                                )
                else:
                    # Mostrar la imagen si ya ha sido generada
                    b64_image = st.session_state['images'][cuento_id]
                    image_bytes = base64.b64decode(b64_image)
                    encoded_image = base64.b64encode(image_bytes).decode()
                    image_uri = f"data:image/png;base64,{encoded_image}"
                    
                    st.image(image_uri, caption=f"Ilustración para Cuento {idx}", use_column_width=True)
                    
                    # Opción para descargar la imagen
                    st.markdown(f"### Descargar Ilustración {idx}")
                    st.download_button(
                        label="Descargar Imagen",
                        data=image_bytes,
                        file_name=f"ilustracion_cuento_{idx}.png",
                        mime="image/png"
                    )
            st.markdown("---")
