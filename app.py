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
def call_openrouter_api(messages, model="openai/gpt-4o-mini", retries=3, delay_seconds=2):
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
            st.warning(f"Reintentando en {delay_seconds} segundos...")
            time.sleep(delay_seconds)
    st.error("No se pudo obtener una respuesta válida de la API después de varios intentos.")
    return None

# Funciones para generar elementos de la novela
def generate_title_genre_audience(title, genre, audience):
    return title, genre, audience

def generate_plot(title, genre, audience):
    prompt = f"""Genera una trama para una novela basada en los siguientes datos:
    
    Título: {title}
    Género: {genre}
    Audiencia: {audience}
    
    La trama debe ser envolvente, coherente y adecuada para la audiencia especificada.
    
    Formato de respuesta:
    Trama: [Descripción de la trama]
    """
    messages = [{"role": "user", "content": prompt}]
    response = call_openrouter_api(messages)
    if response:
        match = re.search(r'Trama:\s*(.*)', response, re.DOTALL)
        if match:
            return match.group(1).strip()
    return ""

def generate_characters(title, genre, audience, plot):
    prompt = f"""Basándote en la siguiente trama, genera una lista de personajes principales para una novela:
    
    Título: {title}
    Género: {genre}
    Audiencia: {audience}
    Trama: {plot}
    
    Cada personaje debe tener un nombre, una breve descripción y su papel en la historia.
    
    Formato de respuesta:
    Personaje 1: [Descripción]
    Personaje 2: [Descripción]
    ...
    """
    messages = [{"role": "user", "content": prompt}]
    response = call_openrouter_api(messages)
    if response:
        return response.strip()
    return ""

def generate_setting(title, genre, audience, plot):
    prompt = f"""Describe la ambientación de una novela basada en los siguientes datos:
    
    Título: {title}
    Género: {genre}
    Audiencia: {audience}
    Trama: {plot}
    
    La ambientación debe ser detallada y coherente con el género y la trama.
    
    Formato de respuesta:
    Ambientación: [Descripción detallada]
    """
    messages = [{"role": "user", "content": prompt}]
    response = call_openrouter_api(messages)
    if response:
        match = re.search(r'Ambientación:\s*(.*)', response, re.DOTALL)
        if match:
            return match.group(1).strip()
    return ""

def generate_narrative_technique(title, genre, audience, plot):
    prompt = f"""Define la técnica narrativa adecuada para una novela con los siguientes datos:
    
    Título: {title}
    Género: {genre}
    Audiencia: {audience}
    Trama: {plot}
    
    La técnica narrativa debe complementar la trama y el género.
    
    Formato de respuesta:
    Técnica Narrativa: [Descripción]
    """
    messages = [{"role": "user", "content": prompt}]
    response = call_openrouter_api(messages)
    if response:
        match = re.search(r'Técnica Narrativa:\s*(.*)', response, re.DOTALL)
        if match:
            return match.group(1).strip()
    return ""

def generate_table_of_chapters(title, genre, audience, plot, characters, setting, narrative_technique, total_chapters):
    prompt = f"""Genera una tabla de contenidos con {total_chapters} capítulos para una novela basada en los siguientes datos:
    
    Título: {title}
    Género: {genre}
    Audiencia: {audience}
    Trama: {plot}
    Personajes: {characters}
    Ambientación: {setting}
    Técnica Narrativa: {narrative_technique}
    
    Cada capítulo debe tener un título que refleje su contenido.
    
    Formato de respuesta:
    Capítulo 1: [Título del Capítulo 1]
    Capítulo 2: [Título del Capítulo 2]
    ...
    Capítulo {total_chapters}: [Título del Capítulo {total_chapters}]
    """
    messages = [{"role": "user", "content": prompt}]
    response = call_openrouter_api(messages)
    table = []
    if response:
        for line in response.split('\n'):
            match = re.match(r'Capítulo\s+(\d+):\s+(.*)', line)
            if match:
                chap_num = int(match.group(1))
                chap_title = match.group(2).strip()
                table.append({"number": chap_num, "title": chap_title, "scenes": []})
    return table

def generate_chapter_title(title, genre, audience, plot, characters, setting, narrative_technique, chapter_num):
    prompt = f"""Genera un título para el capítulo {chapter_num} de una novela con los siguientes datos:
    
    Título de la Novela: {title}
    Género: {genre}
    Audiencia: {audience}
    Trama: {plot}
    Personajes: {characters}
    Ambientación: {setting}
    Técnica Narrativa: {narrative_technique}
    
    Formato de respuesta:
    Título del Capítulo {chapter_num}: [Título Único]
    """
    messages = [{"role": "user", "content": prompt}]
    response = call_openrouter_api(messages)
    if response:
        match = re.match(r'Título del Capítulo\s+\d+:\s+(.*)', response)
        if match:
            return match.group(1).strip()
    return f"Capítulo {chapter_num}"

