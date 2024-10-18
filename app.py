import streamlit as st
import requests
import markdown
from bs4 import BeautifulSoup
from docx import Document
from io import BytesIO
import re
import time

# Configuración de la página
st.set_page_config(
    page_title="Generador de Novelas",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Título de la aplicación
st.title("Generador de Novelas Automático")

# Descripción de la aplicación
st.markdown("""
Esta aplicación genera automáticamente una novela basada en el título, género y audiencia proporcionados. 
Puedes generar capítulos y escenas de manera continua, permitiéndote descargar contenido parcial en cualquier momento.
Finalmente, puedes exportar la novela completa a un archivo en formato Word.
""")

# Inicialización de variables en el estado de la sesión
if 'title' not in st.session_state:
    st.session_state.title = ""
if 'genre' not in st.session_state:
    st.session_state.genre = ""
if 'audience' not in st.session_state:
    st.session_state.audience = ""
if 'plot' not in st.session_state:
    st.session_state.plot = ""
if 'characters' not in st.session_state:
    st.session_state.characters = ""
if 'setting' not in st.session_state:
    st.session_state.setting = ""
if 'narrative_technique' not in st.session_state:
    st.session_state.narrative_technique = ""
if 'table_of_chapters' not in st.session_state:
    st.session_state.table_of_chapters = []
if 'chapters' not in st.session_state:
    st.session_state.chapters = []  # Lista de diccionarios: [{'number': 1, 'title': 'Título', 'scenes': [{'number':1, 'title':'Título', 'content':'Contenido'}]}, ...]
if 'current_chapter' not in st.session_state:
    st.session_state.current_chapter = 1
if 'current_scene' not in st.session_state:
    st.session_state.current_scene = 1
if 'total_chapters' not in st.session_state:
    st.session_state.total_chapters = 9  # Total de capítulos
if 'total_scenes' not in st.session_state:
    st.session_state.total_scenes = 5  # Total de escenas por capítulo
if 'total_paragraphs' not in st.session_state:
    st.session_state.total_paragraphs = 9  # Total de párrafos por escena
if 'markdown_content' not in st.session_state:
    st.session_state.markdown_content = ""
if 'generation_complete' not in st.session_state:
    st.session_state.generation_complete = False
if 'selected_chapter' not in st.session_state:
    st.session_state.selected_chapter = None
if 'selected_scene' not in st.session_state:
    st.session_state.selected_scene = None

# Función para reiniciar el estado de la sesión
def reset_session():
    st.session_state.title = ""
    st.session_state.genre = ""
    st.session_state.audience = ""
    st.session_state.plot = ""
    st.session_state.characters = ""
    st.session_state.setting = ""
    st.session_state.narrative_technique = ""
    st.session_state.table_of_chapters = []
    st.session_state.chapters = []
    st.session_state.current_chapter = 1
    st.session_state.current_scene = 1
    st.session_state.markdown_content = ""
    st.session_state.generation_complete = False
    st.session_state.selected_chapter = None
    st.session_state.selected_scene = None

# Función para llamar a la API de OpenRouter con reintentos
def call_openrouter_api(messages, model="openai/gpt-4o-mini", retries=3, delay_sec=2):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}"
    }
    data = {
        "model": model,
        "messages": messages
    }
    for attempt in range(retries):
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content'].strip()
        except requests.exceptions.HTTPError as err:
            st.error(f"Error en la API: {err}")
        except Exception as e:
            st.error(f"Error inesperado: {e}")
        if attempt < retries - 1:
            st.warning(f"Reintentando en {delay_sec} segundos...")
            time.sleep(delay_sec)
    st.error("No se pudo obtener una respuesta válida de la API después de varios intentos.")
    return None

# Funciones para generar elementos de la novela

def generate_initial_elements(title, genre, audience):
    prompt = f"""A partir de la siguiente información, genera la trama, los personajes, la ambientación y la técnica narrativa para una novela.

Título: {title}
Género: {genre}
Audiencia: {audience}

Proporciona la respuesta en el siguiente formato:

Trama: [Descripción de la trama]
Personajes: [Descripción de los personajes principales]
Ambientación: [Descripción de la ambientación]
Técnica Narrativa: [Descripción de la técnica narrativa]
"""
    messages = [
        {"role": "user", "content": prompt}
    ]
    response = call_openrouter_api(messages)
    if response:
        # Separar los elementos
        elements = {}
        for line in response.split('\n'):
            if line.startswith("Trama:"):
                elements['plot'] = line.replace("Trama:", "").strip()
            elif line.startswith("Personajes:"):
                elements['characters'] = line.replace("Personajes:", "").strip()
            elif line.startswith("Ambientación:"):
                elements['setting'] = line.replace("Ambientación:", "").strip()
            elif line.startswith("Técnica Narrativa:"):
                elements['narrative_technique'] = line.replace("Técnica Narrativa:", "").strip()
        return elements
    return None

