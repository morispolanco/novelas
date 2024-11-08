import streamlit as st
import requests
from docx import Document
from io import BytesIO
import backoff
import re
from difflib import SequenceMatcher
from PIL import Image
from docx.shared import Inches

# Definir constantes
MAX_INTENTOS = 3  # Número máximo de intentos para generar ilustraciones

# Configuración de la página
st.set_page_config(
    page_title="📝 Adventure Tales Generator for Kids",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📝 Adventure Tales Generator for Kids (9-12 años)")
st.write("""
Esta aplicación genera automáticamente una historia de aventuras para niños de 9 a 12 años en inglés, incluyendo tres ilustraciones por historia. Simplemente selecciona el rango de edad y haz clic en el botón para generar tu cuento.
""")

# Inicializar estado de la sesión
if 'capitulos' not in st.session_state:
    st.session_state.capitulos = []
if 'titulo_obra' not in st.session_state:
    st.session_state.titulo_obra = "Adventure Tales"
if 'proceso_generado' not in st.session_state:
    st.session_state.proceso_generado = False
if 'temas_utilizados' not in st.session_state:
    st.session_state.temas_utilizados = []

# Función para medir la similitud entre dos textos
def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

# Prompt personalizado refinado sin marcadores de posición innecesarios
PROMPT_BASE = """
Write an adventure story intended for {rango_edad} years old. The story should be exciting and age-appropriate, including elements such as challenges, brave characters, and imaginative settings. Ensure the content is entertaining, but also safe and suitable for children. Include an interesting conflict and a resolution that leaves a positive message.

# Requirements and Suggestions
- The story should be between 500 and 700 words, using accessible and understandable language for readers in this age group.
- Introduce lovable characters that readers can empathize with, such as curious children, magical animals, or fantastical beings.
- There should be at least one obstacle or challenge that the characters must overcome, with a positive message about teamwork, bravery, or creativity at the end.
- Use visual descriptions to create vibrant scenes, but avoid using overly complex terms or situations.

# Suggested Structure
1. **Introduction**: Present the protagonist and the initial setting where a calm situation is experienced before the adventure begins.
2. **Conflict**: An event that changes the protagonist's routine and leads them to an unexpected mission.
3. **Development**: Moments of action where the protagonist faces challenges and obstacles. There can be a companion who helps the protagonist.
4. **Resolution**: The conclusion of the adventure with a creative solution and a happy ending that offers reflection or a positive message.

# Tone and Style
- **Tone**: Adventurous, motivating, fun.
- **Narrative Style**: Third person or first person.

# Output Format
The output should include:
1. **CHAPTER 1: The Title**
2. **Summary:** A brief summary of the chapter.
3. **Theme:** The main theme of the chapter.
4. **Illustrations:** Three descriptions for illustrations relevant to the story.
5. **Story Content:** The full story, between 500-700 words.

Each time a speaking character changes, use a line break for clarity.

# Unique Theme Instruction
Each story must have a unique theme that has not been used in previous stories. Refer to the list of used themes below and choose a new, distinct theme for this story. Avoid using similar phrases or titles such as "The Quest for...", "The Mystery of...", or "The Adventure of...".
"""

# Función para extraer el título usando expresiones regulares
def extraer_titulo(respuesta):
    patron = r'CHAPTER\s*1:\s*(.*)'
    match = re.search(patron, respuesta, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "Untitled Chapter"

# Función para extraer el resumen del cuento
def extraer_resumen(respuesta):
    patron = r'Summary:\s*(.*)'
    match = re.search(patron, respuesta, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "No summary available."

# Función para extraer el tema principal del cuento
def extraer_tema(respuesta):
    patron = r'Theme:\s*(.*)'
    match = re.search(patron, respuesta, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "No theme identified."

# Función para extraer las ilustraciones
def extraer_ilustraciones(respuesta):
    patron = r'Illustrations:\s*((?:.|\n)*?)\n{2,}'
    match = re.search(patron, respuesta, re.IGNORECASE)
    if match:
        ilustraciones_texto = match.group(1).strip()
        ilustraciones = re.findall(r'\d+\.\s*(.*)', ilustraciones_texto)
        return ilustraciones if len(ilustraciones) == 3 else []
    return []

# Función con reintentos para generar la historia
@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=MAX_INTENTOS)
def generar_historia(rango_edad):
    """
    Genera una historia completa incluyendo título, resumen, tema e ilustraciones.
    
    Args:
        rango_edad (str): Rango de edad seleccionado.
    
    Returns:
        tuple: (titulo_generado, resumen_generado, tema_generado, ilustraciones_generadas, contenido)
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}"
    }

    temas_utilizados = st.session_state.temas_utilizados
    if temas_utilizados:
        temas_formateados = "; ".join(temas_utilizados)
        prompt = PROMPT_BASE.format(rango_edad=rango_edad).replace(
            "Refer to the list of used themes below and choose a new, distinct theme for this story.",
            f"Refer to the list of used themes below and choose a new, distinct theme for this story.\n\nUsed Themes: {temas_formateados}"
        )
    else:
        prompt = PROMPT_BASE.format(rango_edad=rango_edad).replace(
            "Refer to the list of used themes below and choose a new, distinct theme for this story.",
            "Refer to the list of used themes below and choose a new, distinct theme for this story.\n\nUsed Themes: None"
        )

    data = {
        "model": "openai/gpt-4",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    response = requests.post(url, headers=headers, json=data, timeout=60)
    response.raise_for_status()
    respuesta = response.json()
    if 'choices' in respuesta and len(respuesta['choices']) > 0:
        contenido_completo = respuesta['choices'][0]['message']['content']
        titulo_generado = extraer_titulo(contenido_completo)
        resumen_generado = extraer_resumen(contenido_completo)
        tema_generado = extraer_tema(contenido_completo)
        ilustraciones_generadas = extraer_ilustraciones(contenido_completo)
        contenido = contenido_completo.split("Story Content:")[1].strip() if "Story Content:" in contenido_completo else "No content available."
        return titulo_generado, resumen_generado, tema_generado, ilustraciones_generadas, contenido
    else:
        st.error("Unexpected API response when generating the story.")
        return "Untitled Chapter", "No summary available.", "No theme identified.", [], "No content available."

# Función para generar una ilustración usando la API de Together
def generar_ilustracion(descripcion):
    """
    Genera una ilustración basada en la descripción proporcionada utilizando la API de Together.
    
    Args:
        descripcion (str): Descripción de la ilustración.
    
    Returns:
        Image: Objeto PIL Image de la ilustración generada o None si falla.
    """
    url = "https://api.together.com/v1/images/generate"  # Reemplaza con el endpoint real de Together
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {st.secrets['TOGETHER_API_KEY']}"
    }
    data = {
        "prompt": descripcion,
        "num_images": 1,
        "size": "1024x1024"  # Ajusta según las opciones disponibles en Together
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        respuesta = response.json()

        # Suponiendo que la API devuelve una URL de la imagen generada
        imagen_url = respuesta.get("data")[0].get("url")
        if imagen_url:
            imagen_response = requests.get(imagen_url)
            imagen = Image.open(BytesIO(imagen_response.content))
            return imagen
        else:
            st.warning(f"No se pudo generar la ilustración para: {descripcion}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error al generar la ilustración: {e}")
        return None

# Función para crear el documento Word con tabla de contenidos e ilustraciones
def crear_documento(titulo_obra, titulo, resumen, tema, ilustraciones, contenido):
    """
    Crea un documento Word que incluye la tabla de contenidos y el capítulo con sus ilustraciones.
    
    Args:
        titulo_obra (str): Título de la obra.
        titulo (str): Título del capítulo.
        resumen (str): Resumen del capítulo.
        tema (str): Tema del capítulo.
        ilustraciones (list): Lista de descripciones de ilustraciones.
        contenido (str): Contenido completo de la historia.
    
    Returns:
        BytesIO: Buffer del documento Word generado.
    """
    doc = Document()
    doc.add_heading(titulo_obra, 0)

    # Crear Tabla de Contenidos
    doc.add_heading("Table of Contents", level=1)
    toc_entry = f"CHAPTER 1: {titulo}"
    toc_summary = f"Summary: {resumen}"
    doc.add_paragraph(toc_entry, style='List Number')
    doc.add_paragraph(toc_summary, style='List Bullet')

    doc.add_page_break()

    # Agregar el capítulo
    doc.add_heading(f"CHAPTER 1: {titulo}", level=1)
    doc.add_paragraph(contenido)

    # Agregar ilustraciones
    if ilustraciones:
        doc.add_heading("Illustrations", level=2)
        for idx, descripcion in enumerate(ilustraciones, 1):
            imagen = generar_ilustracion(descripcion)
            if imagen:
                # Convertir PIL Image a BytesIO
                imagen_buffer = BytesIO()
                imagen.save(imagen_buffer, format='PNG')
                imagen_buffer.seek(0)

                doc.add_paragraph(f"Illustration {idx}: {descripcion}")
                doc.add_picture(imagen_buffer, width=Inches(6))
            else:
                doc.add_paragraph(f"Illustration {idx}: {descripcion} (Image not available)")

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# Interfaz de usuario para generar la historia
if not st.session_state.proceso_generado:
    st.sidebar.title("Opciones")
    rangos_edades = ["9-12 años"]  # Puedes ampliar los rangos si lo deseas
    rango_edad = st.sidebar.selectbox("Selecciona el rango de edad para la historia:", rangos_edades)

    if st.button("Generar Historia"):
        st.session_state.proceso_generado = True
        st.session_state.capitulos = []
        st.session_state.temas_utilizados = []

        with st.spinner("Generando la historia..."):
            titulo_generado, resumen_generado, tema_generado, ilustraciones_generadas, contenido = generar_historia(rango_edad)
            if tema_generado and tema_generado not in st.session_state.temas_utilizados:
                st.session_state.capitulos.append((titulo_generado, resumen_generado, tema_generado, ilustraciones_generadas, contenido))
                st.session_state.temas_utilizados.append(tema_generado)
            else:
                st.error("No se pudo generar una historia con un tema único. Intenta nuevamente.")
                st.session_state.proceso_generado = False

        if st.session_state.capitulos:
            st.success("¡Historia generada exitosamente!")

else:
    if st.session_state.capitulos:
        titulo_obra = st.text_input("Título de la obra:", value=st.session_state.titulo_obra)
        if st.button("Descargar Historia en Word"):
            capitulos = st.session_state.capitulos[0]
            documento = crear_documento(
                titulo_obra,
                capitulos[0],  # Título del capítulo
                capitulos[1],  # Resumen
                capitulos[2],  # Tema
                capitulos[3],  # Ilustraciones
                capitulos[4]   # Contenido
            )
            st.download_button(
                label="Descargar en Word",
                data=documento,
                file_name="Adventure_Tales.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

        # Mostrar la historia y las ilustraciones en la interfaz
        st.markdown("---")
        st.header("📖 Generated Adventure Tale")

        capitulos = st.session_state.capitulos[0]
        st.markdown(f"**CHAPTER 1: {capitulos[0]}**")
        st.markdown(f"*Summary:* {capitulos[1]}")
        st.markdown(f"*Theme:* {capitulos[2]}")

        st.markdown("---")
        st.write(capitulos[4])  # Contenido de la historia

        if capitulos[3]:
            st.subheader("📷 Illustrations")
            for idx, descripcion in enumerate(capitulos[3], 1):
                imagen = generar_ilustracion(descripcion)
                if imagen:
                    st.image(imagen, caption=f"Illustration {idx}: {descripcion}", use_column_width=True)
                else:
                    st.write(f"**Illustration {idx}:** {descripcion} (Image not available)")
