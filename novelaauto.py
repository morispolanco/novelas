import streamlit as st
import requests
import time
from docx import Document
from docx.shared import Pt
from io import BytesIO
import json
import sqlite3
import uuid
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Generador de Novelas de Thriller Político", layout="wide")

# Conexión a la base de datos SQLite
def get_db_connection():
    conn = sqlite3.connect('novel_generator.db')
    conn.row_factory = sqlite3.Row
    return conn

# Inicializar la base de datos
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS novel_progress (
            id TEXT PRIMARY KEY,
            theme TEXT,
            plan TEXT,
            distribution TEXT,
            sections_description TEXT,
            sections_content TEXT,
            chapters TEXT,
            step INTEGER,
            completed BOOLEAN
        )
    ''')
    conn.commit()
    conn.close()

# Llamada a la API de OpenRouter
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

# Funciones para las etapas de generación de la novela
def plan_novel(theme):
    prompt = [
        {"role": "user", "content": f"Planifica una novela de thriller político basada en el siguiente tema: {theme}. Genera la trama principal y las subtramas."}
    ]
    return call_openrouter_api(prompt)

def distribute_plot(plot):
    prompt = [
        {"role": "user", "content": f"Distribuye la siguiente trama en 12 capítulos, cada uno con 5 secciones. Proporciona una lista estructurada con capítulos y secciones.\n\nTrama: {plot}"}
    ]
    return call_openrouter_api(prompt)

def describe_sections(distribution):
    prompt = [
        {"role": "user", "content": f"Describe detalladamente qué sucede en cada una de las siguientes 60 secciones para asegurar coherencia y consistencia en la trama.\n\nDistribución: {distribution}"}
    ]
    return call_openrouter_api(prompt)

def write_section(section_description):
    prompt = [
        {"role": "user", "content": f"Escribe una sección de aproximadamente 1000 palabras con las siguientes características de un thriller político: mucha acción, ritmo rápido, descripciones vívidas, finales de escena con ganchos para mantener la atención del lector. Evita descripciones excesivas y frases cliché. Utiliza raya para los diálogos.\n\nDescripción de la sección: {section_description}"}
    ]
    return call_openrouter_api(prompt)

def create_word_document(chapters, sections_content):
    doc = Document()
    doc.add_heading("Novela de Thriller Político", 0)

    for chapter_num, chapter in enumerate(chapters, start=1):
        doc.add_heading(f"Capítulo {chapter_num}: {chapter['title']}", level=1)
        for section_num, section in enumerate(chapter['sections'], start=1):
            doc.add_heading(f"Sección {chapter_num}.{section_num}: {section['title']}", level=2)
            paragraph = doc.add_paragraph(sections_content.get(f"{chapter_num}.{section_num}", "Contenido no disponible."))
            paragraph.style.font.size = Pt(12)

    # Guardar el documento en un objeto BytesIO
    byte_io = BytesIO()
    doc.save(byte_io)
    byte_io.seek(0)
    return byte_io

# Inicializar la base de datos al iniciar la aplicación
init_db()

# Título de la aplicación
st.title("Generador de Novelas de Thriller Político")

# Entrada para el tema de la novela
theme = st.text_input("Ingresa el tema de tu novela de thriller político:", "")

# Conexión a la base de datos
conn = get_db_connection()
cursor = conn.cursor()

# Generar un ID único para cada proceso basado en el tema y la marca de tiempo
def generate_unique_id(theme):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = f"{theme}_{timestamp}_{uuid.uuid4().hex[:6]}"
    return unique_id

# Buscar procesos existentes para el tema ingresado
def get_existing_processes(theme):
    cursor.execute("SELECT * FROM novel_progress WHERE theme = ? AND completed = FALSE", (theme,))
    return cursor.fetchall()

# Función para reiniciar el proceso
def reset_process(process_id):
    cursor.execute("DELETE FROM novel_progress WHERE id = ?", (process_id,))
    conn.commit()
    st.session_state.reset = True

# Botón para reiniciar todos los procesos (opcional)
if st.button("Reiniciar Todos los Procesos"):
    cursor.execute("DELETE FROM novel_progress WHERE completed = FALSE")
    conn.commit()
    st.success("Todos los procesos no completados han sido eliminados.")

# Inicializar variables de estado
if 'current_process_id' not in st.session_state:
    st.session_state.current_process_id = None
if 'reset' not in st.session_state:
    st.session_state.reset = False

# Manejar el reset del proceso
if st.session_state.reset:
    st.session_state.current_process_id = None
    st.session_state.reset = False

# Botón para iniciar el proceso
if st.button("Generar Novela"):
    if not theme.strip():
        st.error("Por favor, ingresa un tema para la novela.")
    else:
        existing_processes = get_existing_processes(theme)
        if existing_processes:
            st.warning("Ya existe un proceso en curso para este tema. Puedes continuar desde donde lo dejaste o reiniciar el proceso.")
            for process in existing_processes:
                st.write(f"**ID del Proceso:** {process['id']}")
                st.write(f"**Fecha de Inicio:** {process['id'].split('_')[-2]}")
                if st.button(f"Continuar con el Proceso {process['id']}"):
                    st.session_state.current_process_id = process['id']
                if st.button(f"Reiniciar el Proceso {process['id']}"):
                    reset_process(process['id'])
        else:
            # Crear un nuevo proceso
            new_id = generate_unique_id(theme)
            cursor.execute('''
                INSERT INTO novel_progress (id, theme, plan, distribution, sections_description, sections_content, chapters, step, completed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (new_id, theme, None, None, None, json.dumps({}), json.dumps([]), 0, False))
            conn.commit()
            st.session_state.current_process_id = new_id
            st.success(f"Nuevo proceso iniciado con ID: {new_id}")

