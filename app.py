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
st.title("Generador de Novelas")

# Descripción de la aplicación
st.markdown("""
Esta aplicación genera automáticamente el título, trama, personajes, ambientación, técnica narrativa y tabla de capítulos de una novela basada en el tema, género y audiencia que proporciones.
Puedes generar los capítulos y sus escenas una por una de manera continua, permitiéndote descargar contenido parcial en cualquier momento.
Finalmente, puedes exportar la novela completa a un archivo en formato Word.
""")

# Inicialización de variables en el estado de la sesión
if 'title' not in st.session_state:
    st.session_state.title = ""
if 'plot' not in st.session_state:
    st.session_state.plot = ""
if 'characters' not in st.session_state:
    st.session_state.characters = ""
if 'setting' not in st.session_state:
    st.session_state.setting = ""
if 'narrative_technique' not in st.session_state:
    st.session_state.narrative_technique = ""
if 'table_of_contents' not in st.session_state:
    st.session_state.table_of_contents = []
if 'chapters' not in st.session_state:
    st.session_state.chapters = []
if 'current_chapter' not in st.session_state:
    st.session_state.current_chapter = 1
if 'current_scene' not in st.session_state:
    st.session_state.current_scene = 1
if 'total_chapters' not in st.session_state:
    st.session_state.total_chapters = 9
if 'total_scenes' not in st.session_state:
    st.session_state.total_scenes = 5
if 'total_paragraphs' not in st.session_state:
    st.session_state.total_paragraphs = 27
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
    st.session_state.plot = ""
    st.session_state.characters = ""
    st.session_state.setting = ""
    st.session_state.narrative_technique = ""
    st.session_state.table_of_contents = []
    st.session_state.chapters = []
    st.session_state.current_chapter = 1
    st.session_state.current_scene = 1
    st.session_state.markdown_content = ""
    st.session_state.generation_complete = False
    st.session_state.selected_chapter = None
    st.session_state.selected_scene = None