def generate_table_of_chapters(title, genre, audience, total_chapters):
    prompt = f"""A partir de la siguiente información, genera una tabla de contenidos con {total_chapters} capítulos para una novela.

Título: {title}
Género: {genre}
Audiencia: {audience}

Proporciona la respuesta en el siguiente formato:

Capítulo 1: [Título del Capítulo 1]
Capítulo 2: [Título del Capítulo 2]
...
Capítulo {total_chapters}: [Título del Capítulo {total_chapters}]
"""
    messages = [
        {"role": "user", "content": prompt}
    ]
    response = call_openrouter_api(messages)
    if response:
        table = []
        for line in response.split('\n'):
            if line.startswith("Capítulo"):
                parts = line.split(":")
                if len(parts) >= 2:
                    try:
                        chap_num = int(parts[0].split(" ")[1])
                        chap_title = parts[1].strip()
                        table.append({"number": chap_num, "title": chap_title, "scenes": []})
                    except ValueError:
                        continue  # Ignorar líneas que no siguen el formato esperado
        return table
    return None

def generate_scene_title(title, genre, audience, chapter_num, scene_num):
    prompt = f"""Genera un título único y descriptivo para la escena {scene_num} del capítulo {chapter_num} de una novela.

Título de la novela: {title}
Género: {genre}
Audiencia: {audience}

Proporciona la respuesta en el siguiente formato:

Título de la Escena {scene_num}: [Título Único]
"""
    messages = [
        {"role": "user", "content": prompt}
    ]
    response = call_openrouter_api(messages)
    if response:
        for line in response.split('\n'):
            if line.startswith(f"Título de la Escena {scene_num}:"):
                return line.replace(f"Título de la Escena {scene_num}:", "").strip()
    return None

def generate_scene_content(title, genre, audience, chapter_num, scene_num, scene_title):
    prompt = f"""Escribe el contenido de la escena {scene_num} del capítulo {chapter_num} para una novela basada en la siguiente información.

Título de la novela: {title}
Género: {genre}
Audiencia: {audience}
Trama: {st.session_state.plot}
Personajes: {st.session_state.characters}
Ambientación: {st.session_state.setting}
Técnica Narrativa: {st.session_state.narrative_technique}

La escena debe estar estructurada de manera clara y fluida, sin subdivisiones ni subsecciones. Debe contener exactamente 9 párrafos.

Proporciona la respuesta en el siguiente formato:

### Escena {scene_num}: {scene_title}
Párrafo 1.
Párrafo 2.
...
Párrafo 9.
"""
    messages = [
        {"role": "user", "content": prompt}
    ]
    response = call_openrouter_api(messages)
    return response

