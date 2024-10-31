import streamlit as st
import requests
import time
from docx import Document
from docx.shared import Pt
from io import BytesIO
import json

# Configuración de la página
st.set_page_config(page_title="Generador de Novelas de Thriller Político", layout="wide")

# Función para llamar a la API de OpenRouter
def call_openrouter_api(messages):
    api_url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}"
    }
    data = {
        "model": "openai/gpt-4o-mini",
        "messages": messages
    }
    response = requests.post(api_url, headers=headers, json=data)
    if response.status_code != 200:
        st.error(f"Error en la API de OpenRouter: {response.status_code} - {response.text}")
        st.stop()
    return response.json()["choices"][0]["message"]["content"].strip()

# Función para planificar la novela
def plan_novel(theme):
    prompt = [
        {"role": "user", "content": f"Planifica una novela de thriller político basada en el siguiente tema: {theme}. Genera la trama principal y las subtramas."}
    ]
    return call_openrouter_api(prompt)

# Función para distribuir la trama en capítulos y secciones
def distribute_plot(plot):
    prompt = [
        {"role": "user", "content": f"Distribuye la siguiente trama en 12 capítulos, cada uno con 5 secciones. Proporciona una lista estructurada con capítulos y secciones.\n\nTrama: {plot}"}
    ]
    return call_openrouter_api(prompt)

# Función para describir cada sección
def describe_sections(distribution):
    prompt = [
        {"role": "user", "content": f"Describe detalladamente qué sucede en cada una de las siguientes 60 secciones para asegurar coherencia y consistencia en la trama.\n\nDistribución: {distribution}"}
    ]
    return call_openrouter_api(prompt)

# Función para escribir una sección
def write_section(section_description):
    prompt = [
        {"role": "user", "content": f"Escribe una sección de aproximadamente 1000 palabras con las siguientes características de un thriller político: mucha acción, ritmo rápido, descripciones vívidas, finales de escena con ganchos para mantener la atención del lector. Evita descripciones excesivas y frases cliché. Utiliza raya para los diálogos.\n\nDescripción de la sección: {section_description}"}
    ]
    return call_openrouter_api(prompt)

# Función para crear el documento Word
def create_word_document(chapters, sections_content):
    doc = Document()
    doc.add_heading("Novela de Thriller Político", 0)

    for chapter_num, chapter in enumerate(chapters, start=1):
        doc.add_heading(f"Capítulo {chapter_num}: {chapter['title']}", level=1)
        for section_num, section in enumerate(chapter['sections'], start=1):
            doc.add_heading(f"Sección {chapter_num}.{section_num}: {section['title']}", level=2)
            paragraph = doc.add_paragraph(sections_content[f"{chapter_num}.{section_num}"])
            paragraph.style.font.size = Pt(12)
    
    # Guardar el documento en un objeto BytesIO
    byte_io = BytesIO()
    doc.save(byte_io)
    byte_io.seek(0)
    return byte_io

# Título de la aplicación
st.title("Generador de Novelas de Thriller Político")

# Entrada para el tema de la novela
theme = st.text_input("Ingresa el tema de tu novela de thriller político:", "")

# Inicializar variables de estado
if 'plan' not in st.session_state:
    st.session_state.plan = None
if 'distribution' not in st.session_state:
    st.session_state.distribution = None
if 'sections_description' not in st.session_state:
    st.session_state.sections_description = None
if 'sections_content' not in st.session_state:
    st.session_state.sections_content = {}
if 'chapters' not in st.session_state:
    st.session_state.chapters = []
if 'step' not in st.session_state:
    st.session_state.step = 0
if 'completed' not in st.session_state:
    st.session_state.completed = False

# Función para reiniciar el proceso
def reset_process():
    st.session_state.plan = None
    st.session_state.distribution = None
    st.session_state.sections_description = None
    st.session_state.sections_content = {}
    st.session_state.chapters = []
    st.session_state.step = 0
    st.session_state.completed = False

# Botón para reiniciar
if st.button("Reiniciar Proceso"):
    reset_process()
    st.success("Proceso reiniciado.")