# Función para llamar a la API de OpenRouter con reintentos
def call_openrouter_api(messages, model="openai/gpt-4o-mini", retries=3, delay=2):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}"
    }
    data = {
        "model": model,
        "messages": messages,
        "max_tokens": 3500
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
            st.warning(f"Reintentando en {delay} segundos...")
            time.sleep(delay)
    st.error("No se pudo obtener una respuesta válida de la API después de varios intentos.")
    return None

# Función para generar título, trama, personajes, ambientación y técnica narrativa
def generate_novel_elements(topic, genre, audience):
    prompt = f"""Eres un escritor que está creando una novela. Genera los siguientes elementos basados en el tema, género y audiencia proporcionados.

Tema: {topic}
Género: {genre}
Audiencia: {audience}

Necesito que proporciones:

Título: [Título de la novela]
Trama: [Resumen de la trama en un párrafo]
Personajes: [Lista de personajes principales con una breve descripción]
Ambientación: [Descripción del escenario donde ocurre la historia]
Técnica Narrativa: [Explicación de la técnica narrativa que se utilizará]

Por favor, sigue el formato proporcionado.
"""
    messages = [
        {"role": "user", "content": prompt}
    ]
    response = call_openrouter_api(messages)
    if response:
        # Separar los elementos
        elements = {}
        current_key = None
        for line in response.split('\n'):
            if line.startswith("Título:"):
                current_key = "title"
                elements[current_key] = line.replace("Título:", "").strip()
            elif line.startswith("Trama:"):
                current_key = "plot"
                elements[current_key] = line.replace("Trama:", "").strip()
            elif line.startswith("Personajes:"):
                current_key = "characters"
                elements[current_key] = line.replace("Personajes:", "").strip()
            elif line.startswith("Ambientación:"):
                current_key = "setting"
                elements[current_key] = line.replace("Ambientación:", "").strip()
            elif line.startswith("Técnica Narrativa:"):
                current_key = "narrative_technique"
                elements[current_key] = line.replace("Técnica Narrativa:", "").strip()
            elif current_key:
                elements[current_key] += "\n" + line.strip()
        return elements
    return None

# Función para generar la tabla de capítulos
def generate_table_of_chapters(title, total_chapters):
    prompt = f"""Genera una tabla de capítulos para la novela titulada "{title}". La tabla debe contener {total_chapters} capítulos con títulos atractivos y relevantes para la trama. No incluyas descripciones, solo los títulos.

Formato de respuesta:
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

# Función para generar contenido de una escena
def generate_scene_content(title, plot, characters, setting, narrative_technique, chapter_num, chapter_title, scene_num):
    prompt = f"""Escribe la Escena {scene_num} del Capítulo {chapter_num}, "{chapter_title}", de la novela titulada "{title}". Utiliza la siguiente información:

- Trama: {plot}
- Personajes: {characters}
- Ambientación: {setting}
- Técnica Narrativa: {narrative_technique}

La escena debe tener exactamente 9 párrafos y continuar la historia de manera coherente. No incluyas encabezados ni títulos. Escribe en un estilo atractivo que enganche al lector. En los diálogos, utiliza la raya (—) para introducir las intervenciones de los personajes, siguiendo las normas de puntuación en español.

Contenido de la escena:
"""
    messages = [
        {"role": "user", "content": prompt}
    ]
    response = call_openrouter_api(messages)
    return response

# Función para validar que cada escena tenga exactamente 9 párrafos
def validate_scene_paragraphs(scene_content, expected_paragraphs=9):
    paragraphs = [p for p in scene_content.strip().split('\n') if p.strip() != ""]
    num_paragraphs = len(paragraphs)
    if num_paragraphs < expected_paragraphs:
        # Generar párrafos faltantes
        paragraphs_needed = expected_paragraphs - num_paragraphs
        additional_paragraphs = []
        for _ in range(paragraphs_needed):
            prompt = """Escribe un párrafo adicional que continúe la historia de manera coherente. Utiliza la raya (—) en los diálogos si corresponde."""
            messages = [
                {"role": "user", "content": prompt}
            ]
            new_paragraph = call_openrouter_api(messages)
            if new_paragraph:
                additional_paragraphs.append(new_paragraph)
            else:
                break
        paragraphs.extend(additional_paragraphs)
    elif num_paragraphs > expected_paragraphs:
        # Limitar a los párrafos necesarios
        paragraphs = paragraphs[:expected_paragraphs]
    return "\n\n".join(paragraphs)

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
        chapter_index = int(selected_chapter.split(" ")[1].replace(":", "")) - 1
        # Verificar que el índice esté dentro del rango
        if 0 <= chapter_index < len(st.session_state.chapters):
            st.session_state.selected_chapter = chapter_index
            chapter = st.session_state.chapters[chapter_index]
            if chapter['scenes']:
                scene_numbers = [f"Escena {scene['number']}" for scene in chapter['scenes']]
                selected_scene = st.selectbox(
                    "Selecciona una escena para ver:",
                    scene_numbers,
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
    else:
        st.info("No hay capítulos generados aún.")

# --- Sección Principal ---

# Entradas de usuario para el tema, género y audiencia
st.header("Datos Iniciales de la Novela")
with st.form("novel_info_form"):
    topic = st.text_input("Ingresa el tema de tu novela:", "")
    genre = st.text_input("Ingresa el género de tu novela:", "")
    audience = st.text_input("Ingresa la audiencia objetivo de tu novela:", "")
    submit_novel_info = st.form_submit_button("Generar Elementos de la Novela")

if submit_novel_info and not st.session_state.title:
    if not topic or not genre or not audience:
        st.warning("Por favor, completa todos los campos para generar los elementos de la novela.")
    else:
        with st.spinner("Generando título, trama, personajes, ambientación y técnica narrativa..."):
            elements = generate_novel_elements(topic, genre, audience)
            if elements:
                st.session_state.title = elements.get('title', '')
                st.session_state.plot = elements.get('plot', '')
                st.session_state.characters = elements.get('characters', '')
                st.session_state.setting = elements.get('setting', '')
                st.session_state.narrative_technique = elements.get('narrative_technique', '')
                # Generar tabla de capítulos
                table_of_chapters = generate_table_of_chapters(st.session_state.title, st.session_state.total_chapters)
                if table_of_chapters:
                    st.session_state.table_of_contents = table_of_chapters
                    st.session_state.chapters = [{"number": chap['number'], "title": chap['title'], "scenes": []} for chap in table_of_chapters]
                    # Construir el contenido Markdown
                    st.session_state.markdown_content = f"# {st.session_state.title}\n\n"
                    st.session_state.markdown_content += f"## Trama\n\n{st.session_state.plot}\n\n"
                    st.session_state.markdown_content += f"## Personajes\n\n{st.session_state.characters}\n\n"
                    st.session_state.markdown_content += f"## Ambientación\n\n{st.session_state.setting}\n\n"
                    st.session_state.markdown_content += f"## Técnica Narrativa\n\n{st.session_state.narrative_technique}\n\n"
                    st.session_state.markdown_content += f"## Tabla de Capítulos\n\n"
                    for chap in table_of_chapters:
                        st.session_state.markdown_content += f"{chap['number']}. {chap['title']}\n"
                    st.session_state.markdown_content += "\n"
                    st.success("Elementos de la novela generados exitosamente.")
                else:
                    st.error("No se pudo generar la tabla de capítulos.")
            else:
                st.error("No se pudieron generar los elementos de la novela.")

# Permitir edición de la información inicial si ya se ha generado
if st.session_state.title and st.session_state.plot and st.session_state.table_of_contents:
    st.markdown("---")
    st.header("Editar Información Inicial")
    
    with st.form("edit_initial_info"):
        # Editar Título
        edited_title = st.text_input("Título de la Novela:", st.session_state.title)
        
        # Editar Trama
        edited_plot = st.text_area("Trama de la Novela:", st.session_state.plot, height=200)
        
        # Editar Personajes
        edited_characters = st.text_area("Personajes:", st.session_state.characters, height=200)
        
        # Editar Ambientación
        edited_setting = st.text_area("Ambientación:", st.session_state.setting, height=200)
        
        # Editar Técnica Narrativa
        edited_narrative_technique = st.text_area("Técnica Narrativa:", st.session_state.narrative_technique, height=200)
        
        # Editar Tabla de Capítulos
        st.subheader("Tabla de Capítulos")
        edited_table = []
        for chap in st.session_state.chapters:
            edited_title_chap = st.text_input(f"Capítulo {chap['number']}:", chap['title'], key=f"chap_{chap['number']}")
            edited_table.append({"number": chap['number'], "title": edited_title_chap, "scenes": chap.get('scenes', [])})
        
        submit_edit = st.form_submit_button("Guardar Cambios")
        
        if submit_edit:
            st.session_state.title = edited_title
            st.session_state.plot = edited_plot
            st.session_state.characters = edited_characters
            st.session_state.setting = edited_setting
            st.session_state.narrative_technique = edited_narrative_technique
            st.session_state.table_of_contents = edited_table
            st.session_state.chapters = edited_table
            # Reconstruir el contenido Markdown
            st.session_state.markdown_content = f"# {st.session_state.title}\n\n"
            st.session_state.markdown_content += f"## Trama\n\n{st.session_state.plot}\n\n"
            st.session_state.markdown_content += f"## Personajes\n\n{st.session_state.characters}\n\n"
            st.session_state.markdown_content += f"## Ambientación\n\n{st.session_state.setting}\n\n"
            st.session_state.markdown_content += f"## Técnica Narrativa\n\n{st.session_state.narrative_technique}\n\n"
            st.session_state.markdown_content += f"## Tabla de Capítulos\n\n"
            for chap in st.session_state.table_of_contents:
                st.session_state.markdown_content += f"{chap['number']}. {chap['title']}\n"
            st.session_state.markdown_content += "\n"
            st.success("Información inicial actualizada exitosamente.")

# Mostrar la sección para generar capítulos y escenas solo si la información inicial ha sido generada
if st.session_state.title and st.session_state.plot and st.session_state.table_of_contents:
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
            st.subheader(f"Capítulo {chapter['number']}: {chapter['title']}")
            st.markdown(f"### Escena {scene['number']}")
            if scene['content']:
                # Mostrar contenido de la escena
                st.markdown(scene['content'])
            else:
                st.info("Esta escena aún no ha sido generada.")
            if st.button("Regenerar Escena"):
                with st.spinner(f"Regenerando Escena {scene['number']} del Capítulo {chapter['number']}..."):
                    # Generar contenido para la escena
                    new_content = generate_scene_content(
                        st.session_state.title,
                        st.session_state.plot,
                        st.session_state.characters,
                        st.session_state.setting,
                        st.session_state.narrative_technique,
                        chapter['number'],
                        chapter['title'],
                        scene['number']
                    )
                    if new_content:
                        # Validar que la escena tenga exactamente 9 párrafos
                        validated_content = validate_scene_paragraphs(new_content, expected_paragraphs=st.session_state.total_paragraphs)
                        # Actualizar la escena con el nuevo contenido
                        st.session_state.chapters[st.session_state.selected_chapter]['scenes'][st.session_state.selected_scene]['content'] = validated_content
                        # Actualizar el contenido Markdown
                        # Primero, eliminar el contenido anterior de la escena en markdown_content
                        scene_heading_old = f"### Escena {scene['number']}\n\n"
                        scene_content_old = scene['content']
                        scene_heading_new = f"### Escena {scene['number']}\n\n"
                        scene_content_new = validated_content + "\n\n"
                        # Reemplazar en markdown_content
                        st.session_state.markdown_content = st.session_state.markdown_content.replace(
                            scene_heading_old + scene_content_old,
                            scene_heading_new + scene_content_new
                        )
                        st.success(f"Escena {scene['number']} del Capítulo {chapter['number']} regenerada exitosamente.")
                    else:
                        st.error(f"No se pudo regenerar la escena {scene['number']} del capítulo {chapter['number']}.")

    # Botón para generar la siguiente escena
    if st.session_state.current_chapter <= st.session_state.total_chapters and st.session_state.current_scene <= st.session_state.total_scenes:
        if st.button("Generar Siguiente Escena"):
            with st.spinner(f"Generando Escena {st.session_state.current_scene} del Capítulo {st.session_state.current_chapter}..."):
                chapter = st.session_state.chapters[st.session_state.current_chapter - 1]
                if not chapter['scenes']:
                    # Inicializar escenas si aún no se han creado
                    chapter['scenes'] = [{"number": i+1, "content": ""} for i in range(st.session_state.total_scenes)]
                scene = chapter['scenes'][st.session_state.current_scene - 1]
                # Generar contenido para la escena
                generated_content = generate_scene_content(
                    st.session_state.title,
                    st.session_state.plot,
                    st.session_state.characters,
                    st.session_state.setting,
                    st.session_state.narrative_technique,
                    chapter['number'],
                    chapter['title'],
                    scene['number']
                )
                if generated_content:
                    # Validar que la escena tenga exactamente 9 párrafos
                    validated_content = validate_scene_paragraphs(generated_content, expected_paragraphs=st.session_state.total_paragraphs)
                    # Actualizar la escena con contenido
                    scene['content'] = validated_content
                    # Agregar al contenido Markdown
                    scene_heading = f"### Escena {scene['number']}\n\n"
                    scene_content = validated_content + "\n\n"
                    st.session_state.markdown_content += f"{scene_heading}{scene_content}"
                    st.success(f"Escena {scene['number']} del Capítulo {chapter['number']} generada exitosamente.")
                    st.session_state.current_scene += 1
                    # Actualizar la barra de progreso
                    generated_scenes += 1
                    progress = generated_scenes / total_scenes
                    progress_bar.progress(progress)
                    # Pausa de 3 segundos entre escenas
                    time.sleep(3)
                else:
                    st.error(f"No se pudo generar el contenido para la escena {scene['number']} del capítulo {chapter['number']}.")

    # Botón para avanzar al siguiente capítulo
    if st.session_state.current_chapter <= st.session_state.total_chapters and st.session_state.current_scene > st.session_state.total_scenes:
        st.session_state.current_chapter += 1
        st.session_state.current_scene = 1
        st.info(f"Capítulo {st.session_state.current_chapter - 1} completado. Puedes comenzar a generar las escenas del Capítulo {st.session_state.current_chapter}.")

    # Verificar si la generación está completa
    if all(len(chap['scenes']) == st.session_state.total_scenes and all(scene['content'] for scene in chap['scenes']) for chap in st.session_state.chapters):
        st.session_state.generation_complete = True
        st.success("¡La novela ha sido generada completamente!")

    # Botones para exportar a Word
    if st.session_state.chapters:
        # Exportar contenido parcial
        partial_markdown = st.session_state.markdown_content
        partial_word_file = export_to_word(partial_markdown)
        
        # Exportar contenido completo si la generación está completa
        if st.session_state.generation_complete:
            complete_markdown = st.session_state.markdown_content
            complete_word_file = export_to_word(complete_markdown)
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