# Función para validar que cada escena tenga exactamente 9 párrafos
def validate_scene_paragraphs(scene_content, title, genre, audience, chapter_num, scene_num, scene_title, expected_paragraphs=9):
    """
    Verifica que el contenido de la escena tenga exactamente el número esperado de párrafos.
    Si es necesario, genera párrafos adicionales hasta alcanzar el número requerido.
    
    Parámetros:
    - scene_content (str): El contenido de la escena generado.
    - title (str): Título de la novela.
    - genre (str): Género de la novela.
    - audience (str): Audiencia de la novela.
    - chapter_num (int): Número del capítulo.
    - scene_num (int): Número de la escena.
    - scene_title (str): Título de la escena.
    - expected_paragraphs (int): Número esperado de párrafos por escena.
    
    Retorna:
    - str: El contenido validado de la escena.
    """
    # Extraer los párrafos, ignorando el título de la escena
    paragraphs = [p for p in scene_content.split('\n\n') if p.strip() != "" and not p.startswith("### Escena")]
    num_paragraphs = len(paragraphs)
    
    if num_paragraphs < expected_paragraphs:
        # Generar párrafos faltantes
        paragraphs_needed = expected_paragraphs - num_paragraphs
        additional_paragraphs = ""
        for _ in range(paragraphs_needed):
            prompt = f"""Agrega un párrafo adicional para la Escena {scene_num} del Capítulo {chapter_num} de la siguiente novela.

Título de la novela: {title}
Género: {genre}
Audiencia: {audience}
Trama: {st.session_state.plot}
Personajes: {st.session_state.characters}
Ambientación: {st.session_state.setting}
Técnica Narrativa: {st.session_state.narrative_technique}

Título de la Escena {scene_num}: {scene_title}

Contenido actual de la escena:
{scene_content}

Nuevo párrafo:"""
            messages = [
                {"role": "user", "content": prompt}
            ]
            new_paragraph = call_openrouter_api(messages)
            if new_paragraph:
                additional_paragraphs += f"{new_paragraph}\n\n"
            else:
                break  # Salir si hay un error en la generación
        
        # Agregar los párrafos adicionales
        paragraphs += [p.strip() for p in additional_paragraphs.strip().split('\n\n') if p.strip() != ""]
    
    elif num_paragraphs > expected_paragraphs:
        # Eliminar párrafos adicionales
        paragraphs = paragraphs[:expected_paragraphs]
    
    # Reconstruir el contenido de la escena
    validated_content = f"### Escena {scene_num}: {scene_title}\n\n" + "\n\n".join(paragraphs)
    return validated_content

# Función para generar el contenido Markdown de la novela
def update_markdown_content(chapter_num, chapter_title, scene_num, scene_title, scene_content):
    chapter_heading = f"## Capítulo {chapter_num}: {chapter_title}\n\n"
    scene_heading = f"### Escena {scene_num}: {scene_title}\n\n"
    st.session_state.markdown_content += f"{chapter_heading}{scene_heading}{scene_content}\n\n"

# Función para exportar a Word
def export_to_word(markdown_content, plot, characters, setting, narrative_technique, table_of_chapters):
    # Crear un documento de Word
    doc = Document()
    
    # Agregar Título
    doc.add_heading(st.session_state.title, level=0)
    
    # Agregar Género y Audiencia
    doc.add_paragraph(f"Género: {st.session_state.genre}")
    doc.add_paragraph(f"Audiencia: {st.session_state.audience}\n")
    
    # Agregar Trama, Personajes, Ambientación y Técnica Narrativa
    doc.add_heading("Trama", level=1)
    doc.add_paragraph(st.session_state.plot)
    
    doc.add_heading("Personajes", level=1)
    doc.add_paragraph(st.session_state.characters)
    
    doc.add_heading("Ambientación", level=1)
    doc.add_paragraph(st.session_state.setting)
    
    doc.add_heading("Técnica Narrativa", level=1)
    doc.add_paragraph(st.session_state.narrative_technique)
    
    # Agregar Tabla de Capítulos
    doc.add_heading("Tabla de Contenidos", level=1)
    for chap in table_of_chapters:
        doc.add_paragraph(f"Capítulo {chap['number']}: {chap['title']}", style='List Number')
    
    # Agregar Contenido de Capítulos y Escenas
    doc.add_heading("Contenido", level=1)
    html = markdown.markdown(markdown_content)
    soup = BeautifulSoup(html, 'html.parser')
    
    for element in soup.descendants:
        if isinstance(element, str):
            continue  # Ignorar cadenas de texto directas
        if element.name == 'h1':
            doc.add_heading(element.get_text(), level=1)
        elif element.name == 'h2':
            doc.add_heading(element.get_text(), level=2)
        elif element.name == 'h3':
            doc.add_heading(element.get_text(), level=3)
        elif element.name == 'p':
            doc.add_paragraph(element.get_text())
        # Ignorar encabezados de nivel 4 o más
    
    # Agregar Trama, Personajes, Ambientación y Técnica Narrativa al final si no se agregaron antes
    # Dependiendo de cómo quieras estructurar el documento
    
    # Guardar el documento en un objeto BytesIO
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- Barra Lateral ---
with st.sidebar:
    st.header("Menú de Navegación")
    
    # Botón para reiniciar la generación
    if st.button("Reiniciar Generación"):
        reset_session()
        st.success("Estado de la generación reiniciado.")
    
    st.markdown("---")
    
    # Menú desplegable para ver capítulos y escenas generados
    if st.session_state.chapters:
        chapter_titles = [f"Capítulo {chap['number']}: {chap['title']}" for chap in st.session_state.chapters]
        selected_chapter = st.selectbox(
            "Selecciona un capítulo para ver:",
            chapter_titles,
            key="select_chapter"
        )
        chapter_index = int(selected_chapter.split(" ")[1].replace(":", "")) - 1
        # Verificar que el índice esté dentro del rango
        if 0 <= chapter_index < len(st.session_state.chapters):
            st.session_state.selected_chapter = chapter_index
            chapter = st.session_state.chapters[chapter_index]
            if chapter['scenes']:
                scene_titles = [f"Escena {sec['number']}: {sec['title']}" for sec in chapter['scenes']]
                selected_scene = st.selectbox(
                    "Selecciona una escena para ver:",
                    scene_titles,
                    key="select_scene"
                )
                scene_index = int(selected_scene.split(" ")[1].replace(":", "")) - 1
                # Verificar que el índice esté dentro del rango
                if 0 <= scene_index < len(chapter['scenes']):
                    st.session_state.selected_scene = scene_index
                else:
                    st.error("Escena seleccionada no válida.")
            else:
                st.info("No hay escenas generadas aún en este capítulo.")
        else:
            st.error("Capítulo seleccionado no válido.")
    else:
        st.info("No hay capítulos generados aún.")