# Si hay un proceso seleccionado, continuar con él
if st.session_state.current_process_id:
    process_id = st.session_state.current_process_id
    cursor.execute("SELECT * FROM novel_progress WHERE id = ?", (process_id,))
    process = cursor.fetchone()
    if not process:
        st.error("Proceso no encontrado.")
    else:
        theme = process['theme']
        step = process['step']
        plan = process['plan']
        distribution = process['distribution']
        sections_description = process['sections_description']
        sections_content = json.loads(process['sections_content'])
        chapters = json.loads(process['chapters'])

        # Barra de progreso
        progress_bar = st.progress((step / 4) * 100)
        status_text = st.empty()

        # Paso 1: Planificación de la novela
        if step >= 1 and not plan:
            status_text.text("Planificando la trama de la novela...")
            plot = plan_novel(theme)
            plan = plot
            cursor.execute("UPDATE novel_progress SET plan = ?, step = ? WHERE id = ?", (plan, 1, process_id))
            conn.commit()
            progress_bar.progress(25)
            time.sleep(1)

        # Mostrar el plan para aprobación si el paso es 1
        if step == 1 and plan:
            st.subheader("Plan de la Novela")
            st.write(plan)
            st.write("¿Deseas aprobar este plan y continuar con la generación de la novela?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Aprobar y Continuar (Proceso {process_id})"):
                    cursor.execute("UPDATE novel_progress SET step = ? WHERE id = ?", (2, process_id))
                    conn.commit()
                    st.experimental_rerun()
            with col2:
                if st.button(f"Cancelar (Proceso {process_id})"):
                    reset_process(process_id)
                    st.info("Proceso cancelado.")
                    st.experimental_rerun()

        # Paso 2: Distribuir la trama en capítulos y secciones
        if step >= 2 and not distribution:
            status_text.text("Distribuyendo la trama en capítulos y secciones...")
            distribution = distribute_plot(plan)
            cursor.execute("UPDATE novel_progress SET distribution = ?, step = ? WHERE id = ?", (distribution, 3, process_id))
            conn.commit()
            progress_bar.progress(50)
            time.sleep(1)

        # Paso 3: Describir cada sección
        if step >= 3 and not sections_description:
            status_text.text("Describiendo cada sección...")
            sections_description = describe_sections(distribution)
            cursor.execute("UPDATE novel_progress SET sections_description = ?, step = ? WHERE id = ?", (sections_description, 4, process_id))
            conn.commit()
            progress_bar.progress(75)
            time.sleep(1)

        # Procesar la distribución y las descripciones
        if step >= 4 and sections_description:
            try:
                distribution_data = json.loads(distribution)
                sections_description_data = json.loads(sections_description)
            except json.JSONDecodeError:
                st.error("Error al procesar la respuesta de la API. Asegúrate de que el formato sea JSON válido.")
                st.stop()

            # Crear una estructura de capítulos y secciones si aún no se ha hecho
            if not chapters:
                chapters = []
                for chapter in distribution_data.get("capítulos", []):
                    chapter_dict = {
                        "title": chapter.get("título", f"Capítulo {len(chapters)+1}"),
                        "sections": [{"title": sec.get("título", f"Sección {i+1}"), "description": sec.get("descripción", "")} for i, sec in enumerate(chapter.get("secciones", []))]
                    }
                    chapters.append(chapter_dict)
                cursor.execute("UPDATE novel_progress SET chapters = ? WHERE id = ?", (json.dumps(chapters), process_id))
                conn.commit()

            # Asignar descripciones a cada sección si aún no se ha hecho
            if not any("description" in sec for chap in chapters for sec in chap['sections']):
                for chap_idx, chapter in enumerate(chapters):
                    for sec_idx, section in enumerate(chapter['sections']):
                        section_key = f"{chap_idx + 1}.{sec_idx + 1}"
                        section['description'] = sections_description_data.get("secciones", [])[chap_idx * 5 + sec_idx].get("descripción", "")
                cursor.execute("UPDATE novel_progress SET chapters = ? WHERE id = ?", (json.dumps(chapters), process_id))
                conn.commit()

            # Escribir cada sección
            total_sections = 12 * 5
            completed_sections = len([content for content in sections_content.values() if content.strip() != ""])
            remaining_sections = total_sections - completed_sections

            if remaining_sections > 0:
                status_text.text("Escribiendo cada sección de la novela...")
                for chap_idx, chapter in enumerate(chapters):
                    for sec_idx, section in enumerate(chapter['sections']):
                        section_key = f"{chap_idx + 1}.{sec_idx + 1}"
                        if sections_content.get(section_key, "").strip() == "":
                            description = section.get("description", "")
                            if not description:
                                st.error(f"Descripción faltante para la sección {section_key}.")
                                break
                            content = write_section(description)
                            sections_content[section_key] = content
                            # Actualizar el contenido en la base de datos
                            cursor.execute("UPDATE novel_progress SET sections_content = ? WHERE id = ?", (json.dumps(sections_content), process_id))
                            conn.commit()
                            completed_sections += 1
                            progress = 75 + (25 * completed_sections) // total_sections
                            progress_bar.progress(progress)
                            status_text.text(f"Escribiendo sección {completed_sections} de {total_sections}...")
                            time.sleep(0.5)  # Pausa para no sobrecargar la API

            # Verificar si todas las secciones están completas
            if completed_sections == total_sections:
                # Crear el documento Word
                status_text.text("Creando el documento Word...")
                word_doc = create_word_document(chapters, sections_content)
                # Actualizar el estado como completado
                cursor.execute("UPDATE novel_progress SET completed = ?, step = ? WHERE id = ?", (True, 5, process_id))
                conn.commit()
                progress_bar.progress(100)
                st.success("¡Novela generada exitosamente!")
                st.download_button(
                    label="Descargar Novela en Word",
                    data=word_doc,
                    file_name="novela_thriller_politico.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
        elif step >= 4 and process['completed']:
            # Si el proceso ya está completado
            st.success("¡Novela generada exitosamente!")
            word_doc = create_word_document(chapters, sections_content)
            st.download_button(
                label="Descargar Novela en Word",
                data=word_doc,
                file_name="novela_thriller_politico.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

# Cerrar la conexión a la base de datos
conn.close()