def generate_scene_title(title, genre, audience, plot, characters, setting, narrative_technique, chapter_num, scene_num):
    prompt = f"""Genera un título para la escena {scene_num} del capítulo {chapter_num} de una novela con los siguientes datos:
    
    Título de la Novela: {title}
    Género: {genre}
    Audiencia: {audience}
    Trama: {plot}
    Personajes: {characters}
    Ambientación: {setting}
    Técnica Narrativa: {narrative_technique}
    
    Formato de respuesta:
    Título de la Escena {scene_num}: [Título Único]
    """
    messages = [{"role": "user", "content": prompt}]
    response = call_openrouter_api(messages)
    if response:
        match = re.match(r'Título de la Escena\s+\d+:\s+(.*)', response)
        if match:
            return match.group(1).strip()
    return f"Escena {scene_num}"

def generate_scene_content(title, genre, audience, plot, characters, setting, narrative_technique, chapter_num, scene_num, scene_title):
    prompt = f"""Escribe el contenido de la escena {scene_num} del capítulo {chapter_num} para una novela con los siguientes datos:
    
    Título de la Novela: {title}
    Género: {genre}
    Audiencia: {audience}
    Trama: {plot}
    Personajes: {characters}
    Ambientación: {setting}
    Técnica Narrativa: {narrative_technique}
    
    La escena debe tener un título: {scene_title}
    Debe estar estructurada de manera clara y envolvente, con exactamente 9 párrafos.
    
    Formato de respuesta:
    ### Escena {scene_num}: {scene_title}
    Párrafo 1.
    Párrafo 2.
    ...
    Párrafo 9.
    """
    messages = [{"role": "user", "content": prompt}]
    response = call_openrouter_api(messages)
    return response

def validate_scene_content(scene_content, expected_paragraphs=9):
    paragraphs = [p for p in scene_content.split('\n\n') if p.strip() != "" and not p.startswith("### Escena")]
    num_paragraphs = len(paragraphs)
    if num_paragraphs < expected_paragraphs:
        paragraphs_needed = expected_paragraphs - num_paragraphs
        additional_paragraphs = ""
        for _ in range(paragraphs_needed):
            prompt = f"""Agrega un párrafo adicional para la escena. El párrafo debe ser relevante y coherente con el contenido existente.
    
    Contenido actual de la escena:
    {scene_content}
    
    Nuevo párrafo:"""
            messages = [{"role": "user", "content": prompt}]
            new_paragraph = call_openrouter_api(messages)
            if new_paragraph:
                additional_paragraphs += f"{new_paragraph}\n\n"
            else:
                break
        paragraphs += [p.strip() for p in additional_paragraphs.strip().split('\n\n') if p.strip() != ""]
    elif num_paragraphs > expected_paragraphs:
        paragraphs = paragraphs[:expected_paragraphs]
    validated_content = "### Escena {}: {}\n\n".format(
        re.search(r'### Escena \d+: (.*)', scene_content).group(1) if re.search(r'### Escena \d+: (.*)', scene_content) else "Escena",
        re.search(r'### Escena \d+: (.*)', scene_content).group(1) if re.search(r'### Escena \d+: (.*)', scene_content) else "Escena"
    ) + "\n\n".join(paragraphs)
    return validated_content

def clean_markdown_content(markdown_content):
    # Eliminar líneas que comiencen con #### (o más #)
    cleaned_content = re.sub(r'#{4,} .*', '', markdown_content)
    return cleaned_content

def export_to_word(markdown_content, title):
    # Convertir Markdown a HTML
    html = markdown.markdown(markdown_content)
    
    # Parsear HTML con BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    
    # Crear un documento de Word
    doc = Document()
    
    # Iterar sobre los elementos del HTML y agregarlos al documento
    for element in soup.descendants:
        if isinstance(element, str):
            continue
        if element.name == 'h1':
            doc.add_heading(element.get_text(), level=1)
        elif element.name == 'h2':
            doc.add_heading(element.get_text(), level=2)
        elif element.name == 'h3':
            doc.add_heading(element.get_text(), level=3)
        elif element.name == 'p':
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

