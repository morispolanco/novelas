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
if 'chapters' not in st.session_state:
    st.session_state.chapters = []  # Lista de diccionarios: [{'number': 1, 'title': 'Título', 'scenes': [{'number':1, 'content':'Contenido'}]}, ...]
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
    st.session_state.chapters = []
    st.session_state.current_chapter = 1
    st.session_state.current_scene = 1
    st.session_state.markdown_content = ""
    st.session_state.generation_complete = False
    st.session_state.selected_chapter = None
    st.session_state.selected_scene = None

# Función para llamar a la API de OpenRouter con reintentos
def call_openrouter_api(prompt, model="qwen/qwen-2.5-72b-instruct", max_tokens=1500, temperature=0.7, retries=3, delay_seconds=2):
    try:
        api_key = st.secrets["OPENROUTER_API_KEY"]
    except KeyError:
        st.error("La clave de API de OpenRouter no está configurada. Por favor, verifica tus secretos.")
        return None

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    for attempt in range(retries):
        try:
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content'].strip()
        except requests.exceptions.HTTPError as err:
            st.error(f"Error en la API: {err}")
        except Exception as e:
            st.error(f"Error inesperado: {e}")
        if attempt < retries - 1:
            st.warning(f"Reintentando en {delay_seconds} segundos...")
            time.sleep(delay_seconds)
    st.error("No se pudo obtener una respuesta válida de la API después de varios intentos.")
    return None

# Función para generar elementos iniciales de la novela
def generate_initial_elements(title, genre, audience):
    prompt = f"""Genera una trama, personajes principales, ambientación y técnica narrativa para una novela con el siguiente título, género y audiencia.
    
Título: {title}
Género: {genre}
Audiencia: {audience}

Proporciona la información en el siguiente formato:

Trama:
[Descripción de la trama]

Personajes Principales:
[Descripción de los personajes]

Ambientación:
[Descripción de la ambientación]

Técnica Narrativa:
[Descripción de la técnica narrativa]
"""
    response = call_openrouter_api(prompt)
    if response:
        try:
            trama = re.search(r"Trama:\s*(.*?)\n\n", response, re.DOTALL).group(1).strip()
            personajes = re.search(r"Personajes Principales:\s*(.*?)\n\n", response, re.DOTALL).group(1).strip()
            ambientacion = re.search(r"Ambientación:\s*(.*?)\n\n", response, re.DOTALL).group(1).strip()
            tecnica = re.search(r"Técnica Narrativa:\s*(.*)", response, re.DOTALL).group(1).strip()
            return trama, personajes, ambientacion, tecnica
        except AttributeError:
            st.error("Error al procesar la respuesta de la API. Por favor, intenta nuevamente.")
    return None, None, None, None

# Función para generar la tabla de capítulos
def generate_table_of_chapters(plot, characters, setting, narrative_technique, total_chapters):
    prompt = f"""Basándote en la siguiente información, genera una tabla de contenidos para una novela con {total_chapters} capítulos. Cada capítulo debe tener un título descriptivo.
    
Trama: {plot}
Personajes Principales: {characters}
Ambientación: {setting}
Técnica Narrativa: {narrative_technique}

Formato de respuesta:
Capítulo 1: [Título del Capítulo 1]
Capítulo 2: [Título del Capítulo 2]
...
Capítulo {total_chapters}: [Título del Capítulo {total_chapters}]
"""
    response = call_openrouter_api(prompt)
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

# Función para generar un título de capítulo
def generate_chapter_title(plot, characters, setting, narrative_technique, chapter_num):
    prompt = f"""Basándote en la siguiente información, genera un título descriptivo para el capítulo {chapter_num} de una novela.
    
Trama: {plot}
Personajes Principales: {characters}
Ambientación: {setting}
Técnica Narrativa: {narrative_technique}

Formato de respuesta:
Título del Capítulo {chapter_num}: [Título Único]
"""
    response = call_openrouter_api(prompt)
    if response:
        match = re.search(r"Título del Capítulo \d+:\s*(.*)", response)
        if match:
            return match.group(1).strip()
    return None

# Función para generar una escena
def generate_scene(plot, characters, setting, narrative_technique, chapter_num, scene_num):
    prompt = f"""Escribe una escena para el capítulo {chapter_num} de una novela. La escena debe tener exactamente {st.session_state.total_paragraphs} párrafos. Usa rayas (–) para los diálogos y no incluye títulos para la escena.
    
Trama: {plot}
Personajes Principales: {characters}
Ambientación: {setting}
Técnica Narrativa: {narrative_technique}

Formato de respuesta:
[Párrafo 1]

[Párrafo 2]

...

[Párrafo {st.session_state.total_paragraphs}]
"""
    response = call_openrouter_api(prompt, model="qwen/qwen-2.5-72b-instruct")
    if response:
        # Asegurarse de que los diálogos utilizan rayas
        response = response.replace('"', '–').replace("“", '–').replace("”", '–')
        return response.strip()
    return None

