import streamlit as st
import anthropic
import json
import time
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from io import BytesIO
import re
import random
import matplotlib.pyplot as plt

# Nuevas importaciones necesarias para agregar la tabla de contenidos
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# Configuración de la página
st.set_page_config(
    page_title="Generador de Novelas de Suspenso Político",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Título de la aplicación
st.title("Generador de Novelas de Suspenso Político")
st.write("""
Esta aplicación genera una novela en el género de thriller político.
Ingrese un tema y personalice el número de capítulos y escenas para crear una narrativa coherente y emocionante.
""")

# Barra lateral para opciones de usuario
st.sidebar.header("Configuración de la Novela")
num_capitulos = st.sidebar.slider("Número de capítulos", min_value=8, max_value=12, value=10)
num_escenas = st.sidebar.slider("Número de escenas por capítulo", min_value=3, max_value=5, value=4)
porcentaje_trama_principal = st.sidebar.slider("Porcentaje de palabras para la trama principal (%)", min_value=60, max_value=80, value=70)
porcentaje_subtramas = 100 - porcentaje_trama_principal
st.sidebar.write(f"Porcentaje de palabras para subtramas: {porcentaje_subtramas}%")

# Inicializar el estado de la aplicación
if 'etapa' not in st.session_state:
    st.session_state.etapa = "inicio"  # etapas: inicio, aprobacion, generacion, completado

if 'estructura' not in st.session_state:
    st.session_state.estructura = None
if 'novela_completa' not in st.session_state:
    st.session_state.novela_completa = None
if 'titulo' not in st.session_state:
    st.session_state.titulo = ""
if 'trama' not in st.session_state:
    st.session_state.trama = ""
if 'subtramas' not in st.session_state:
    st.session_state.subtramas = ""
if 'personajes' not in st.session_state:
    st.session_state.personajes = ""
if 'ambientacion' not in st.session_state:
    st.session_state.ambientacion = ""
if 'tecnica' not in st.session_state:
    st.session_state.tecnica = ""

# Función para llamar a la API de Anthropic utilizando la librería oficial
def call_anthropic_api(prompt, max_tokens, model="claude-2"):
    client = anthropic.Client(api_key=st.secrets['ANTHROPIC_API_KEY'])
    try:
        response = client.completions.create(
            model=model,
            max_tokens_to_sample=max_tokens,
            temperature=0.7,
            prompt=f"{anthropic.HUMAN_PROMPT}{prompt}{anthropic.AI_PROMPT}"
        )
        return response.completion.strip()
    except Exception as e:
        st.error(f"Error en la llamada a la API de Anthropic: {e}")
        return None

# Función para generar la estructura inicial de la novela con subtramas y técnicas avanzadas
def generar_estructura(theme):
    prompt = f"""
Basado en el tema proporcionado, genera una estructura detallada para una novela de suspenso político de alta calidad. Asegúrate de que la novela obtenga una calificación de 10 sobre 10 en los siguientes aspectos:
- **Trama**: Compleja, bien desarrollada y llena de giros inesperados.
- **Originalidad**: Ideas frescas y únicas que distinguen la novela de otras en el mismo género.
- **Desarrollo de Personajes**: Personajes profundos, multidimensionales y realistas con arcos de desarrollo claros.
- **Ritmo**: Fluido y bien equilibrado, manteniendo el interés del lector en todo momento.
- **Descripciones**: Vivas y detalladas que permiten al lector visualizar escenas y emociones con claridad.
- **Calidad General**: Cohesión, coherencia y excelencia literaria en todo momento.
- **Técnicas Avanzadas de Escritura**:
    - **Foreshadowing**: Introduce pistas sutiles sobre eventos futuros.
    - **Metáforas y Simbolismo**: Utiliza figuras retóricas para enriquecer la narrativa.
    - **Show, Don't Tell**: Enfócate en mostrar acciones y emociones en lugar de simplemente describirlas.

### Estructura Requerida:
1. **Título**
2. **Trama Principal**
3. **Subtramas** (incluyendo nombres, descripciones detalladas, motivaciones y cómo afectan a los personajes y la trama principal)
4. **Personajes** (incluyendo nombres, descripciones físicas y psicológicas, motivaciones, y arcos de desarrollo)
5. **Ambientación** (detallada y relevante para la trama)
6. **Técnicas Literarias a Utilizar** (como metáforas, simbolismo, foreshadowing, etc.)

### Tema:
{theme}

Asegúrate de que toda la información generada sea coherente y adecuada para un thriller político de alta calidad.
"""
    estructura = call_anthropic_api(prompt, max_tokens=4000)
    return estructura

# Función para extraer los elementos de la estructura usando expresiones regulares
def extraer_elementos(estructura):
    # Mostrar la estructura completa para depuración
    st.write("### Estructura generada por la API:")
    st.write(estructura)

    # Patrón mejorado para extraer los elementos, incluyendo subtramas
    patrones = {
        'titulo': r"(?:Título|Titulo):\s*(.*)",
        'trama': r"Trama Principal:\s*((?:.|\n)*?)\n(?:Subtramas|Subtrama)",
        'subtramas': r"Subtramas?:\s*((?:.|\n)*?)\n(?:Personajes|Ambientación|Ambientacion|Técnicas literarias|$)",
        'personajes': r"Personajes:\s*((?:.|\n)*?)\n(?:Ambientación|Ambientacion|Técnicas literarias|$)",
        'ambientacion': r"Ambientación:\s*((?:.|\n)*?)\n(?:Técnicas literarias|$)",
        'tecnica': r"Técnicas literarias(?: a utilizar)?:\s*((?:.|\n)*)"
    }

    titulo = re.search(patrones['titulo'], estructura, re.IGNORECASE)
    trama = re.search(patrones['trama'], estructura, re.IGNORECASE)
    subtramas = re.search(patrones['subtramas'], estructura, re.IGNORECASE)
    personajes = re.search(patrones['personajes'], estructura, re.IGNORECASE)
    ambientacion = re.search(patrones['ambientacion'], estructura, re.IGNORECASE)
    tecnica = re.search(patrones['tecnica'], estructura, re.IGNORECASE)

    # Extraer el contenido, manejando posibles espacios y formatos
    titulo = titulo.group(1).strip() if titulo else "Sin título"
    trama = trama.group(1).strip() if trama else "Sin trama principal"
    subtramas = subtramas.group(1).strip() if subtramas else "Sin subtramas"
    personajes = personajes.group(1).strip() if personajes else "Sin personajes"
    ambientacion = ambientacion.group(1).strip() if ambientacion else "Sin ambientación"
    tecnica = tecnica.group(1).strip() if tecnica else "Sin técnicas literarias"

    return titulo, trama, subtramas, personajes, ambientacion, tecnica

# Aquí continúan las demás funciones y el código principal...

# Interfaz de usuario principal
st.write(f"**Etapa actual:** {st.session_state.etapa}")  # Depuración

if st.session_state.etapa == "inicio":
    st.header("Generación de Elementos Iniciales")
    theme = st.text_input("Ingrese el tema para su thriller político:", "")

    if st.button("Generar Elementos Iniciales"):
        if not theme:
            st.error("Por favor, ingrese un tema.")
        else:
            with st.spinner("Generando la estructura inicial..."):
                estructura = generar_estructura(theme)
                if estructura:
                    titulo, trama, subtramas, personajes, ambientacion, tecnica = extraer_elementos(estructura)
                    # Guardar en el estado de la sesión
                    st.session_state.estructura = estructura
                    st.session_state.titulo = titulo
                    st.session_state.trama = trama
                    st.session_state.subtramas = subtramas
                    st.session_state.personajes = personajes
                    st.session_state.ambientacion = ambientacion
                    st.session_state.tecnica = tecnica
                    st.session_state.etapa = "aprobacion"
                else:
                    st.error("No se pudo generar la estructura inicial. Por favor, intente nuevamente.")

# Continúa con el resto del código...



if st.session_state.etapa == "aprobacion":
    mostrar_aprobacion()

if st.session_state.etapa == "generacion":
    with st.spinner("Generando la novela completa..."):
        novela_completa = generar_novela_completa(num_capitulos, num_escenas)
        if novela_completa:
            st.session_state.etapa = "completado"

if st.session_state.etapa == "completado":
    if st.session_state.novela_completa:
        st.success("Novela generada con éxito.")
        # Exportar a Word
        doc_buffer = exportar_a_word(st.session_state.titulo, st.session_state.novela_completa)
        st.download_button(
            label="Descargar Novela en Word",
            data=doc_buffer,
            file_name=f"novela_thriller_politico_{int(time.time())}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        # Mostrar la novela en la interfaz
        st.text_area("Novela Generada:", st.session_state.novela_completa, height=600)
