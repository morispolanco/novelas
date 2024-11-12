import streamlit as st
import requests
import base64
from datetime import datetime
import re

# Configuración de la página
st.set_page_config(
    page_title="Generador de Ilustraciones para Cuentos por Capítulo",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Título de la aplicación
st.title("Generador de Ilustraciones para Cuentos por Capítulo con Streamlit y Together API")

# Instrucciones
st.markdown("""
Esta aplicación permite subir un archivo de texto que contiene varios cuentos divididos en capítulos. Para cada capítulo, se extraen momentos clave utilizando la API de Together y se generan ilustraciones de arte digital imitando el estilo del siglo XVIII, a lápiz y en blanco y negro.

**Pasos:**
1. Sube un archivo de texto con tus cuentos y capítulos.
2. Para cada capítulo, haz clic en "Extraer Momentos Clave".
3. Una vez extraídos los momentos clave, haz clic en "Generar Ilustración".
4. Visualiza y descarga las ilustraciones generadas.
""")

# Inicializar el estado de sesión para almacenar momentos clave y imágenes
if 'key_moments' not in st.session_state:
    st.session_state['key_moments'] = {}
if 'images' not in st.session_state:
    st.session_state['images'] = {}

# Función para separar el texto en cuentos y capítulos
def parse_text(content):
    """
    Asume que los cuentos están marcados con '# Cuento X: Título'
    y los capítulos con 'CAP. X: Título'.
    """
    # Separar cuentos
    cuentos = re.split(r'^# Cuento \d+:', content, flags=re.MULTILINE)
    # El primer elemento puede estar vacío si el texto comienza con '# Cuento 1: ...'
    cuentos = [c for c in cuentos if c.strip()]
    
    parsed_cuentos = []
    for idx, cuento in enumerate(cuentos, 1):
        # Buscar el título del cuento dentro del segmento de cuento
        titulo_match = re.search(r'^# Cuento \d+: (.+)', cuento, re.MULTILINE)
        titulo = titulo_match.group(1).strip() if titulo_match else f"Cuento {idx}"
        
        # Separar capítulos
        capitulos = re.split(r'^CAP\. \d+:', cuento, flags=re.MULTILINE)
        capitulos = [c for c in capitulos if c.strip()]
        
        parsed_capitulos = []
        for c_idx, capitulo in enumerate(capitulos, 1):
            # Buscar el título del capítulo dentro del segmento de capítulo
            capitulo_match = re.search(r'^CAP\. \d+: (.+)', capitulo, re.MULTILINE)
            capitulo_titulo = capitulo_match.group(1).strip() if capitulo_match else f"Capítulo {c_idx}"
            # Extraer el contenido del capítulo
            contenido = re.split(r'^CAP\. \d+: .+', capitulo, flags=re.MULTILINE)[-1].strip()
            parsed_capitulos.append({
                'titulo': capitulo_titulo,
                'contenido': contenido
            })
        
        parsed_cuentos.append({
            'numero': idx,
            'titulo': titulo,
            'capitulos': parsed_capitulos
        })
    
    return parsed_cuentos

# Función para extraer momentos clave utilizando la API de Together
def extract_key_moments_with_together(cuento_num, capitulo_num, contenido, api_key):
    url = "https://api.together.xyz/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    prompt = (
        "Analiza el siguiente capítulo de un cuento y extrae los tres momentos más importantes o destacados. "
        "Proporciona una lista numerada con cada momento.\n\n"
        f"Capítulo:\n{contenido}\n\nMomentos Clave:"
    )
    payload = {
        "model": "Qwen/Qwen2.5-7B-Instruct-Turbo",
        "messages": [
            {"role": "system", "content": "Eres un asistente que ayuda a extraer los momentos clave de un capítulo de un cuento."},
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
        if "choices" in data and len(data["choices"]) > 0:
            key_moments = data['choices'][0]['message']['content'].strip()
            # Almacenar los momentos clave en el estado de la sesión
            clave_id = f"cuento_{cuento_num}_capitulo_{capitulo_num}"
            st.session_state['key_moments'][clave_id] = key_moments
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
def generate_image(prompt, api_key, clave_id):
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
            st.session_state['images'][clave_id] = image_b64
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
uploaded_file = st.file_uploader("Sube un archivo de texto con tus cuentos y capítulos", type=["txt"])

if uploaded_file is not None:
    # Leer el contenido del archivo
    content = uploaded_file.read().decode("utf-8")
    
    # Parsear el contenido en cuentos y capítulos
    parsed_cuentos = parse_text(content)
    
    st.success(f"Archivo cargado exitosamente. Número de cuentos detectados: {len(parsed_cuentos)}")
    
    # Obtener la clave de la API de los secretos de Streamlit
    TOGETHER_API_KEY = st.secrets["TOGETHER_API_KEY"]
    
    if not TOGETHER_API_KEY:
        st.error("La clave de la API de Together no está configurada en los secretos de Streamlit.")
    else:
        # Iterar sobre los cuentos
        for cuento in parsed_cuentos:
            cuento_num = cuento['numero']
            cuento_titulo = cuento['titulo']
            
            st.markdown(f"### Cuento {cuento_num}: {cuento_titulo}")
            
            # Iterar sobre los capítulos del cuento
            for capitulo_num, capitulo in enumerate(cuento['capitulos'], 1):
                capitulo_titulo = capitulo['titulo']
                contenido = capitulo['contenido']
                
                capitulo_id = f"cuento_{cuento_num}_capitulo_{capitulo_num}"
                
                st.markdown(f"#### Capítulo {capitulo_num}: {capitulo_titulo}")
                with st.expander(f"Ver Contenido del Capítulo {capitulo_num}", expanded=False):
                    st.text_area(f"Capítulo {capitulo_num}:", contenido, height=200)
                
                # Botón para extraer momentos clave
                if st.button(f"Extraer Momentos Clave para Capítulo {capitulo_num} del Cuento {cuento_num}", key=f"extract_{capitulo_id}"):
                    with st.spinner("Extrayendo momentos clave..."):
                        key_moments = extract_key_moments_with_together(cuento_num, capitulo_num, contenido, TOGETHER_API_KEY)
                        if key_moments:
                            st.markdown(f"**Momentos Clave:**\n{key_moments}")
                
                # Verificar si los momentos clave ya han sido extraídos y almacenados
                key_moments = st.session_state['key_moments'].get(capitulo_id, None)
                
                if key_moments:
                    prompt = generate_prompt(key_moments)
                    st.markdown(f"**Prompt para la API de Imagen:** {prompt}")
                    
                    # Botón para generar ilustración
                    if capitulo_id not in st.session_state['images']:
                        if st.button(f"Generar Ilustración para Capítulo {capitulo_num} del Cuento {cuento_num}", key=f"generate_{capitulo_id}"):
                            with st.spinner("Generando ilustración..."):
                                b64_image = generate_image(prompt, TOGETHER_API_KEY, capitulo_id)
                                if b64_image:
                                    # Decodificar la imagen
                                    image_bytes = base64.b64decode(b64_image)
                                    encoded_image = base64.b64encode(image_bytes).decode()
                                    image_uri = f"data:image/png;base64,{encoded_image}"
                                    
                                    st.image(image_uri, caption=f"Ilustración para Capítulo {capitulo_num} del Cuento {cuento_num}", use_column_width=True)
                                    
                                    # Opción para descargar la imagen
                                    st.markdown(f"### Descargar Ilustración del Capítulo {capitulo_num}")
                                    st.download_button(
                                        label="Descargar Imagen",
                                        data=image_bytes,
                                        file_name=f"ilustracion_cuento_{cuento_num}_capitulo_{capitulo_num}.png",
                                        mime="image/png"
                                    )
                    else:
                        # Mostrar la imagen si ya ha sido generada
                        b64_image = st.session_state['images'][capitulo_id]
                        image_bytes = base64.b64decode(b64_image)
                        encoded_image = base64.b64encode(image_bytes).decode()
                        image_uri = f"data:image/png;base64,{encoded_image}"
                        
                        st.image(image_uri, caption=f"Ilustración para Capítulo {capitulo_num} del Cuento {cuento_num}", use_column_width=True)
                        
                        # Opción para descargar la imagen
                        st.markdown(f"### Descargar Ilustración del Capítulo {capitulo_num}")
                        st.download_button(
                            label="Descargar Imagen",
                            data=image_bytes,
                            file_name=f"ilustracion_cuento_{cuento_num}_capitulo_{capitulo_num}.png",
                            mime="image/png"
                        )
                st.markdown("---")