# Entrada de usuario para el título, género y audiencia
st.header("Información de la Novela")
with st.form("novel_info"):
    title = st.text_input("Título de la Novela:", st.session_state.title)
    genre = st.selectbox("Género:", ["Misterio", "Romance", "Ciencia Ficción", "Fantasía", "Terror", "Aventura", "Drama", "Thriller", "Otros"], index=0)
    audience = st.selectbox("Audiencia:", ["Adolescentes", "Jóvenes Adultos", "Adultos"], index=1)
    submit_info = st.form_submit_button("Guardar Información")
    
    if submit_info:
        st.session_state.title, st.session_state.genre, st.session_state.audience = generate_title_genre_audience(title, genre, audience)
        st.success("Información de la novela guardada exitosamente.")

# Botón para generar trama, personajes, ambientación, técnica narrativa y tabla de capítulos
if st.session_state.title and st.session_state.genre and st.session_state.audience and not st.session_state.plot:
    if st.button("Generar Elementos de la Novela"):
        with st.spinner("Generando trama, personajes, ambientación y técnica narrativa..."):
            st.session_state.plot = generate_plot(st.session_state.title, st.session_state.genre, st.session_state.audience)
            st.session_state.characters = generate_characters(st.session_state.title, st.session_state.genre, st.session_state.audience, st.session_state.plot)
            st.session_state.setting = generate_setting(st.session_state.title, st.session_state.genre, st.session_state.audience, st.session_state.plot)
            st.session_state.narrative_technique = generate_narrative_technique(st.session_state.title, st.session_state.genre, st.session_state.audience, st.session_state.plot)
            st.session_state.table_of_chapters = generate_table_of_chapters(
                st.session_state.title,
                st.session_state.genre,
                st.session_state.audience,
                st.session_state.plot,
                st.session_state.characters,
                st.session_state.setting,
                st.session_state.narrative_technique,
                st.session_state.total_chapters
            )
            # Construir el contenido Markdown inicial
            st.session_state.markdown_content = f"# {st.session_state.title}\n\n**Género:** {st.session_state.genre}\n\n**Audiencia:** {st.session_state.audience}\n\n**Trama:** {st.session_state.plot}\n\n**Personajes:**\n{st.session_state.characters}\n\n**Ambientación:** {st.session_state.setting}\n\n**Técnica Narrativa:** {st.session_state.narrative_technique}\n\n## Tabla de Capítulos\n\n"
            for chap in st.session_state.table_of_chapters:
                st.session_state.markdown_content += f"Capítulo {chap['number']}: {chap['title']}\n"
            st.session_state.markdown_content += "\n"
            # Inicializar la lista de capítulos sin contenido
            st.session_state.chapters = [{"number": chap['number'], "title": chap['title'], "scenes": []} for chap in st.session_state.table_of_chapters]
            st.success("Elementos de la novela generados exitosamente.")
            st.subheader("Trama")
            st.write(st.session_state.plot)
            st.subheader("Personajes")
            st.write(st.session_state.characters)
            st.subheader("Ambientación")
            st.write(st.session_state.setting)
            st.subheader("Técnica Narrativa")
            st.write(st.session_state.narrative_technique)
            st.subheader("Tabla de Capítulos")
            for chap in st.session_state.table_of_chapters:
                st.write(f"Capítulo {chap['number']}: {chap['title']}")

