import streamlit as st
import requests
import json
import time
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

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
theme = st.sidebar.text_input("Ingrese el tema para su thriller político:", "")

# Función para llamar a la API de Together
def call_together_api(prompt):
    api_url = "https://api.together.xyz/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {st.secrets['TOGETHER_API_KEY']}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "Qwen/Qwen2.5-7B-Instruct-Turbo",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2500,
        "temperature": 0.7,
        "top_p": 0.7,
        "top_k": 50,
        "repetition_penalty": 1,
        "stop": ["[\"<|eot_id|>\"]"],
        "stream": False
    }
    response = requests.post(api_url, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        return response.json().get("choices")[0].get("message").get("content")
    else:
        st.error(f"Error en la API: {response.status_code} - {response.text}")
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
    estructura = call_together_api(prompt)
    return estructura

# Función para generar cada escena
def generar_escena(capitulo, escena, trama, personajes, ambientacion, tecnica):
    prompt = f"""
    Escribe la Escena {escena} del Capítulo {capitulo} de una novela de suspenso político con las siguientes características:

    Trama: {trama}
    Personajes: {personajes}
    Ambientación: {ambientacion}
    Técnicas literarias: {tecnica}

    La escena debe tener al menos 2000 palabras, mantener la consistencia y coherencia, evitar clichés y frases hechas. 
    Utiliza rayas (—) para las intervenciones de los personajes.
    Debe incluir descripciones vívidas, diálogos agudos y dinámicos, y contribuir al desarrollo de la trama y los personajes.
    """
    escena_texto = call_together_api(prompt)
    return escena_texto

# Función para generar la novela completa
def generar_novela(theme, num_capitulos, num_escenas):
    with st.spinner("Generando la estructura de la novela..."):
        estructura = generar_estructura(theme)
        if not estructura:
            st.error("No se pudo generar la estructura de la novela.")
            return None

    st.subheader("Estructura de la Novela")
    st.text(estructura)

    # Procesar la estructura para extraer título, trama, etc.
    lineas = estructura.split('\n')
    titulo = ""
    trama = ""
    personajes = ""
    ambientacion = ""
    tecnica = ""

    for linea in lineas:
        if linea.lower().startswith("título"):
            titulo = linea.split(":", 1)[1].strip()
        elif linea.lower().startswith("trama"):
            trama = linea.split(":", 1)[1].strip()
        elif linea.lower().startswith("personajes"):
            personajes = linea.split(":", 1)[1].strip()
        elif linea.lower().startswith("ambientación"):
            ambientacion = linea.split(":", 1)[1].strip()
        elif linea.lower().startswith("técnicas literarias"):
            tecnica = linea.split(":", 1)[1].strip()

    st.subheader("Título")
    st.write(titulo)

    st.subheader("Trama")
    st.write(trama)

    st.subheader("Personajes")
    st.write(personajes)

    st.subheader("Ambientación")
    st.write(ambientacion)

    st.subheader("Técnicas Literarias")
    st.write(tecnica)

    novela = f"**{titulo}**\n\n"

    # Generar cada capítulo y escena
    for cap in range(1, num_capitulos + 1):
        novela += f"## Capítulo {cap}\n\n"
        for esc in range(1, num_escenas + 1):
            with st.spinner(f"Generando Capítulo {cap}, Escena {esc}..."):
                escena = generar_escena(cap, esc, trama, personajes, ambientacion, tecnica)
                if not escena:
                    st.error(f"No se pudo generar la Escena {esc} del Capítulo {cap}.")
                    return None
            novela += f"### Escena {esc}\n\n{escena}\n\n"
            # Retraso para evitar exceder los límites de la API
            time.sleep(1)

    return titulo, trama, personajes, ambientacion, tecnica, novela

# Función para exportar la novela a un archivo de Word con el formato especificado
def exportar_a_word(titulo, novela_completa):
    document = Document()

    # Configurar el tamaño de la página y márgenes
    section = document.sections[0]
    section.page_width = Inches(5)
    section.page_height = Inches(8)
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.7)
    section.right_margin = Inches(0.7)

    # Establecer el estilo normal con la fuente Alegreya, 12 pt
    style = document.styles['Normal']
    font = style.font
    font.name = 'Alegreya'
    font.size = Pt(12)

    # Agregar el título
    document.add_heading(titulo, level=0).alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

    # Separar la novela por capítulos
    capítulos = novela_completa.split("## Capítulo")
    for cap in capítulos:
        if cap.strip() == "":
            continue
        cap_num, *cap_contenido = cap.split('\n', 1)
        cap_num = cap_num.strip()
        cap_text = cap_contenido[0].strip() if cap_contenido else ""
        document.add_heading(f"Capítulo {cap_num}", level=1)

        # Separar por escenas
        escenas = cap_text.split("### Escena")
        for esc in escenas:
            if esc.strip() == "":
                continue
            esc_num, *esc_contenido = esc.split('\n', 1)
            esc_num = esc_num.strip()
            esc_text = esc_contenido[0].strip() if esc_contenido else ""
            document.add_heading(f"Escena {esc_num}", level=2)
            # Agregar el texto de la escena
            paragraph = document.add_paragraph(esc_text)
            paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY
            paragraph_format = paragraph.paragraph_format
            paragraph_format.line_spacing = 1.15
            paragraph_format.space_after = Pt(6)

    # Guardar el documento en memoria
    from io import BytesIO
    buffer = BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer

# Interfaz de usuario para generar y descargar la novela
if st.button("Generar Novela"):
    if not theme:
        st.error("Por favor, ingrese un tema.")
    else:
        titulo, trama, personajes, ambientacion, tecnica, novela_completa = generar_novela(theme, num_capitulos, num_escenas)
        if novela_completa:
            st.success("Novela generada con éxito.")
            # Exportar a Word
            doc_buffer = exportar_a_word(titulo, novela_completa)
            st.download_button(
                label="Descargar Novela en Word",
                data=doc_buffer,
                file_name=f"novela_thriller_politico_{int(time.time())}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            # Mostrar la novela en la interfaz
            st.text_area("Novela Generada:", novela_completa, height=600)