# Función para limpiar el contenido Markdown de subdivisiones (opcional)
def clean_markdown_content(markdown_content):
    # Eliminar líneas que comiencen con #### (o más #)
    cleaned_content = re.sub(r'#{4,} .*', '', markdown_content)
    return cleaned_content

# Función para exportar a Word
def export_to_word(markdown_content):
    # Convertir Markdown a HTML
    html = markdown.markdown(markdown_content)
    
    # Parsear HTML con BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    
    # Crear un documento de Word
    doc = Document()
    
    # Iterar sobre los elementos del HTML y agregarlos al documento
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
        # Ignorar otros elementos
        else:
            if element.name == 'p':
                doc.add_paragraph(element.get_text())
    
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
        try:
            chapter_index = int(selected_chapter.split(" ")[1].replace(":", "")) - 1
            # Verificar que el índice esté dentro del rango
            if 0 <= chapter_index < len(st.session_state.chapters):
                st.session_state.selected_chapter = chapter_index
                chapter = st.session_state.chapters[chapter_index]
                if chapter['scenes']:
                    scene_titles = [f"Escena {sec['number']}" for sec in chapter['scenes']]
                    selected_scene = st.selectbox(
                        "Selecciona una escena para ver:",
                        scene_titles,
                        key="select_scene"
                    )
                    scene_index = int(selected_scene.split(" ")[1]) - 1
                    # Verificar que el índice esté dentro del rango
                    if 0 <= scene_index < len(chapter['scenes']):
                        st.session_state.selected_scene = scene_index
                    else:
                        st.error("Escena seleccionada no válida.")
                else:
                    st.info("No hay escenas generadas aún en este capítulo.")
            else:
                st.error("Capítulo seleccionado no válido.")
        except (IndexError, ValueError):
            st.error("Error al seleccionar el capítulo.")
    else:
        st.info("No hay capítulos generados aún.")

# --- Sección Principal ---

# Entrada de usuario para los detalles de la novela
st.header("Datos de la Novela")
with st.form("novel_details"):
    title = st.text_input("Título de la Novela:", st.session_state.title)
    genre = st.selectbox("Género:", ["Misterio", "Romance", "Ciencia Ficción", "Fantasía", "Thriller", "Drama", "Aventura", "Otro"], index=0)
    audience = st.selectbox("Audiencia:", ["Adolescentes", "Jóvenes Adultos", "Adultos"], index=0)
    submit_details = st.form_submit_button("Guardar Detalles")
    
    if submit_details:
        if not title:
            st.warning("Por favor, ingresa un título para la novela.")
        else:
            st.session_state.title = title
            st.session_state.genre = genre
            st.session_state.audience = audience
            st.success("Detalles de la novela guardados exitosamente.")

# Botón para generar elementos iniciales de la novela
if st.session_state.title and st.session_state.genre and st.session_state.audience and not st.session_state.chapters:
    if st.button("Generar Trama, Personajes, Ambientación y Técnica Narrativa"):
        with st.spinner("Generando elementos iniciales de la novela..."):
            trama, personajes, ambientacion, tecnica = generate_initial_elements(st.session_state.title, st.session_state.genre, st.session_state.audience)
            if trama and personajes and ambientacion and tecnica:
                st.session_state.plot = trama
                st.session_state.characters = personajes
                st.session_state.setting = ambientacion
                st.session_state.narrative_technique = tecnica
                table = generate_table_of_chapters(trama, personajes, ambientacion, tecnica, st.session_state.total_chapters)
                if table:
                    # Inicializar la lista de capítulos
                    st.session_state.chapters = table
                    # Construir el contenido Markdown inicial
                    st.session_state.markdown_content = f"# {st.session_state.title}\n\n"
                    st.session_state.markdown_content += f"**Género:** {st.session_state.genre}\n\n"
                    st.session_state.markdown_content += f"**Audiencia:** {st.session_state.audience}\n\n"
                    st.session_state.markdown_content += f"## Trama\n\n{st.session_state.plot}\n\n"
                    st.session_state.markdown_content += f"## Personajes Principales\n\n{st.session_state.characters}\n\n"
                    st.session_state.markdown_content += f"## Ambientación\n\n{st.session_state.setting}\n\n"
                    st.session_state.markdown_content += f"## Técnica Narrativa\n\n{st.session_state.narrative_technique}\n\n"
                    st.session_state.markdown_content += f"## Tabla de Capítulos\n\n"
                    for chap in table:
                        st.session_state.markdown_content += f"Capítulo {chap['number']}: {chap['title']}\n"
                    st.session_state.markdown_content += "\n"
                    st.success("Elementos iniciales generados exitosamente.")
            else:
                st.error("No se pudieron generar los elementos iniciales. Por favor, intenta nuevamente.")