# Permitir edición de la información inicial si ya se ha generado
if st.session_state.title and st.session_state.genre and st.session_state.audience and st.session_state.plot:
    st.markdown("---")
    st.header("Editar Información de la Novela")
    
    with st.form("edit_novel_info"):
        edited_title = st.text_input("Título de la Novela:", st.session_state.title)
        edited_genre = st.selectbox("Género:", ["Misterio", "Romance", "Ciencia Ficción", "Fantasía", "Terror", "Aventura", "Drama", "Thriller", "Otros"], index=["Misterio", "Romance", "Ciencia Ficción", "Fantasía", "Terror", "Aventura", "Drama", "Thriller", "Otros"].index(st.session_state.genre) if st.session_state.genre in ["Misterio", "Romance", "Ciencia Ficción", "Fantasía", "Terror", "Aventura", "Drama", "Thriller", "Otros"] else 0)
        edited_audience = st.selectbox("Audiencia:", ["Adolescentes", "Jóvenes Adultos", "Adultos"], index=["Adolescentes", "Jóvenes Adultos", "Adultos"].index(st.session_state.audience) if st.session_state.audience in ["Adolescentes", "Jóvenes Adultos", "Adultos"] else 1)
        edited_plot = st.text_area("Trama:", st.session_state.plot, height=200)
        edited_characters = st.text_area("Personajes:", st.session_state.characters, height=200)
        edited_setting = st.text_area("Ambientación:", st.session_state.setting, height=200)
        edited_narrative_technique = st.text_area("Técnica Narrativa:", st.session_state.narrative_technique, height=200)
        
        submit_edit = st.form_submit_button("Guardar Cambios")
        
        if submit_edit:
            st.session_state.title, st.session_state.genre, st.session_state.audience = generate_title_genre_audience(edited_title, edited_genre, edited_audience)
            st.session_state.plot = edited_plot
            st.session_state.characters = edited_characters
            st.session_state.setting = edited_setting
            st.session_state.narrative_technique = edited_narrative_technique
            # Reconstruir el contenido Markdown
            st.session_state.markdown_content = f"# {st.session_state.title}\n\n**Género:** {st.session_state.genre}\n\n**Audiencia:** {st.session_state.audience}\n\n**Trama:** {st.session_state.plot}\n\n**Personajes:**\n{st.session_state.characters}\n\n**Ambientación:** {st.session_state.setting}\n\n**Técnica Narrativa:** {st.session_state.narrative_technique}\n\n## Tabla de Capítulos\n\n"
            for chap in st.session_state.table_of_chapters:
                st.session_state.markdown_content += f"Capítulo {chap['number']}: {chap['title']}\n"
            st.session_state.markdown_content += "\n"
            st.success("Información de la novela actualizada exitosamente.")

