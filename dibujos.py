import streamlit as st
from docx import Document
import requests
from io import BytesIO
from PIL import Image
import re
import base64
import json

# Configuración de la página
st.set_page_config(page_title="Generador de Ilustraciones para Novelas", layout="wide")

# Título de la aplicación
st.title("Generador de Ilustraciones para Novelas en DOCX")

# Instrucciones
st.markdown("""
Sube tu novela en formato **DOCX** y genera una ilustración por cada capítulo. 
Las ilustraciones serán coherentes a lo largo de los capítulos, manteniendo consistencia en los personajes.
""")

@st.cache_data
def parse_docx(file):
    """Parsea el archivo DOCX y extrae los capítulos."""
    doc = Document(file)
    chapters = {}
    current_chapter = "Introducción"
    chapters[current_chapter] = ""

    for para in doc.paragraphs:
        # Suponiendo que los títulos de capítulos están en estilo 'Heading 1'
        if para.style.name == 'Heading 1':
            current_chapter = para.text.strip()
            chapters[current_chapter] = ""
        else:
            chapters[current_chapter] += para.text + " "

    return chapters

def extract_characters(text, num_characters=5):
    """
    Extrae nombres de personajes principales usando expresiones regulares.
    Este método es simplista y puede mejorarse con técnicas de NLP.
    """
    # Buscar palabras que comienzan con mayúscula y no al inicio de una oración
    potential_names = re.findall(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)+\b', text)
    character_freq = {}
    for name in potential_names:
        character_freq[name] = character_freq.get(name, 0) + 1
    # Ordenar por frecuencia
    sorted_characters = sorted(character_freq.items(), key=lambda x: x[1], reverse=True)
    # Retornar los nombres más frecuentes
    return [name for name, freq in sorted_characters[:num_characters]]

def generate_character_descriptions(characters):
    """
    Genera descripciones para los personajes usando la API de OpenRouter.
    """
    descriptions = {}
    for character in characters:
        prompt = f"Describe al personaje {character} de una manera detallada para mantener la coherencia en las ilustraciones a lo largo de una novela."
        response = call_openrouter_api(prompt)
        if response:
            descriptions[character] = response
        else:
            descriptions[character] = "Descripción no disponible."
    return descriptions

def summarize_chapter(chapter_text):
    """
    Resume el texto del capítulo para extraer elementos clave para la ilustración.
    """
    prompt = f"Resume el siguiente texto del capítulo destacando los elementos clave que deben reflejarse en una ilustración: {chapter_text}"
    summary = call_openrouter_api(prompt)
    return summary if summary else "Resumen no disponible."

def generate_image_prompt(summary, character_descriptions):
    """
    Genera un prompt detallado para la ilustración usando el resumen del capítulo y las descripciones de los personajes.
    """
    prompt = f"Basado en el siguiente resumen del capítulo, crea una descripción detallada para una ilustración: {summary}\n\n"
    prompt += "Descripción de personajes:\n"
    for character, desc in character_descriptions.items():
        prompt += f"- {character}: {desc}\n"
    prompt += "Asegúrate de que los personajes sean consistentes con las descripciones proporcionadas."
    detailed_prompt = call_openrouter_api(prompt)
    return detailed_prompt if detailed_prompt else "Descripción de ilustración no disponible."

def generate_image_from_prompt(prompt):
    """
    Genera una imagen usando la API de Together a partir de un prompt.
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
        # Asumiendo que la estructura de respuesta es similar al ejemplo de curl
        b64_image = response_data["data"][0]["b64_json"]
        image_bytes = base64.b64decode(b64_image)
        image = Image.open(BytesIO(image_bytes))
        return image
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred al generar la imagen: {http_err} - {response.text}")
    except Exception as e:
        st.error(f"Error al generar la imagen: {e}")
    return None

def call_openrouter_api(prompt):
    """
    Llama a la API de OpenRouter para obtener una respuesta basada en el prompt.
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
                "content": prompt
            }
        ]
    }
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred en OpenRouter: {http_err} - {response.text}")
    except Exception as e:
        st.error(f"Error al comunicarse con OpenRouter: {e}")
    return None

# Interfaz de carga de archivo
uploaded_file = st.file_uploader("Sube tu novela en formato DOCX", type=["docx"])

if uploaded_file is not None:
    with st.spinner("Procesando el archivo..."):
        chapters = parse_docx(uploaded_file)

    st.success("Archivo procesado con éxito.")

    # Extraer personajes de todo el libro
    all_text = " ".join(chapters.values())
    characters = extract_characters(all_text)

    if not characters:
        st.warning("No se pudieron extraer personajes. Asegúrate de que los nombres estén correctamente capitalizados.")
    else:
        st.sidebar.header("Personajes Principales")
        for char in characters:
            st.sidebar.write(char)

        # Generar descripciones de personajes
        with st.spinner("Generando descripciones de personajes..."):
            character_descriptions = generate_character_descriptions(characters)

        # Botón para generar ilustraciones
        if st.button("Generar Ilustraciones"):
            illustrations = {}
            for chapter, text in chapters.items():
                with st.spinner(f"Generando ilustración para el capítulo: {chapter}"):
                    summary = summarize_chapter(text)
                    detailed_prompt = generate_image_prompt(summary, character_descriptions)
                    image = generate_image_from_prompt(detailed_prompt)
                    if image:
                        illustrations[chapter] = image
            if illustrations:
                st.success("Ilustraciones generadas con éxito.")
                for chapter, image in illustrations.items():
                    st.header(f"Capítulo: {chapter}")
                    st.image(image, use_column_width=True)
            else:
                st.error("No se generaron ilustraciones.")