# Permitir edición de los elementos iniciales si ya se han generado
if st.session_state.chapters:
    st.markdown("---")
    st.header("Editar Elementos Iniciales")
    
    with st.form("edit_initial_elements"):
        trama_edit = st.text_area("Trama:", st.session_state.plot, height=200)
        personajes_edit = st.text_area("Personajes Principales:", st.session_state.characters, height=200)
        ambientacion_edit = st.text_area("Ambientación:", st.session_state.setting, height=200)
        tecnica_edit = st.text_area("Técnica Narrativa:", st.session_state.narrative_technique, height=200)
        submit_edit = st.form_submit_button("Guardar Cambios")
        
        if submit_edit:
            st.session_state.plot = trama_edit
            st.session_state.characters = personajes_edit
            st.session_state.setting = ambientacion_edit
            st.session_state.narrative_technique = tecnica_edit
            # Actualizar el contenido Markdown
            st.session_state.markdown_content = f"# {st.session_state.title}\n\n"
            st.session_state.markdown_content += f"**Género:** {st.session_state.genre}\n\n"
            st.session_state.markdown_content += f"**Audiencia:** {st.session_state.audience}\n\n"
            st.session_state.markdown_content += f"## Trama\n\n{st.session_state.plot}\n\n"
            st.session_state.markdown_content += f"## Personajes Principales\n\n{st.session_state.characters}\n\n"
            st.session_state.markdown_content += f"## Ambientación\n\n{st.session_state.setting}\n\n"
            st.session_state.markdown_content += f"## Técnica Narrativa\n\n{st.session_state.narrative_technique}\n\n"
            st.session_state.markdown_content += f"## Tabla de Capítulos\n\n"
            for chap in st.session_state.chapters:
                st.session_state.markdown_content += f"Capítulo {chap['number']}: {chap['title']}\n"
            st.session_state.markdown_content += "\n"
            st.success("Elementos iniciales actualizados exitosamente.")