# Mostrar la sección para generar capítulos y escenas solo si todos los elementos han sido generados
if st.session_state.title and st.session_state.genre and st.session_state.audience and st.session_state.plot and st.session_state.characters and st.session_state.setting and st.session_state.narrative_technique and st.session_state.table_of_chapters:
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
                st.markdown(scene['content'])
            else:
                st.info("Esta escena aún no ha sido generada.")
            if st.button("Regenerar Escena"):
                with st.spinner(f"Regenerando Escena {scene['number']} del Capítulo {chapter['number']}..."):
                    scene_num = scene['number']
                    # Generar un nuevo título para la escena
                    new_title = generate_scene_title(
                        st.session_state.title,
                        st.session_state.genre,
                        st.session_state.audience,
                        st.session_state.plot,
                        st.session_state.characters,
                        st.session_state.setting,
                        st.session_state.narrative_technique,
                        chapter_num=chapter['number'],
                        scene_num=scene_num
                    )
                    if not new_title:
                        st.error(f"No se pudo generar el título para la escena {scene_num} del capítulo {chapter['number']}.")
                    else:
                        # Generar contenido para la escena
                        new_content = generate_scene_content(
                            st.session_state.title,
                            st.session_state.genre,
                            st.session_state.audience,
                            st.session_state.plot,
                            st.session_state.characters,
                            st.session_state.setting,
                            st.session_state.narrative_technique,
                            chapter_num=chapter['number'],
                            scene_num=scene_num,
                            scene_title=new_title
                        )
                        if new_content:
                            # Validar que la escena tenga exactamente 9 párrafos
                            validated_content = validate_scene_content(new_content, expected_paragraphs=st.session_state.total_paragraphs)
                            
                            # Actualizar la escena con el nuevo título y contenido
                            st.session_state.chapters[st.session_state.selected_chapter]['scenes'][st.session_state.selected_scene]['title'] = new_title
                            st.session_state.chapters[st.session_state.selected_chapter]['scenes'][st.session_state.selected_scene]['content'] = validated_content
                            
                            # Actualizar el contenido Markdown
                            # Eliminar el contenido anterior de la escena en markdown_content
                            scene_heading_old = f"### Escena {scene_num}: {scene['title']}\n\n"
                            scene_content_old = scene['content']
                            
                            scene_heading_new = f"### Escena {scene_num}: {new_title}\n\n"
                            scene_content_new = validated_content + "\n\n"
                            
                            st.session_state.markdown_content = st.session_state.markdown_content.replace(
                                scene_heading_old + scene_content_old,
                                scene_heading_new + scene_content_new
                            )
                            
                            st.success(f"Escena {scene_num} del Capítulo {chapter['number']} regenerada exitosamente.")
    # Botón para generar la siguiente escena
    if st.session_state.current_chapter <= st.session_state.total_chapters and st.session_state.current_scene <= st.session_state.total_scenes:
        if st.button("Generar Siguiente Escena"):
            with st.spinner(f"Generando Escena {st.session_state.current_scene} del Capítulo {st.session_state.current_chapter}..."):
                chapter = st.session_state.chapters[st.session_state.current_chapter - 1]
                scene_num = st.session_state.current_scene
                # Generar título para la escena
                generated_title = generate_scene_title(
                    st.session_state.title,
                    st.session_state.genre,
                    st.session_state.audience,
                    st.session_state.plot,
                    st.session_state.characters,
                    st.session_state.setting,
                    st.session_state.narrative_technique,
                    chapter_num=st.session_state.current_chapter,
                    scene_num=scene_num
                )
                if not generated_title:
                    st.error(f"No se pudo generar el título para la escena {scene_num} del capítulo {st.session_state.current_chapter}.")
                else:
                    # Generar contenido para la escena
                    generated_content = generate_scene_content(
                        st.session_state.title,
                        st.session_state.genre,
                        st.session_state.audience,
                        st.session_state.plot,
                        st.session_state.characters,
                        st.session_state.setting,
                        st.session_state.narrative_technique,
                        chapter_num=st.session_state.current_chapter,
                        scene_num=scene_num,
                        scene_title=generated_title
                    )
                    if generated_content:
                        # Validar que la escena tenga exactamente 9 párrafos
                        validated_content = validate_scene_content(generated_content, expected_paragraphs=st.session_state.total_paragraphs)
                        
                        # Actualizar la escena con título y contenido
                        chapter['scenes'].append({
                            "number": scene_num,
                            "title": generated_title,
                            "content": validated_content
                        })
                        
                        # Agregar al contenido Markdown
                        scene_heading = f"### Escena {scene_num}: {generated_title}\n\n"
                        scene_content = validated_content + "\n\n"
                        st.session_state.markdown_content += f"{scene_heading}{scene_content}"
                        
                        st.success(f"Escena {scene_num} del Capítulo {st.session_state.current_chapter} generada exitosamente.")
                        st.session_state.current_scene += 1
                        
                        # Actualizar la barra de progreso
                        generated_scenes += 1
                        progress = generated_scenes / total_scenes
                        progress_bar.progress(progress)
                        
                        # Pausa de 3 segundos entre escenas
                        time.sleep(3)
    # Botón para generar el siguiente capítulo
    if st.session_state.current_chapter <= st.session_state.total_chapters and st.session_state.current_scene > st.session_state.total_scenes:
        if st.button("Generar Siguiente Capítulo"):
            with st.spinner(f"Generando Capítulo {st.session_state.current_chapter}..."):
                # Generar título para el capítulo
                generated_title = generate_chapter_title(
                    st.session_state.title,
                    st.session_state.genre,
                    st.session_state.audience,
                    st.session_state.plot,
                    st.session_state.characters,
                    st.session_state.setting,
                    st.session_state.narrative_technique,
                    chapter_num=st.session_state.current_chapter
                )
                if not generated_title:
                    st.error(f"No se pudo generar el título para el capítulo {st.session_state.current_chapter}.")
                else:
                    # Actualizar el capítulo con título
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
            partial_markdown = f"# {st.session_state.title}\n\n**Género:** {st.session_state.genre}\n\n**Audiencia:** {st.session_state.audience}\n\n**Trama:** {st.session_state.plot}\n\n**Personajes:**\n{st.session_state.characters}\n\n**Ambientación:** {st.session_state.setting}\n\n**Técnica Narrativa:** {st.session_state.narrative_technique}\n\n## Tabla de Capítulos\n\n"
            for chap in st.session_state.chapters:
                partial_markdown += f"Capítulo {chap['number']}: {chap['title']}\n"
            partial_markdown += "\n"
            for chap in st.session_state.chapters:
                if chap['scenes']:
                    for sec in chap['scenes']:
                        partial_markdown += f"## Capítulo {chap['number']}: {chap['title']}\n\n### Escena {sec['number']}: {sec['title']}\n\n{sec['content']}\n\n"
                else:
                    break  # Solo incluir capítulos generados hasta el momento
            # Limpiar el contenido de subdivisiones (opcional)
            partial_markdown = clean_markdown_content(partial_markdown)
            partial_word_file = export_to_word(partial_markdown, st.session_state.title)
            
            # Exportar contenido completo
            if st.session_state.generation_complete:
                complete_markdown = st.session_state.markdown_content
                # No hay referencias al final
                # Limpiar el contenido de subdivisiones (opcional)
                complete_markdown = clean_markdown_content(complete_markdown)
                complete_word_file = export_to_word(complete_markdown, st.session_state.title)
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