# --- Sección Principal ---

# Entrada de usuario para los elementos iniciales
if not st.session_state.title:
    with st.form("input_form"):
        st.subheader("Datos de la Novela")
        title = st.text_input("Título de la Novela:", "")
        genre = st.selectbox("Género:", ["Misterio", "Romance", "Ciencia Ficción", "Fantasía", "Terror", "Aventura", "Drama", "Comedia", "Histórica"])
        audience = st.selectbox("Audiencia:", ["Adolescentes", "Jóvenes Adultos", "Adultos", "Niños"])
        
        submitted = st.form_submit_button("Generar Novela")
        
        if submitted:
            if not title:
                st.warning("Por favor, ingresa un título para la novela.")
            else:
                with st.spinner("Generando trama, personajes, ambientación y técnica narrativa..."):
                    elements = generate_initial_elements(title, genre, audience)
                    if elements:
                        st.session_state.plot = elements.get('plot', "")
                        st.session_state.characters = elements.get('characters', "")
                        st.session_state.setting = elements.get('setting', "")
                        st.session_state.narrative_technique = elements.get('narrative_technique', "")
                        # Generar tabla de capítulos
                        table_of_chapters = generate_table_of_chapters(title, genre, audience, st.session_state.total_chapters)
                        if table_of_chapters:
                            st.session_state.title = title
                            st.session_state.genre = genre
                            st.session_state.audience = audience
                            st.session_state.table_of_chapters = table_of_chapters
                            st.session_state.markdown_content = f"# {title}\n\n**Género:** {genre}\n**Audiencia:** {audience}\n\n## Trama\n\n{st.session_state.plot}\n\n## Personajes\n\n{st.session_state.characters}\n\n## Ambientación\n\n{st.session_state.setting}\n\n## Técnica Narrativa\n\n{st.session_state.narrative_technique}\n\n## Tabla de Contenidos\n\n"
                            for chap in table_of_chapters:
                                st.session_state.markdown_content += f"Capítulo {chap['number']}. {chap['title']}\n"
                            st.session_state.markdown_content += "\n"
                            # Inicializar la lista de capítulos sin contenido
                            st.session_state.chapters = [{"number": chap['number'], "title": chap['title'], "scenes": []} for chap in table_of_chapters]
                            st.success("Novela generada exitosamente. Puedes comenzar a generar escenas.")
                            st.subheader("Trama")
                            st.write(st.session_state.plot)
                            st.subheader("Personajes")
                            st.write(st.session_state.characters)
                            st.subheader("Ambientación")
                            st.write(st.session_state.setting)
                            st.subheader("Técnica Narrativa")
                            st.write(st.session_state.narrative_technique)
                            st.subheader("Tabla de Contenidos")
                            st.write("1. " + "\n2. ".join([chap['title'] for chap in table_of_chapters]))
                        else:
                            st.error("No se pudo generar la tabla de contenidos.")
                    else:
                        st.error("No se pudieron generar los elementos iniciales de la novela.")