# Botón para iniciar el proceso
if st.button("Generar Novela"):
    if not theme.strip():
        st.error("Por favor, ingresa un tema para la novela.")
    else:
        with st.spinner("Planificando la trama de la novela..."):
            plot = plan_novel(theme)
            st.session_state.plan = plot
            st.session_state.step = 1

# Mostrar el plan para aprobación si está disponible
if st.session_state.step == 1 and st.session_state.plan:
    st.subheader("Plan de la Novela")
    st.write(st.session_state.plan)
    st.write("¿Deseas aprobar este plan y continuar con la generación de la novela?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Aprobar y Continuar"):
            st.session_state.step = 2
    with col2:
        if st.button("Cancelar"):
            reset_process()
            st.info("Proceso cancelado.")

# Continuar con la generación si el plan fue aprobado
if st.session_state.step == 2:
    # Barra de progreso
    progress_bar = st.progress(0)
    status_text = st.empty()

    # Paso 2: Distribuir la trama en capítulos y secciones
    status_text.text("Distribuyendo la trama en capítulos y secciones...")
    distribution = distribute_plot(st.session_state.plan)
    st.session_state.distribution = distribution
    progress_bar.progress(20)
    time.sleep(1)

    # Paso 3: Describir cada sección
    status_text.text("Describiendo cada sección...")
    sections_description = describe_sections(st.session_state.distribution)
    st.session_state.sections_description = sections_description
    progress_bar.progress(40)
    time.sleep(1)

    # Procesar la distribución y las descripciones
    try:
        distribution_data = json.loads(st.session_state.distribution)
        sections_description_data = json.loads(st.session_state.sections_description)
    except json.JSONDecodeError:
        st.error("Error al procesar la respuesta de la API. Asegúrate de que el formato sea JSON válido.")
        st.stop()

    # Crear una estructura de capítulos y secciones
    st.session_state.chapters = []
    for chapter in distribution_data.get("capítulos", []):
        chapter_dict = {
            "title": chapter.get("título", f"Capítulo {len(st.session_state.chapters)+1}"),
            "sections": [{"title": sec.get("título", f"Sección {i+1}")} for i, sec in enumerate(chapter.get("secciones", []))]
        }
        st.session_state.chapters.append(chapter_dict)

    # Asignar descripciones a cada sección
    for idx, section_desc in enumerate(sections_description_data.get("secciones", []), start=1):
        chapter_num = (idx - 1) // 5 + 1
        section_num = (idx - 1) % 5 + 1
        section_key = f"{chapter_num}.{section_num}"
        st.session_state.sections_content[section_key] = section_desc.get("descripción", "")

    progress_bar.progress(50)
    status_text.text("Descripción de secciones completada.")
    time.sleep(1)

    # Paso 4: Escribir cada sección
    status_text.text("Escribiendo cada sección de la novela...")
    total_sections = 12 * 5
    for idx in range(1, total_sections + 1):
        chapter_num = (idx - 1) // 5 + 1
        section_num = (idx - 1) % 5 + 1
        section_key = f"{chapter_num}.{section_num}"
        description = st.session_state.sections_content.get(section_key, "")
        if not description:
            st.error(f"Descripción faltante para la sección {section_key}.")
            break
        content = write_section(description)
        st.session_state.sections_content[section_key] = content
        progress = 50 + (50 * idx) // total_sections
        progress_bar.progress(progress)
        status_text.text(f"Escribiendo sección {idx} de {total_sections}...")
        time.sleep(0.5)  # Pausa para no sobrecargar la API

    progress_bar.progress(100)
    status_text.text("Generación de la novela completada.")
    st.session_state.step = 3

    # Paso 5: Crear y ofrecer el documento Word
    with st.spinner("Creando el documento Word..."):
        word_doc = create_word_document(st.session_state.chapters, st.session_state.sections_content)
    st.success("¡Novela generada exitosamente!")
    st.download_button(
        label="Descargar Novela en Word",
        data=word_doc,
        file_name="novela_thriller_politico.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

# Mostrar progreso si el proceso está en curso
if st.session_state.step == 3 and st.session_state.completed:
    st.balloons()