# Mostrar la sección para generar capítulos y escenas solo si los elementos iniciales han sido generados
if st.session_state.chapters:
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
            if scene['content']:
                st.subheader(f"Capítulo {chapter['number']}: {chapter['title']}")
                st.markdown(f"**Escena {scene['number']}**")
                st.markdown(scene['content'])
            else:
                st.info("Esta escena aún no ha sido generada.")
            if st.button("Regenerar Escena"):
                with st.spinner(f"Regenerando Escena {scene['number']} del Capítulo {chapter['number']}..."):
                    # Generar contenido para la escena
                    new_content = generate_scene(
                        st.session_state.plot,
                        st.session_state.characters,
                        st.session_state.setting,
                        st.session_state.narrative_technique,
                        chapter_num=chapter['number'],
                        scene_num=scene['number']
                    )
                    if new_content:
                        # Actualizar la escena con el nuevo contenido
                        st.session_state.chapters[st.session_state.selected_chapter]['scenes'][st.session_state.selected_scene]['content'] = new_content
                        
                        # Actualizar el contenido Markdown
                        # Encontrar y reemplazar la escena en markdown_content
                        # Asumiendo que las escenas no tienen títulos, solo se indican como "Escena X"
                        pattern = re.compile(rf"Escena {scene['number']}\s*\n\n(.*?)\n\n", re.DOTALL)
                        replacement = f"Escena {scene['number']}\n\n{new_content}\n\n"
                        st.session_state.markdown_content = pattern.sub(replacement, st.session_state.markdown_content)
                        
                        st.success(f"Escena {scene['number']} del Capítulo {chapter['number']} regenerada exitosamente.")

    # Botón para generar la siguiente escena
    if st.session_state.current_chapter <= st.session_state.total_chapters and st.session_state.current_scene <= st.session_state.total_scenes:
        if st.button("Generar Siguiente Escena"):
            with st.spinner(f"Generando Escena {st.session_state.current_scene} del Capítulo {st.session_state.current_chapter}..."):
                chapter = st.session_state.chapters[st.session_state.current_chapter - 1]
                scene_num = st.session_state.current_scene
                # Generar contenido para la escena
                generated_content = generate_scene(
                    st.session_state.plot,
                    st.session_state.characters,
                    st.session_state.setting,
                    st.session_state.narrative_technique,
                    chapter_num=st.session_state.current_chapter,
                    scene_num=scene_num
                )
                if generated_content:
                    # Actualizar la escena con contenido
                    chapter['scenes'].append({
                        "number": scene_num,
                        "content": generated_content
                    })
                    
                    # Agregar al contenido Markdown
                    scene_heading = f"Escena {scene_num}\n\n"
                    scene_content = generated_content + "\n\n"
                    st.session_state.markdown_content += f"{scene_heading}{scene_content}"
                    
                    st.success(f"Escena {scene_num} del Capítulo {st.session_state.current_chapter} generada exitosamente.")
                    st.session_state.current_scene += 1
                    
                    # Actualizar la barra de progreso
                    generated_scenes += 1
                    progress = generated_scenes / total_scenes
                    progress_bar.progress(progress)
                    
                    # Pausa de 1 segundo entre escenas para mejorar la experiencia del usuario
                    time.sleep(1)
                else:
                    st.error(f"No se pudo generar el contenido para la escena {scene_num} del capítulo {st.session_state.current_chapter}.")

    # Botón para generar el siguiente capítulo
    if st.session_state.current_chapter <= st.session_state.total_chapters and st.session_state.current_scene > st.session_state.total_scenes:
        if st.button("Generar Siguiente Capítulo"):
            with st.spinner(f"Generando Capítulo {st.session_state.current_chapter}..."):
                # Generar título para el capítulo
                generated_title = generate_chapter_title(
                    st.session_state.plot,
                    st.session_state.characters,
                    st.session_state.setting,
                    st.session_state.narrative_technique,
                    chapter_num=st.session_state.current_chapter
                )
                if not generated_title:
                    st.error(f"No se pudo generar el título para el capítulo {st.session_state.current_chapter}.")
                else:
                    # Actualizar el título del capítulo
                    st.session_state.chapters[st.session_state.current_chapter - 1]['title'] = generated_title
                    # Actualizar el contenido Markdown para el capítulo
                    chapter_heading = f"## Capítulo {st.session_state.current_chapter}: {generated_title}\n\n"
                    st.session_state.markdown_content += f"{chapter_heading}"
                    
                    st.success(f"Capítulo {st.session_state.current_chapter} generado exitosamente. Ahora puedes comenzar a generar sus escenas.")
                    st.session_state.current_chapter += 1
                    st.session_state.current_scene = 1  # Reiniciar la escena para el nuevo capítulo

    # Actualizar la barra de progreso hasta completar
    if len([chap for chap in st.session_state.chapters if len(chap['scenes']) == st.session_state.total_scenes]) == st.session_state.total_chapters:
        st.session_state.generation_complete = True

    # Botones para exportar a Word
    if st.session_state.chapters:
        with st.spinner("Preparando la exportación..."):
            # Exportar contenido parcial
            partial_markdown = f"# {st.session_state.title}\n\n"
            partial_markdown += f"**Género:** {st.session_state.genre}\n\n"
            partial_markdown += f"**Audiencia:** {st.session_state.audience}\n\n"
            partial_markdown += f"## Trama\n\n{st.session_state.plot}\n\n"
            partial_markdown += f"## Personajes Principales\n\n{st.session_state.characters}\n\n"
            partial_markdown += f"## Ambientación\n\n{st.session_state.setting}\n\n"
            partial_markdown += f"## Técnica Narrativa\n\n{st.session_state.narrative_technique}\n\n"
            partial_markdown += f"## Tabla de Capítulos\n\n"
            for chap in st.session_state.chapters:
                partial_markdown += f"Capítulo {chap['number']}: {chap['title']}\n"
            partial_markdown += "\n"
            for chap in st.session_state.chapters:
                if chap['scenes']:
                    partial_markdown += f"## Capítulo {chap['number']}: {chap['title']}\n\n"
                    for sec in chap['scenes']:
                        partial_markdown += f"Escena {sec['number']}\n\n{sec['content']}\n\n"
                else:
                    break  # Solo incluir capítulos generados hasta el momento
            # Limpiar el contenido de subdivisiones (opcional)
            partial_markdown = clean_markdown_content(partial_markdown)
            partial_word_file = export_to_word(partial_markdown)
            
            # Exportar contenido completo
            if st.session_state.generation_complete:
                complete_markdown = st.session_state.markdown_content
                # Limpiar el contenido de subdivisiones (opcional)
                complete_markdown = clean_markdown_content(complete_markdown)
                complete_word_file = export_to_word(complete_markdown)
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