else:
    st.info("La novela ya ha sido generada. Si deseas generar una nueva, reinicia la generación.")

# Permitir edición de la información inicial si ya se ha generado
if st.session_state.title and st.session_state.plot and st.session_state.characters and st.session_state.setting and st.session_state.narrative_technique and st.session_state.table_of_chapters:
    st.markdown("---")
    st.header("Editar Información Inicial")
    
    with st.form("edit_initial_info"):
        # Editar Título
        edited_title = st.text_input("Título de la Novela:", st.session_state.title)
        
        # Editar Género
        edited_genre = st.selectbox("Género:", ["Misterio", "Romance", "Ciencia Ficción", "Fantasía", "Terror", "Aventura", "Drama", "Comedia", "Histórica"], index=["Misterio", "Romance", "Ciencia Ficción", "Fantasía", "Terror", "Aventura", "Drama", "Comedia", "Histórica"].index(st.session_state.genre) if st.session_state.genre in ["Misterio", "Romance", "Ciencia Ficción", "Fantasía", "Terror", "Aventura", "Drama", "Comedia", "Histórica"] else 0)
        
        # Editar Audiencia
        edited_audience = st.selectbox("Audiencia:", ["Adolescentes", "Jóvenes Adultos", "Adultos", "Niños"], index=["Adolescentes", "Jóvenes Adultos", "Adultos", "Niños"].index(st.session_state.audience) if st.session_state.audience in ["Adolescentes", "Jóvenes Adultos", "Adultos", "Niños"] else 0)
        
        # Editar Trama
        edited_plot = st.text_area("Trama:", st.session_state.plot, height=200)
        
        # Editar Personajes
        edited_characters = st.text_area("Personajes:", st.session_state.characters, height=200)
        
        # Editar Ambientación
        edited_setting = st.text_area("Ambientación:", st.session_state.setting, height=200)
        
        # Editar Técnica Narrativa
        edited_narrative = st.text_area("Técnica Narrativa:", st.session_state.narrative_technique, height=200)
        
        # Editar Tabla de Contenidos
        st.subheader("Tabla de Contenidos")
        edited_table = []
        for chap in st.session_state.chapters:
            edited_title_chap = st.text_input(f"Capítulo {chap['number']}:", chap['title'], key=f"chap_{chap['number']}")
            edited_table.append({"number": chap['number'], "title": edited_title_chap, "scenes": chap['scenes']})
        
        submit_edit = st.form_submit_button("Guardar Cambios")
        
        if submit_edit:
            st.session_state.title = edited_title
            st.session_state.genre = edited_genre
            st.session_state.audience = edited_audience
            st.session_state.plot = edited_plot
            st.session_state.characters = edited_characters
            st.session_state.setting = edited_setting
            st.session_state.narrative_technique = edited_narrative
            st.session_state.table_of_chapters = edited_table
            st.session_state.chapters = edited_table
            # Reconstruir el contenido Markdown
            st.session_state.markdown_content = f"# {st.session_state.title}\n\n**Género:** {st.session_state.genre}\n**Audiencia:** {st.session_state.audience}\n\n## Trama\n\n{st.session_state.plot}\n\n## Personajes\n\n{st.session_state.characters}\n\n## Ambientación\n\n{st.session_state.setting}\n\n## Técnica Narrativa\n\n{st.session_state.narrative_technique}\n\n## Tabla de Contenidos\n\n"
            for chap in st.session_state.table_of_chapters:
                st.session_state.markdown_content += f"Capítulo {chap['number']}. {chap['title']}\n"
            st.session_state.markdown_content += "\n"
            st.success("Información inicial actualizada exitosamente.")

