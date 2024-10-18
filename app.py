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
    page_title="Generador de Novelas Automático",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Título de la aplicación
st.title("Generador de Novelas Automático")

# Descripción de la aplicación
st.markdown("""
Esta aplicación genera automáticamente una novela basada en el título, género y audiencia proporcionados. 
Las escenas y capítulos se generan automáticamente con pausas para simular un flujo más natural de escritura.
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
    st.session_state.chapters = []
if 'current_chapter' not in st.session_state:
    st.session_state.current_chapter = 1
if 'current_scene' not in st.session_state:
    st.session_state.current_scene = 1
if 'total_chapters' not in st.session_state:
    st.session_state.total_chapters = 5  # Ajusta el número de capítulos según tu preferencia
if 'total_scenes' not in st.session_state:
    st.session_state.total_scenes = 5    # Ajusta el número de escenas por capítulo
if 'total_paragraphs' not in st.session_state:
    st.session_state.total_paragraphs = 27
if 'markdown_content' not in st.session_state:
    st.session_state.markdown_content = ""
if 'generation_complete' not in st.session_state:
    st.session_state.generation_complete = False

# Función para llamar a la API de OpenRouter
def call_openrouter_api(prompt, model="qwen/qwen-7b", max_tokens=3000, temperature=0.7, retries=3, delay_seconds=2):
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
        "messages": [{"role": "user", "content": prompt}],
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
                        continue
        return table
    return None

# Función para generar una escena
def generate_scene(plot, characters, setting, narrative_technique, chapter_num, scene_num):
    prompt = f"""Escribe una escena para el capítulo {chapter_num} de una novela. La escena debe tener exactamente {st.session_state.total_paragraphs} párrafos. Usa raya (—) para los diálogos y no incluyas títulos para la escena.

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
    response = call_openrouter_api(prompt)
    if response:
        response = response.replace('"', '—').replace("“", '—').replace("”", '—')
        return response.strip()
    return None

# Función para exportar a Word
def export_to_word(markdown_content):
    html = markdown.markdown(markdown_content)
    soup = BeautifulSoup(html, 'html.parser')
    doc = Document()
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
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# Función para limpiar el contenido Markdown
def clean_markdown_content(markdown_content):
    cleaned_content = re.sub(r'#{4,} .*', '', markdown_content)
    return cleaned_content

# Función para auto generar escenas con pausas
def auto_generate_scenes():
    progress_bar = st.progress(0)
    total_steps = st.session_state.total_chapters * st.session_state.total_scenes
    current_step = 0

    while st.session_state.current_chapter <= st.session_state.total_chapters:
        chapter = st.session_state.chapters[st.session_state.current_chapter - 1]
        st.session_state.markdown_content += f"## Capítulo {chapter['number']}: {chapter['title']}\n\n"
        while st.session_state.current_scene <= st.session_state.total_scenes:
            with st.spinner(f"Generando Escena {st.session_state.current_scene} del Capítulo {st.session_state.current_chapter}..."):
                generated_content = generate_scene(
                    st.session_state.plot,
                    st.session_state.characters,
                    st.session_state.setting,
                    st.session_state.narrative_technique,
                    chapter_num=st.session_state.current_chapter,
                    scene_num=st.session_state.current_scene
                )
                if generated_content:
                    chapter['scenes'].append({
                        "number": st.session_state.current_scene,
                        "content": generated_content
                    })
                    st.session_state.markdown_content += f"### Escena {st.session_state.current_scene}\n\n{generated_content}\n\n"
                    st.success(f"Escena {st.session_state.current_scene} del Capítulo {st.session_state.current_chapter} generada.")
                    st.session_state.current_scene += 1
                    current_step += 1
                    progress_bar.progress(current_step / total_steps)
                    time.sleep(2)  # Pausa entre escenas
                else:
                    st.error(f"Error al generar la escena {st.session_state.current_scene}.")
                    return
        st.session_state.current_chapter += 1
        st.session_state.current_scene = 1
    st.session_state.generation_complete = True
    st.success("Generación de todas las escenas completada.")
    st.experimental_rerun()  # <-- Forzar actualización de la interfaz

# Interfaz para entrada de detalles de la novela
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

# Generar elementos iniciales
if st.session_state.title and st.session_state.genre and st.session_state.audience and not st.session_state.plot:
    if st.button("Generar Elementos Iniciales de la Novela"):
        with st.spinner("Generando elementos iniciales..."):
            trama, personajes, ambientacion, tecnica = generate_initial_elements(st.session_state.title, st.session_state.genre, st.session_state.audience)
            if trama and personajes and ambientacion and tecnica:
                st.session_state.plot = trama
                st.session_state.characters = personajes
                st.session_state.setting = ambientacion
                st.session_state.narrative_technique = tecnica
                table = generate_table_of_chapters(trama, personajes, ambientacion, tecnica, st.session_state.total_chapters)
                if table:
                    st.session_state.chapters = table
                    st.session_state.markdown_content = f"# {st.session_state.title}\n\n"
                    st.session_state.markdown_content += f"**Género:** {st.session_state.genre}\n\n"
                    st.session_state.markdown_content += f"**Audiencia:** {st.session_state.audience}\n\n"
                    st.session_state.markdown_content += f"## Trama\n\n{st.session_state.plot}\n\n"
                    st.session_state.markdown_content += f"## Personajes Principales\n\n{st.session_state.characters}\n\n"
                    st.session_state.markdown_content += f"## Ambientación\n\n{st.session_state.setting}\n\n"
                    st.session_state.markdown_content += f"## Técnica Narrativa\n\n{st.session_state.narrative_technique}\n\n"
                    st.session_state.markdown_content += f"## Tabla de Capítulos\n\n"
                    for chap in table:
                        st.session_state.markdown_content += f"- Capítulo {chap['number']}: {chap['title']}\n"
                    st.success("Elementos iniciales generados exitosamente.")
                else:
                    st.error("Error al generar la tabla de capítulos.")
            else:
                st.error("No se pudieron generar los elementos iniciales.")

# Comenzar la generación automática una vez que los elementos iniciales están listos
if st.session_state.chapters and not st.session_state.generation_complete:
    if st.button("Iniciar Generación Automática de Novela"):
        auto_generate_scenes()

# Exportar la novela a Word si la generación está completa
if st.session_state.generation_complete:
    cleaned_content = clean_markdown_content(st.session_state.markdown_content)
    complete_word_file = export_to_word(cleaned_content)
    st.download_button(
        label="Descargar Novela Completa en Word",
        data=complete_word_file,
        file_name=f"{st.session_state.title.replace(' ', '_')}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

    # Mostrar el contenido completo en la aplicación
    with st.expander("Ver Contenido Completo de la Novela"):
        st.markdown(st.session_state.markdown_content)
