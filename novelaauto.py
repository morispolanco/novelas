import streamlit as st
import requests
import time
from docx import Document
from docx.shared import Pt
from io import BytesIO

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

# Botón para iniciar el proceso
if st.button("Generar Novela"):
    if not theme.strip():
        st.error("Por favor, ingresa un tema para la novela.")
    else:
        # Barra de progreso
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Paso 1: Planificación de la novela
        status_text.text("Planificando la trama de la novela...")
        plot = plan_novel(theme)
        progress_bar.progress(10)
        time.sleep(1)

        # Paso 2: Distribuir la trama en capítulos y secciones
        status_text.text("Distribuyendo la trama en capítulos y secciones...")
        distribution = distribute_plot(plot)
        progress_bar.progress(20)
        time.sleep(1)

        # Paso 3: Describir cada sección
        status_text.text("Describiendo cada sección...")
        sections_description = describe_sections(distribution)
        progress_bar.progress(30)
        time.sleep(1)

        # Procesar la distribución y las descripciones
        import json

        try:
            distribution_data = json.loads(distribution)
            sections_description_data = json.loads(sections_description)
        except json.JSONDecodeError:
            st.error("Error al procesar la respuesta de la API. Asegúrate de que el formato sea JSON válido.")
            st.stop()

        # Crear una estructura de capítulos y secciones
        chapters = []
        sections_content = {}
        for chapter in distribution_data["capítulos"]:
            chapter_dict = {
                "title": chapter["título"],
                "sections": []
            }
            chapters.append(chapter_dict)

        # Asumiendo que sections_description_data es una lista de descripciones en orden
        for idx, section_desc in enumerate(sections_description_data["secciones"], start=1):
            chapter_num = (idx - 1) // 5 + 1
            section_num = (idx - 1) % 5 + 1
            chapter = chapters[chapter_num - 1]
            section_title = chapter["sections"].append({"title": section_desc["título"]})
            # Guardar las descripciones para escribir luego
            sections_content[f"{chapter_num}.{section_num}"] = section_desc["descripción"]

        progress_bar.progress(40)
        status_text.text("Descripción de secciones completada.")
        time.sleep(1)

        # Paso 4: Escribir cada sección
        status_text.text("Escribiendo cada sección de la novela...")
        total_sections = 12 * 5
        for idx in range(1, total_sections + 1):
            chapter_num = (idx - 1) // 5 + 1
            section_num = (idx - 1) % 5 + 1
            section_key = f"{chapter_num}.{section_num}"
            description = sections_description_data["secciones"][idx - 1]["descripción"]
            content = write_section(description)
            sections_content[section_key] = content
            progress_bar.progress(40 + (60 * idx) // total_sections)
            status_text.text(f"Escribiendo sección {idx} de {total_sections}...")
            time.sleep(0.5)  # Pequeña pausa para no sobrecargar la API

        progress_bar.progress(100)
        status_text.text("Generación de la novela completada.")

        # Paso 5: Crear y ofrecer el documento Word
        status_text.text("Creando el documento Word...")
        word_doc = create_word_document(distribution_data["capítulos"], sections_content)

        st.success("¡Novela generada exitosamente!")
        st.download_button(
            label="Descargar Novela en Word",
            data=word_doc,
            file_name="novela_thriller_politico.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
