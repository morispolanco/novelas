import streamlit as st
import requests
import json
import time
from docx import Document
from io import BytesIO
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from docx.shared import Inches, Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import logging
from time import sleep

# Configurar el logging para Streamlit
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)  # Nivel DEBUG para más detalles

# Configuración de la página
st.set_page_config(
    page_title="Analizador de Novelas de Suspenso Político",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Título de la aplicación
st.title("Analizador de Novelas de Suspenso Político")
st.write("""
Esta aplicación analiza una novela en el género de thriller político.
Sube tu novela en formato `.docx` o `.txt` y recibe un informe detallado de errores y mejoras, además de una calificación global.
""")

# Barra lateral para opciones de usuario
st.sidebar.header("Configuración de Análisis")
file_upload = st.sidebar.file_uploader("Sube tu novela (.docx o .txt):", type=["docx", "txt"])

# Inicializar el estado de la aplicación
if 'etapa' not in st.session_state:
    st.session_state.etapa = "inicio"  # etapas: inicio, analisis, completado

if 'novela' not in st.session_state:
    st.session_state.novela = ""
if 'informe_global' not in st.session_state:
    st.session_state.informe_global = ""

# Función para extraer JSON de una respuesta mixta
def extraer_json(texto):
    try:
        # Encuentra el primer bloque que comienza con { y termina con }
        match = re.search(r'\{.*\}', texto, re.DOTALL)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
        else:
            return None
    except json.JSONDecodeError:
        return None

# Función para llamar a la API de OpenRouter con reintentos y parámetros ajustables
def call_openrouter_api(prompt, max_tokens=3000, temperature=0.5, top_p=0.9, repetition_penalty=1.2):
    api_url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai/gpt-4o-mini",  # Usando el modelo especificado por el usuario
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p,
        "repetition_penalty": repetition_penalty,
        "stream": False
        # "stop": ["<|eot_id|>"],  # Eliminado para evitar posibles interrupciones incorrectas
    }
    
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    
    response_text = ""
    for attempt in range(5):
        try:
            response = session.post(api_url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            response_text = response.text  # Obtener la respuesta como texto
            logging.debug("Respuesta de la API: %s", response_text)  # Registrar la respuesta completa
            
            # Mostrar detalles de la respuesta para depuración
            logging.debug("Código de estado HTTP: %s", response.status_code)
            logging.debug("Encabezados de la respuesta: %s", response.headers)
            
            if 'application/json' in response.headers.get('Content-Type', ''):
                response_json = response.json()
            else:
                response_json = extraer_json(response_text)
                if not response_json:
                    st.error("La respuesta de la API no contiene un JSON válido.")
                    st.write("**Respuesta completa de la API:**", response_text)
                    return None
            
            if 'choices' in response_json and len(response_json['choices']) > 0:
                contenido = response_json['choices'][0]['message']['content']
                logging.debug("Contenido de la respuesta de la API: %s", contenido)
                return contenido
            else:
                st.error("La respuesta de la API no contiene 'choices'.")
                st.write("**Respuesta completa de la API:**", response_json)
                return None
        except requests.exceptions.RequestException as e:
            logging.error(f"Intento {attempt + 1}: Error en la llamada a la API: {e}")
            st.warning(f"Intento {attempt + 1}: Error en la llamada a la API. Reintentando...")
            sleep(2 ** attempt)
        except json.JSONDecodeError as e:
            logging.error("Error al decodificar la respuesta de la API: %s", e)
            st.error(f"Error al decodificar la respuesta de la API: {e}")
            st.write("**Respuesta de la API (texto):**", response_text)
            return None
    
    st.error("No se pudo obtener una respuesta válida de la API después de varios intentos.")
    return None

# Función para leer el contenido del archivo subido
def leer_archivo(file):
    try:
        if file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(file)
            texto = "\n".join([para.text for para in doc.paragraphs])
        elif file.type == "text/plain":
            texto = file.read().decode("utf-8")
        else:
            st.error("Formato de archivo no soportado.")
            return None
        return texto
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        logging.error("Error al leer el archivo: %s", e)
        return None

# Función para dividir la novela si es muy larga
def dividir_novela(texto, max_length=2500):  # Reducido a 2500 si es necesario
    # Dividir por párrafos para mantener la coherencia
    parrafos = texto.split('\n')
    secciones = []
    seccion_actual = ""
    
    for parrafo in parrafos:
        if len(seccion_actual) + len(parrafo) + 1 <= max_length:
            seccion_actual += parrafo + '\n'
        else:
            secciones.append(seccion_actual.strip())
            seccion_actual = parrafo + '\n'
    
    if seccion_actual:
        secciones.append(seccion_actual.strip())
    
    return secciones

# Función para analizar la novela completa
def analizar_novela(texto, progress_bar=None, progress_text=None):
    secciones = dividir_novela(texto)
    total_secciones = len(secciones)
    analisis_completo = {
        "calificacion": [],
        "errores": [],
        "recomendaciones": []
    }
    
    for idx, seccion in enumerate(secciones):
        prompt = f"""
Por favor, analiza la siguiente sección de una novela de suspenso político. Identifica errores gramaticales, de coherencia, desarrollo de personajes, ritmo y cualquier otro aspecto que pueda mejorar la calidad de la novela. Proporciona recomendaciones claras y específicas para cada área de mejora y asigna una calificación de 1 a 10 puntos basada en la calidad general de la sección.

**Importante:** Responde únicamente con un JSON válido que contenga las siguientes claves: "calificacion", "errores", "recomendaciones". No incluyas ningún texto adicional fuera del JSON.

### Sección {idx+1}:
{seccion}

### Informe de Análisis:
```json