# Mostrar la sección para generar capítulos y escenas solo si la información inicial ha sido generada
if st.session_state.title and st.session_state.plot and st.session_state.characters and st.session_state.setting and st.session_state.narrative_technique and st.session_state.table_of_chapters:
    st.markdown("---")
    st.header("Generación de Capítulos y Escenas")

    # Barra de progreso
    generated_scenes = sum([len(chap['scenes']) for chap in st.session_state.chapters if chap['scenes']])
    total_scenes = st.session_state.total_chapters * st.session_state.total_scenes
    progress = generated_scenes / total_scenes
    progress_bar = st.progress(progress)

    # Botón para regenerar la escena seleccionada
    if st.session_state.selected_chapter is not None and st.session_state.selected_scene is not None:
        with st.container():
            chapter = st.session_state.chapters[st.session_state.selected_chapter]
            scene = chapter['scenes'][st.session_state.selected_scene]
            if scene['title']:
                st.subheader(f"Capítulo {chapter['number']}: {chapter['title']}")
                st.markdown(f"### Escena {scene['number']}: {scene['title']}")
            else:
                st.subheader(f"Capítulo {chapter['number']}: {chapter['title']}")
                st.markdown(f"### Escena {scene['number']}")
            if scene['content']:
                # Mostrar contenido de la escena con párrafos
                st.markdown(scene['content'])
            else:
                st.info("Esta escena aún no ha sido generada.")
            if st.button("Regenerar Escena"):
                with st.spinner(f"Regenerando Escena {scene['number']} del Capítulo {chapter['number']}..."):
                    scene_num = scene['number']
                    # Generar un nuevo título para la escena
                    new_title = generate_scene_title(st.session_state.title, st.session_state.genre, st.session_state.audience, chapter['number'], scene_num)
                    if not new_title:
                        st.error(f"No se pudo generar el título para la escena {scene_num} del capítulo {chapter['number']}.")
                    else:
                        # Generar contenido para la escena
                        new_content = generate_scene_content(st.session_state.title, st.session_state.genre, st.session_state.audience, chapter['number'], scene_num, new_title)
                        if new_content:
                            # Validar que la escena tenga exactamente 9 párrafos
                            validated_content = validate_scene_paragraphs(new_content, st.session_state.title, st.session_state.genre, st.session_state.audience, chapter['number'], scene_num, new_title, expected_paragraphs=st.session_state.total_paragraphs)
                            
                            # Actualizar la escena con el nuevo título y contenido
                            st.session_state.chapters[st.session_state.selected_chapter]['scenes'][st.session_state.selected_scene]['title'] = new_title
                            st.session_state.chapters[st.session_state.selected_chapter]['scenes'][st.session_state.selected_scene]['content'] = validated_content
                            
                            # Actualizar el contenido Markdown
                            # Primero, eliminar el contenido anterior de la escena en markdown_content
                            scene_heading_old = f"### Escena {scene_num}: {scene['title']}\n\n"
                            scene_content_old = scene['content']
                            
                            scene_heading_new = f"### Escena {scene_num}: {new_title}\n\n"
                            scene_content_new = validated_content + "\n\n"
                            
                            # Reemplazar en markdown_content
                            st.session_state.markdown_content = st.session_state.markdown_content.replace(
                                scene_heading_old + scene_content_old,
                                scene_heading_new + scene_content_new
                            )
                            
                            st.success(f"Escena {scene_num} del Capítulo {chapter['number']} regenerada exitosamente.")
                            # No se actualiza la barra de progreso aquí ya que la escena ya existía
                    # Pausa de 3 segundos
                    time.sleep(3)

    # Botón para generar la siguiente escena
    if st.session_state.current_chapter <= st.session_state.total_chapters and st.session_state.current_scene <= st.session_state.total_scenes:
        if st.button("Generar Siguiente Escena"):
            with st.spinner(f"Generando Escena {st.session_state.current_scene} del Capítulo {st.session_state.current_chapter}..."):
                chapter = st.session_state.chapters[st.session_state.current_chapter - 1]
                scene_num = st.session_state.current_scene
                # Generar título para la escena
                generated_title = generate_scene_title(st.session_state.title, st.session_state.genre, st.session_state.audience, st.session_state.current_chapter, scene_num)
                if not generated_title:
                    st.error(f"No se pudo generar el título para la escena {scene_num} del capítulo {st.session_state.current_chapter}.")
                else:
                    # Generar contenido para la escena
                    generated_content = generate_scene_content(st.session_state.title, st.session_state.genre, st.session_state.audience, st.session_state.current_chapter, scene_num, generated_title)
                    if generated_content:
                        # Validar que la escena tenga exactamente 9 párrafos
                        validated_content = validate_scene_paragraphs(generated_content, st.session_state.title, st.session_state.genre, st.session_state.audience, st.session_state.current_chapter, scene_num, generated_title, expected_paragraphs=st.session_state.total_paragraphs)
                        
                        # Actualizar la escena con título y contenido
                        chapter['scenes'].append({
                            "number": scene_num,
                            "title": generated_title,
                            "content": validated_content
                        })
                        
                        # Agregar al contenido Markdown
                        update_markdown_content(st.session_state.current_chapter, chapter['title'], scene_num, generated_title, validated_content)
                        
                        st.success(f"Escena {scene_num} del Capítulo {st.session_state.current_chapter} generada exitosamente.")
                        st.session_state.current_scene += 1
                        
                        # Actualizar la barra de progreso
                        generated_scenes += 1
                        progress = generated_scenes / total_scenes
                        progress_bar.progress(progress)
                        
                        # Pausa de 3 segundos entre escenas
                        time.sleep(3)
                    else:
                        st.error(f"No se pudo generar el contenido para la escena {scene_num} del capítulo {st.session_state.current_chapter}.")

    # Botón para generar el siguiente capítulo
    if st.session_state.current_chapter <= st.session_state.total_chapters and st.session_state.current_scene > st.session_state.total_scenes:
        if st.button("Generar Siguiente Capítulo"):
            with st.spinner(f"Generando Capítulo {st.session_state.current_chapter}..."):
                # Generar título para el capítulo si no se ha generado
                chapter = st.session_state.chapters[st.session_state.current_chapter - 1]
                if not chapter['title']:
                    generated_title = generate_scene_title(st.session_state.title, st.session_state.genre, st.session_state.audience, st.session_state.current_chapter, 0)  # Usando escena_num=0 para generar capítulo sin escena
                    # Alternativamente, podrías crear una función específica para generar títulos de capítulos
                    # Por simplicidad, reutilizamos la función de escena
                    if not generated_title:
                        st.error(f"No se pudo generar el título para el capítulo {st.session_state.current_chapter}.")
                        return
                    else:
                        chapter['title'] = generated_title
                        # Actualizar el contenido Markdown para el capítulo
                        chapter_heading = f"## Capítulo {st.session_state.current_chapter}: {generated_title}\n\n"
                        st.session_state.markdown_content += f"{chapter_heading}"
                        st.success(f"Capítulo {st.session_state.current_chapter} generado exitosamente. Ahora puedes comenzar a generar sus escenas.")
                else:
                    st.info(f"El capítulo {st.session_state.current_chapter} ya tiene un título.")
                st.session_state.current_chapter += 1
                st.session_state.current_scene = 1  # Reiniciar la escena para el nuevo capítulo

    # Actualizar la barra de progreso hasta completar
    if len([chap for chap in st.session_state.chapters if len(chap['scenes']) == st.session_state.total_scenes]) == st.session_state.total_chapters:
        st.session_state.generation_complete = True

    # Botones para exportar a Word
    if st.session_state.chapters:
        with st.spinner("Preparando la exportación..."):
            # Exportar contenido parcial
            partial_markdown = st.session_state.markdown_content
            partial_word_file = export_to_word(partial_markdown, st.session_state.plot, st.session_state.characters, st.session_state.setting, st.session_state.narrative_technique, st.session_state.table_of_chapters)
            
            # Exportar contenido completo
            if st.session_state.generation_complete:
                complete_markdown = st.session_state.markdown_content
                # Agregar referencias al final si se han generado (puedes omitir esta parte si no es necesario)
                # complete_markdown += "\n## Referencias\n\n"  # Opcional
                complete_word_file = export_to_word(complete_markdown, st.session_state.plot, st.session_state.characters, st.session_state.setting, st.session_state.narrative_technique, st.session_state.table_of_chapters)
                st.success("Preparado para descargar la novela completa.")
            else:
                complete_word_file = None

            # Botón para descargar contenido parcial en Word
            st.download_button(
                label="Descargar Contenido Parcial en Word",
                data=partial_word_file,
                file_name=f"{st.session_state.title.replace(' ', '_')}_Parcial.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            
            # Botón para descargar contenido completo en Word (solo si está completo)
            if st.session_state.generation_complete:
                st.download_button(
                    label="Descargar Novela Completa en Word",
                    data=complete_word_file,
                    file_name=f"{st.session_state.title.replace(' ', '_')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

    # Opcional: Mostrar todo el contenido generado
    with st.expander("Mostrar Contenido Completo"):
        st.markdown(st.session_state.markdown_content)
