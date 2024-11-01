import streamlit as st
import requests
import time
from docx import Document
from io import BytesIO
import nltk
from nltk.tokenize import sent_tokenize

# Descargar recursos de NLTK
nltk.download('punkt')

# Configuración de la página
st.set_page_config(
    page_title="📝 Generador de Obras de Ficción",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📝 Generador de Obras de Ficción")
st.write("Esta aplicación genera una obra de ficción basada en el prompt que ingreses, dividida en capítulos evitando la repetición de contenido.")

# Función para generar un capítulo de la obra
def generar_capitulo(prompt, capitulo_num, resumen_previas):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}"
    }
    # Instrucciones para evitar repeticiones
    instrucciones = (
        "Asegúrate de no repetir información ya mencionada en capítulos anteriores de la obra. "
        "Utiliza un lenguaje creativo y atractivo, desarrollando nuevos eventos, personajes o giros en la trama en cada capítulo."
    )
    if resumen_previas:
        resumen_texto = " Hasta ahora, la obra ha cubierto los siguientes puntos: " + resumen_previas
    else:
        resumen_texto = ""
    mensaje = (
        f"Escribe el capítulo {capitulo_num} de una obra de ficción sobre el siguiente tema: {prompt}. "
        f"El capítulo debe tener aproximadamente 1000 palabras y no debe contener subdivisiones ni subcapítulos.{resumen_texto} {instrucciones}"
    )
    data = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": mensaje
            }
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        respuesta = response.json()
        contenido = respuesta['choices'][0]['message']['content']
        return contenido
    except requests.exceptions.RequestException as e:
        st.error(f"Error al generar el capítulo {capitulo_num}: {e}")
        return None

# Función para resumir un capítulo utilizando la API de OpenRouter
def resumir_capitulo(capitulo):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}"
    }
    prompt_resumen = (
        "Proporciona un resumen conciso y relevante del siguiente capítulo de una obra de ficción. "
        "El resumen debe resaltar los puntos clave de la trama, los desarrollos de los personajes y los eventos principales, evitando detalles redundantes.\n\n"
        f"Capítulo:\n{capitulo}\n\nResumen:"
    )
    data = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": prompt_resumen
            }
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        respuesta = response.json()
        resumen = respuesta['choices'][0]['message']['content']
        # Limpiar el resumen eliminando posibles saltos de línea adicionales
        resumen = ' '.join(resumen.split())
        return resumen
    except requests.exceptions.RequestException as e:
        st.error(f"Error al resumir el capítulo: {e}")
        return None

# Función para crear el documento Word
def crear_documento(capitulo_list, titulo):
    doc = Document()
    doc.add_heading(titulo, 0)
    for idx, capitulo in enumerate(capitulo_list, 1):
        doc.add_heading(f"Capítulo {idx}", level=1)
        doc.add_paragraph(capitulo)
    # Guardar el documento en un buffer
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# Interfaz de usuario
with st.form(key='form_obra'):
    prompt = st.text_area("Ingresa el tema o idea para la obra de ficción:", height=200)
    num_capitulos = st.slider("Número de capítulos:", min_value=5, max_value=20, value=10)
    submit_button = st.form_submit_button(label='Generar Obra')
    
if submit_button:
    if not prompt.strip():
        st.error("Por favor, ingresa un tema o idea válida para la obra de ficción.")
    else:
        st.success("Iniciando la generación de la obra de ficción...")
        capitulos = []
        resumenes = []
        progreso = st.progress(0)
        for i in range(1, num_capitulos + 1):
            st.write(f"Generando **Capítulo {i}**...")
            # Crear un resumen de capítulos previos para evitar repeticiones
            if resumenes:
                resumen_previas = ' '.join(resumenes)
            else:
                resumen_previas = ''
            capitulo = generar_capitulo(prompt, i, resumen_previas)
            if capitulo:
                capitulos.append(capitulo)
                # Resumir el capítulo generado
                resumen = resumir_capitulo(capitulo)
                if resumen:
                    resumenes.append(resumen)
                else:
                    st.warning(f"No se pudo generar un resumen para el Capítulo {i}.")
            else:
                st.error("La generación de la obra se ha detenido debido a un error.")
                break
            progreso.progress(i / num_capitulos)
            time.sleep(5)  # Pausa de 5 segundos entre capítulos
        if len(capitulos) == num_capitulos:
            titulo_obra = st.text_input("Título de la obra:", value="Obra de Ficción")
            documento = crear_documento(capitulos, titulo_obra)
            st.success("Obra de ficción generada exitosamente.")
            st.download_button(
                label="Descargar Obra en Word",
                data=documento,
                file_name="obra_de_ficcion.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        progreso.empty()
