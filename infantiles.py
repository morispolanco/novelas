import streamlit as st
import requests
from docx import Document
from io import BytesIO
import backoff
import re
from difflib import SequenceMatcher

# Definir constantes
MAX_INTENTOS = 3  # Número máximo de intentos para generar historias
MAX_HISTORIAS = 30  # Número máximo de historias que se pueden generar para evitar sobrecarga
MIN_HISTORIAS = 1   # Número mínimo de historias

# Configuración de la página
st.set_page_config(
    page_title="📝 Generador de Historias para Niños",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📝 Generador de Historias para Niños (9-12 años)")
st.write("""
Esta aplicación genera automáticamente historias de diversos géneros para niños de 9 a 12 años en inglés. Puedes especificar cuántas historias deseas generar y luego descargar todas en un documento Word.
""")

# Inicializar estado de la sesión
if 'historias' not in st.session_state:
    st.session_state.historias = []
if 'proceso_generado' not in st.session_state:
    st.session_state.proceso_generado = False
if 'temas_utilizados' not in st.session_state:
    st.session_state.temas_utilizados = []

# Función para medir la similitud entre dos textos
def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

# Prompt personalizado refinado sin ilustraciones y adaptado para múltiples capítulos
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
1. **CHAPTER {n}: {{Title}}**
2. **Summary:** A brief summary of the chapter.
3. **Theme:** The main theme of the chapter.
4. **Story Content:** The full story, between 500-700 words.

Each time a speaking character changes, use a line break for clarity.

# Unique Theme Instruction
Each story must have a unique theme that has not been used in previous stories. Refer to the list of used themes below and choose a new, distinct theme for this story. Avoid using similar phrases or titles such as "The Quest for...", "The Mystery of...", or "The Adventure of...".
"""

# Función para extraer el título usando expresiones regulares
def extraer_titulo(respuesta, numero_capitulo):
    patron = fr'CHAPTER\s*{numero_capitulo}:\s*(.*)'
    match = re.search(patron, respuesta, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return f"Untitled Chapter {numero_capitulo}"

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

# Función para extraer el contenido de la historia
def extraer_contenido(respuesta):
    patron = r'Story Content:\s*((?:.|\n)*)'
    match = re.search(patron, respuesta, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "No content available."

# Función con reintentos para generar una historia
@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=MAX_INTENTOS)
def generar_historia(rango_edad, numero_capitulo):
    """
    Genera una historia completa incluyendo título, resumen, tema y contenido.

    Args:
        rango_edad (str): Rango de edad seleccionado.
        numero_capitulo (int): Número del capítulo/historia.

    Returns:
        dict: Diccionario con 'titulo', 'resumen', 'tema', 'contenido'.
    """
    url = "https://api.openai.com/v1/chat/completions"  # Asegúrate de que este es el endpoint correcto
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
        "model": "openai/gpt-4o-mini",  # Especificar el modelo requerido
        "messages": [
            {
                "role": "user",
                "content": prompt.format(n=numero_capitulo)
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        respuesta = response.json()
        
        # Depuración: Mostrar la respuesta completa de la API
        st.write(f"**Respuesta de la API de OpenAI para CHAPTER {numero_capitulo}:**")
        st.json(respuesta)
        
        if 'choices' in respuesta and len(respuesta['choices']) > 0:
            contenido_completo = respuesta['choices'][0]['message']['content']
            st.write(f"**Contenido Generado para CHAPTER {numero_capitulo}:**")
            st.text(contenido_completo)
            
            titulo_generado = extraer_titulo(contenido_completo, numero_capitulo)
            resumen_generado = extraer_resumen(contenido_completo)
            tema_generado = extraer_tema(contenido_completo)
            contenido = extraer_contenido(contenido_completo)
            
            return {
                "titulo": titulo_generado,
                "resumen": resumen_generado,
                "tema": tema_generado,
                "contenido": contenido
            }
        else:
            st.error(f"**Error:** La API de OpenAI no devolvió las opciones esperadas para CHAPTER {numero_capitulo}.")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"**Error al generar CHAPTER {numero_capitulo}:** {e}")
        return None

# Función para crear el documento Word con todas las historias
def crear_documento(titulo_obra, historias):
    """
    Crea un documento Word que incluye todas las historias generadas.

    Args:
        titulo_obra (str): Título de la obra.
        historias (list): Lista de diccionarios con 'titulo', 'resumen', 'tema', 'contenido'.

    Returns:
        BytesIO: Buffer del documento Word generado.
    """
    doc = Document()
    doc.add_heading(titulo_obra, 0)

    # Crear Tabla de Contenidos
    doc.add_heading("Table of Contents", level=1)
    for idx, historia in enumerate(historias, 1):
        toc_entry = f"CHAPTER {idx}: {historia['titulo']}"
        toc_summary = f"Summary: {historia['resumen']}"
        doc.add_paragraph(toc_entry, style='List Number')
        doc.add_paragraph(toc_summary, style='List Bullet')
    
    doc.add_page_break()

    # Agregar cada historia
    for idx, historia in enumerate(historias, 1):
        doc.add_heading(f"CHAPTER {idx}: {historia['titulo']}", level=1)
        doc.add_paragraph(historia['contenido'])
        doc.add_page_break()

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# Interfaz de usuario para generar las historias
if not st.session_state.proceso_generado:
    st.sidebar.title("Opciones")
    rangos_edades = ["9-12 años"]  # Puedes ampliar los rangos si lo deseas
    rango_edad = st.sidebar.selectbox("Selecciona el rango de edad para las historias:", rangos_edades)
    
    # Input para el número de historias
    numero_historias = st.sidebar.number_input(
        "¿Cuántas historias deseas generar?",
        min_value=MIN_HISTORIAS,
        max_value=MAX_HISTORIAS,
        value=5,
        step=1,
        help=f"Selecciona un número entre {MIN_HISTORIAS} y {MAX_HISTORIAS}."
    )

    if st.sidebar.button("Generar Historias"):
        st.session_state.proceso_generado = True
        st.session_state.historias = []
        st.session_state.temas_utilizados = []

        with st.spinner(f"Generando {int(numero_historias)} historias..."):
            for i in range(1, int(numero_historias) + 1):
                st.write(f"**Generando CHAPTER {i}...**")
                historia = generar_historia(rango_edad, i)
                if historia:
                    st.session_state.historias.append(historia)
                    st.session_state.temas_utilizados.append(historia['tema'])
                else:
                    st.error(f"No se pudo generar CHAPTER {i}.")

        if st.session_state.historias:
            st.success(f"¡{int(numero_historias)} historias generadas exitosamente!")

else:
    if st.session_state.historias:
        titulo_obra = st.text_input("Título de la obra:", value="Adventure Tales Collection")
        if st.button("Descargar Historias en Word"):
            documento = crear_documento(titulo_obra, st.session_state.historias)
            st.download_button(
                label="Descargar en Word",
                data=documento,
                file_name="Adventure_Tales_Collection.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        
        # Mostrar todas las historias generadas
        st.markdown("---")
        st.header("📖 Generated Adventure Tales Collection")
        
        for idx, historia in enumerate(st.session_state.historias, 1):
            st.subheader(f"CHAPTER {idx}: {historia['titulo']}")
            st.markdown(f"**Summary:** {historia['resumen']}")
            st.markdown(f"**Theme:** {historia['tema']}")
            st.write(historia['contenido'])
            st.markdown("---")
