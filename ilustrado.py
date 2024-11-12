import streamlit as st
import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
import requests
import base64
import json
from io import StringIO
from datetime import datetime

# Descargar recursos de NLTK si no están ya descargados
nltk.download('punkt')
nltk.download('stopwords')

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
Esta aplicación permite subir un archivo de texto que contiene varios cuentos. Para cada cuento, se extraen momentos clave y se generan ilustraciones de arte digital imitando el estilo del siglo XVIII, a lápiz y en blanco y negro.

**Pasos:**
1. Sube un archivo de texto con tus cuentos.
2. La aplicación procesará cada cuento y generará ilustraciones automáticamente.
3. Visualiza y descarga las ilustraciones generadas.
""")

# Función para extraer momentos clave utilizando NLTK
def extract_key_moments(text, num_moments=3):
    sentences = sent_tokenize(text)
    # Aquí puedes implementar una lógica más avanzada para extraer momentos clave
    # Por simplicidad, seleccionaremos las primeras 'num_moments' oraciones
    key_moments = sentences[:num_moments]
    return " ".join(key_moments)

# Función para generar prompt
def generate_prompt(key_moments):
    prompt = (
        f"Ilustración en estilo de arte del siglo XVIII, a lápiz, en blanco y negro. "
        f"Escena que representa: {key_moments}"
    )
    return prompt

# Función para generar imagen utilizando la API de Together
def generate_image(prompt, api_key):
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
        "response_format": "b64_json",
        "update_at": datetime.utcnow().isoformat() + "Z"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        if "data" in data and len(data["data"]) > 0:
            return data["data"][0]["b64_json"]
        else:
            st.error("Respuesta inesperada de la API.")
            return None
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred: {http_err}")
        return None
    except Exception as err:
        st.error(f"Other error occurred: {err}")
        return None

# Sección para subir el archivo
uploaded_file = st.file_uploader("Sube un archivo de texto con tus cuentos", type=["txt"])

if uploaded_file is not None:
    # Leer el contenido del archivo
    content = uploaded_file.read().decode("utf-8")
    
    # Suponiendo que los cuentos están separados por títulos en mayúsculas
    # Puedes ajustar esto según el formato de tu archivo
    cuentos = content.split("\n\n")  # Separar por párrafos dobles como ejemplo
    
    st.success(f"Archivo cargado exitosamente. Número de cuentos detectados: {len(cuentos)}")
    
    # Obtener la clave de la API de los secretos de Streamlit
    TOGETHER_API_KEY = st.secrets["TOGETHER_API_KEY"]
    
    if not TOGETHER_API_KEY:
        st.error("La clave de la API de Together no está configurada en los secretos de Streamlit.")
    else:
        # Crear una sección para mostrar los resultados
        for idx, cuento in enumerate(cuentos, 1):
            st.markdown(f"### Cuento {idx}")
            st.text_area(f"Cuento {idx}:", cuento, height=150)
            
            # Extraer momentos clave
            key_moments = extract_key_moments(cuento)
            st.markdown(f"**Momentos Clave:** {key_moments}")
            
            # Generar prompt
            prompt = generate_prompt(key_moments)
            st.markdown(f"**Prompt para la API:** {prompt}")
            
            # Botón para generar la imagen
            if st.button(f"Generar Ilustración para Cuento {idx}"):
                with st.spinner("Generando ilustración..."):
                    b64_image = generate_image(prompt, TOGETHER_API_KEY)
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
            st.markdown("---")
