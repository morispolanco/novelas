import streamlit as st
import requests
import json
import time
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from io import BytesIO
import re
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import matplotlib.pyplot as plt

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
num_capitulos = st.sidebar.slider("Número de capítulos", min_value=3, max_value=15, value=12)
num_escenas = st.sidebar.slider("Número de escenas por capítulo", min_value=3, max_value=7, value=3)

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
if 'personajes' not in st.session_state:
    st.session_state.personajes = ""
if 'ambientacion' not in st.session_state:
    st.session_state.ambientacion = ""
if 'tecnica' not in st.session_state:
    st.session_state.tecnica = ""

# Función para llamar a la API de OpenRouter con reintentos
def call_openrouter_api(prompt, max_tokens=3000):
    api_url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": max_tokens,
        "top_p": 0.7,
        "top_k": 50,
        "repetition_penalty": 1,
        "stop": ["[\"<|eot_id|>\"]"],
        "stream": False
    }
    
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    
    try:
        response = session.post(api_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        response_json = response.json()
        if 'choices' in response_json and len(response_json['choices']) > 0:
            return response_json['choices'][0]['message']['content']
        else:
            st.error("La respuesta de la API no contiene 'choices'.")
            st.write("Respuesta completa de la API:", response_json)
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error en la llamada a la API: {e}")
        return None

# Función para generar la estructura inicial de la novela
def generar_estructura(theme):
    prompt = f"""
Basado en el tema proporcionado, genera lo siguiente para una novela de suspenso político:
- Título
- Trama
- Personajes (incluyendo nombres, descripciones, motivaciones)
- Ambientación
- Técnicas literarias a utilizar

Tema: {theme}

Asegúrate de que todo sea coherente y adecuado para un thriller político.
"""
    estructura = call_openrouter_api(prompt)
    return estructura

# Función para extraer los elementos de la estructura usando expresiones regulares
def extraer_elementos(estructura):
    # Mostrar la estructura completa para depuración
    st.write("### Estructura generada por la API:")
    st.write(estructura)

    # Patrón mejorado para extraer los elementos
    patrones = {
        'titulo': r"(?:Título|Titulo):\s*(.*)",
        'trama': r"Trama:\s*(.*)",
        'personajes': r"Personajes:\s*((?:.|\n)*?)\n(?:Ambientación|Ambientacion|Técnicas literarias|$)",
        'ambientacion': r"Ambientación:\s*((?:.|\n)*?)\n(?:Técnicas literarias|$)",
        'tecnica': r"Técnicas literarias(?: a utilizar)?:\s*((?:.|\n)*)"
    }

    titulo = re.search(patrones['titulo'], estructura, re.IGNORECASE)
    trama = re.search(patrones['trama'], estructura, re.IGNORECASE)
    personajes = re.search(patrones['personajes'], estructura, re.IGNORECASE)
    ambientacion = re.search(patrones['ambientacion'], estructura, re.IGNORECASE)
    tecnica = re.search(patrones['tecnica'], estructura, re.IGNORECASE)

    # Extraer el contenido, manejando posibles espacios y formatos
    titulo = titulo.group(1).strip() if titulo else "Sin título"
    trama = trama.group(1).strip() if trama else "Sin trama"
    personajes = personajes.group(1).strip() if personajes else "Sin personajes"
    ambientacion = ambientacion.group(1).strip() if ambientacion else "Sin ambientación"
    tecnica = tecnica.group(1).strip() if tecnica else "Sin técnicas literarias"

    return titulo, trama, personajes, ambientacion, tecnica

# Función para generar cada escena
def generar_escena(capitulo, escena, trama, personajes, ambientacion, tecnica, palabras):
    # Estimar tokens: 1 palabra ≈ 1.3 tokens
    max_tokens = int(palabras * 1.3)
    prompt = f"""
Escribe la Escena {escena} del Capítulo {capitulo} de una novela de suspenso político con las siguientes características:

Trama: {trama}
Personajes: {personajes}
Ambientación: {ambientacion}
Técnicas literarias: {tecnica}

La escena debe tener aproximadamente {palabras} palabras, mantener la consistencia y coherencia, evitar clichés y frases hechas. 
Utiliza rayas (—) para las intervenciones de los personajes.
Debe incluir descripciones vívidas, diálogos agudos y dinámicos, y contribuir al desarrollo de la trama y los personajes.
"""
    escena_texto = call_openrouter_api(prompt, max_tokens=max_tokens)
    return escena_texto

# Función para generar la novela completa después de la aprobación
def generar_novela_completa(num_capitulos, num_escenas):
    titulo = st.session_state.titulo
    trama = st.session_state.trama
    personajes = st.session_state.personajes
    ambientacion = st.session_state.ambientacion
    tecnica = st.session_state.tecnica

    total_palabras = 40000
    total_escenas = num_capitulos * num_escenas
    palabras_por_escena_base = total_palabras // total_escenas
    palabras_restantes = total_palabras - (palabras_por_escena_base * total_escenas)

    # Crear una lista de palabras por escena con variación del ±10%
    palabras_por_escena = []
    for _ in range(total_escenas):
        variacion = random.randint(-100, 100)  # Ajusta según la preferencia
        palabras = palabras_por_escena_base + variacion
        # Asegurar que cada escena tenga al menos 500 palabras
        palabras = max(500, palabras)
        palabras_por_escena.append(palabras)

    # Ajustar las palabras restantes
    for i in range(palabras_restantes):
        palabras_por_escena[i % total_escenas] += 1

    novela = f"**{titulo}**\n\n"

    # Inicializar la barra de progreso
    progress_bar = st.progress(0)
    progress_text = st.empty()
    current = 0

    escena_index = 0  # Índice para acceder a palabras_por_escena
    palabras_por_capitulo = {cap: [] for cap in range(1, num_capitulos + 1)}  # Para la gráfica

    # Generar cada capítulo y escena
    for cap in range(1, num_capitulos + 1):
        novela += f"## Capítulo {cap}\n\n"
        for esc in range(1, num_escenas + 1):
            palabras_escena = palabras_por_escena[escena_index]
            palabras_por_capitulo[cap].append(palabras_escena)
            with st.spinner(f"Generando Capítulo {cap}, Escena {esc} ({palabras_escena} palabras)..."):
                escena = generar_escena(cap, esc, trama, personajes, ambientacion, tecnica, palabras_escena)
                if not escena:
                    st.error(f"No se pudo generar la Escena {esc} del Capítulo {cap}.")
                    return None
                # Limpiar saltos de línea manuales, reemplazándolos por saltos de párrafo
                escena = escena.replace('\r\n', '\n').replace('\n', '\n\n')
                novela += f"### Escena {esc}\n\n{escena}\n\n"
                # Contar palabras generadas (estimación simple)
                # Puedes mejorar esto con un conteo más preciso si lo deseas
                # total_palabras_generadas += len(escena.split())
                # Actualizar la barra de progreso
                current += 1
                progress_bar.progress(current / total_escenas)
                progress_text.text(f"Progreso: {current}/{total_escenas} escenas generadas.")
                escena_index += 1
                # Retraso para evitar exceder los límites de la API
                time.sleep(1)

    # Ocultar la barra de progreso y el texto de progreso
    progress_bar.empty()
    progress_text.empty()

    # Mostrar el total de palabras generadas estimadas
    total_palabras_generadas = len(novela.split())
    st.write(f"**Total de palabras generadas estimadas:** {total_palabras_generadas}")

    # Graficar la distribución de palabras por capítulo
    fig, ax = plt.subplots(figsize=(10, 6))
    for cap in palabras_por_capitulo:
        ax.plot(range(1, num_escenas + 1), palabras_por_capitulo[cap], marker='o', label=f'Capítulo {cap}')
    ax.set_xlabel('Escena')
    ax.set_ylabel('Palabras')
    ax.set_title('Distribución de Palabras por Escena en Cada Capítulo')
    ax.legend()
    st.pyplot(fig)

    st.session_state.novela_completa = novela
    st.session_state.etapa = "completado"

    return novela

# Función para exportar la novela a un archivo de Word con el formato especificado
def exportar_a_word(titulo, novela_completa):
    document = Document()

    # Configurar el tamaño de la página y márgenes
    section = document.sections[0]
    section.page_width = Inches(6)
    section.page_height = Inches(9)
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.7)
    section.right_margin = Inches(0.7)

    # Establecer el estilo normal con una fuente común
    style = document.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'  # Cambiado a una fuente común
    font.size = Pt(12)

    # Agregar el título
    titulo_paragraph = document.add_heading(titulo, level=0)
    titulo_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

    # Agregar la tabla de contenidos
    agregar_tabla_de_contenidos(document)
    document.add_page_break()

    # Separar la novela por capítulos
    capítulos = novela_completa.split("## Capítulo")
    for cap in capítulos:
        cap = cap.strip()
        if not cap:
            continue
        cap_num_match = re.match(r"(\d+)", cap)
        cap_num = cap_num_match.group(1) if cap_num_match else "Sin número"
        cap_content = cap.split('\n', 1)[1].strip() if '\n' in cap else ""

        # Agregar el capítulo
        document.add_heading(f"Capítulo {cap_num}", level=1)

        # Separar por escenas
        escenas = cap_content.split("### Escena")
        for esc in escenas:
            esc = esc.strip()
            if not esc:
                continue
            esc_num_match = re.match(r"(\d+)", esc)
            esc_num = esc_num_match.group(1) if esc_num_match else "Sin número"
            esc_text = esc.split('\n', 1)[1].strip() if '\n' in esc else ""

            # Agregar la escena
            document.add_heading(f"Escena {esc_num}", level=2)

            # Agregar el texto de la escena con saltos de párrafo
            for paragraph_text in esc_text.split('\n\n'):
                paragraph_text = paragraph_text.strip()
                if paragraph_text:
                    paragraph = document.add_paragraph(paragraph_text)
                    paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY
                    paragraph_format = paragraph.paragraph_format
                    paragraph_format.line_spacing = 1.15
                    paragraph_format.space_after = Pt(6)

    # Agregar el conteo total de palabras al final del documento
    total_palabras = len(novela_completa.split())
    document.add_page_break()
    document.add_paragraph(f"**Total de palabras generadas:** {total_palabras}", style='Intense Quote')

    # Guardar el documento en memoria
    buffer = BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer

# Función para agregar una tabla de contenidos automática
def agregar_tabla_de_contenidos(document):
    paragraph = document.add_paragraph()
    run = paragraph.add_run()
    fldChar1 = OxmlElement('w:fldChar')
    fldChar1.set(qn('w:fldCharType'), 'begin')
    instrText = OxmlElement('w:instrText')
    instrText.text = 'TOC \\o "1-3" \\h \\z \\u'
    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'separate')
    fldChar3 = OxmlElement('w:fldChar')
    fldChar3.set(qn('w:fldCharType'), 'end')
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)
    run._r.append(fldChar3)

# Interfaz de usuario para aprobar la estructura inicial
def mostrar_aprobacion():
    st.header("Aprobación de Elementos Iniciales")
    st.subheader("Título")
    st.write(st.session_state.titulo)

    st.subheader("Trama")
    st.write(st.session_state.trama)

    st.subheader("Personajes")
    st.write(st.session_state.personajes)

    st.subheader("Ambientación")
    st.write(st.session_state.ambientacion)

    st.subheader("Técnicas Literarias")
    st.write(st.session_state.tecnica)

    # Alinear los botones a la izquierda sin columnas
    aprobar = st.button("Aprobar y Generar Novela", key="aprobar")
    if aprobar:
        st.session_state.etapa = "generacion"

    rechazar = st.button("Rechazar y Regenerar Estructura", key="rechazar")
    if rechazar:
        # Reiniciamos los valores
        st.session_state.estructura = None
        st.session_state.titulo = ""
        st.session_state.trama = ""
        st.session_state.personajes = ""
        st.session_state.ambientacion = ""
        st.session_state.tecnica = ""
        st.session_state.etapa = "inicio"

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
                    titulo, trama, personajes, ambientacion, tecnica = extraer_elementos(estructura)
                    # Guardar en el estado de la sesión
                    st.session_state.estructura = estructura
                    st.session_state.titulo = titulo
                    st.session_state.trama = trama
                    st.session_state.personajes = personajes
                    st.session_state.ambientacion = ambientacion
                    st.session_state.tecnica = tecnica
                    st.session_state.etapa = "aprobacion"
                else:
                    st.error("No se pudo generar la estructura inicial. Por favor, intente nuevamente.")

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
