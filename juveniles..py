import streamlit as st
import requests
from docx import Document
from io import BytesIO
import backoff
import re
from difflib import SequenceMatcher

# Definir la cantidad máxima de capítulos
MAX_CAPITULOS = 24

# Configuración de la página
st.set_page_config(
    page_title="📝 Generador de Cuentos de Aventuras para Niños (9-12 años)",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📝 Generador de Cuentos de Aventuras para Niños (9-12 años)")
st.write("""
Esta aplicación genera hasta 24 capítulos de cuentos de aventuras para niños de 9 a 12 años en inglés.
Cada capítulo presenta una aventura independiente con personajes únicos y escenarios imaginativos.
Cada capítulo comienza con la palabra "CHAPTER".
""")

# Inicializar estado de la sesión
if 'capitulos' not in st.session_state:
    st.session_state.capitulos = []
if 'titulo_obra' not in st.session_state:
    st.session_state.titulo_obra = "Adventure Tales"
if 'proceso_generado' not in st.session_state:
    st.session_state.proceso_generado = False
if 'num_capitulos' not in st.session_state:
    st.session_state.num_capitulos = 1
if 'temas_utilizados' not in st.session_state:
    st.session_state.temas_utilizados = []

# Función para medir la similitud entre dos textos
def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

# Prompt personalizado refinado
PROMPT_BASE = """
Write an adventure story intended for boys and girls aged between 9 and 12 years. The story should be exciting and age-appropriate, including elements such as challenges, brave characters, and imaginative settings. Ensure the content is entertaining, but also safe and suitable for children. Include an interesting conflict and a resolution that leaves a positive message.

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
The output should be a story written in well-formed paragraphs, with a continuous narrative flow and clear dialogue when necessary. Each time a speaking character changes, use a line break for clarity.

# Chapter Title Format
Begin the story with "CHAPTER {n}: {Title}", where {n} is the chapter number and {Title} is the story's title.

# Unique Theme Instruction
Each chapter must have a unique theme that has not been used in previous chapters. Refer to the list of used themes below and choose a new, distinct theme for this story. Avoid using similar phrases or titles such as "The Quest for...", "The Mystery of...", or "The Adventure of...".
"""

# Función para extraer el título usando expresiones regulares
def extraer_titulo(respuesta, capitulo_num):
    # Buscamos "CHAPTER {n}: Título"
    patron = rf'CHAPTER\s*{capitulo_num}:\s*(.*)'
    match = re.search(patron, respuesta, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "Title Not Found"

# Función para extraer el tema principal del cuento
def extraer_tema(respuesta):
    # Suponiendo que el modelo incluye una oración final con el mensaje o tema
    # Ejemplo: "The true treasure was the knowledge and friendship they gained."
    # Intentamos capturar la última oración que no sea "**Fin**"
    lines = respuesta.strip().split('\n')
    for line in reversed(lines):
        if line.strip().lower() != "**fin**":
            # Dividir en oraciones y tomar la última
            oraciones = re.split(r'[.!?]', line)
            if oraciones:
                return oraciones[-1].strip()
    return "Unique Theme Not Found"

# Función con reintentos para generar un capítulo
@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=3)
def generar_capitulo(capitulo_num):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}"
    }

    # Seleccionar el modelo según la solicitud del usuario
    modelo = "openai/gpt-4o-mini"  # Modelo solicitado por el usuario

    # Construir el prompt incluyendo la lista de temas utilizados
    temas_utilizados = st.session_state.temas_utilizados
    if temas_utilizados:
        temas_formateados = "; ".join(temas_utilizados)
        prompt = PROMPT_BASE.replace("Refer to the list of used themes below and choose a new, distinct theme for this story.",
                                    f"Refer to the list of used themes below and choose a new, distinct theme for this story.\n\nUsed Themes: {temas_formateados}")
    else:
        prompt = PROMPT_BASE.replace("Refer to the list of used themes below and choose a new, distinct theme for this story.",
                                    "Refer to the list of used themes below and choose a new, distinct theme for this story.\n\nUsed Themes: None")

    mensaje = (
        f"{prompt}\n\n"
        f"CHAPTER {capitulo_num}:"
    )

    data = {
        "model": modelo,
        "messages": [
            {
                "role": "user",
                "content": mensaje
            }
        ]
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    respuesta = response.json()
    if 'choices' in respuesta and len(respuesta['choices']) > 0:
        contenido_completo = respuesta['choices'][0]['message']['content']
        titulo_capitulo = extraer_titulo(contenido_completo, capitulo_num)
        # Extraer el contenido sin el título
        contenido = contenido_completo.replace(f"CHAPTER {capitulo_num}: {titulo_capitulo}", "").strip()
        # Extraer el tema del cuento
        tema_capitulo = extraer_tema(contenido_completo)
        return titulo_capitulo, contenido, tema_capitulo
    else:
        st.error(f"Unexpected API response when generating Chapter {capitulo_num}.")
        return None, None, None

# Función para crear el documento Word con títulos
def crear_documento(capitulos_list, titulo):
    doc = Document()
    doc.add_heading(titulo, 0)
    for idx, (titulo_capitulo, capitulo) in enumerate(capitulos_list, 1):
        doc.add_heading(f"CHAPTER {idx}: {titulo_capitulo}", level=1)
        doc.add_paragraph(capitulo)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# Interfaz de usuario para seleccionar opción
st.sidebar.title("Options")

# Determinar las opciones disponibles en la barra lateral
opciones_disponibles = []
if len(st.session_state.capitulos) < MAX_CAPITULOS and st.session_state.capitulos:
    opciones_disponibles = ["Continue Generating", "Start New Generation"]
else:
    opciones_disponibles = ["Start New Generation"]

# Radio buttons sin necesidad de botón de envío
opcion = st.sidebar.radio("What would you like to do?", opciones_disponibles)

mostrar_formulario = False
if opcion == "Start New Generation":
    # Limpiar el estado de la sesión
    st.session_state.capitulos = []
    st.session_state.titulo_obra = "Adventure Tales"
    st.session_state.proceso_generado = False
    st.session_state.num_capitulos = 1
    st.session_state.temas_utilizados = []
    mostrar_formulario = True
elif opcion == "Continue Generating":
    if len(st.session_state.capitulos) >= MAX_CAPITULOS:
        st.sidebar.info(f"You have reached the maximum limit of {MAX_CAPITULOS} chapters.")
    else:
        mostrar_formulario = True

if mostrar_formulario:
    with st.form(key='form_cuento_infantil'):
        if opcion == "Start New Generation":
            st.session_state.num_capitulos = st.number_input(
                "Number of chapters to generate:",
                min_value=1,
                max_value=MAX_CAPITULOS,
                value=3
            )
        else:
            historias_generadas = len(st.session_state.capitulos)
            historias_restantes = MAX_CAPITULOS - historias_generadas
            st.session_state.num_capitulos = st.number_input(
                "Number of chapters to generate:",
                min_value=1,
                max_value=historias_restantes,
                value=min(3, historias_restantes)
            )
        
        submit_button = st.form_submit_button(label='Generate Adventure Tales')

    if submit_button:
        st.success("Starting the generation of adventure tales...")
        st.session_state.proceso_generado = True
        progreso = st.progress(0)
        
        inicio = len(st.session_state.capitulos) + 1
        fin = inicio + st.session_state.num_capitulos - 1
        if fin > MAX_CAPITULOS:
            fin = MAX_CAPITULOS
        capitulos_generados_ejecucion = 0
        
        for i in range(inicio, fin + 1):
            st.write(f"Generating **CHAPTER {i}**...")
            titulo_capitulo, capitulo, tema_capitulo = generar_capitulo(i)
            if capitulo and tema_capitulo and tema_capitulo not in st.session_state.temas_utilizados:
                st.session_state.capitulos.append((titulo_capitulo, capitulo))
                st.session_state.temas_utilizados.append(tema_capitulo)
                capitulos_generados_ejecucion += 1
            else:
                st.error("Generation of tales has been stopped due to an error or a repeated theme.")
                break
            progreso.progress(capitulos_generados_ejecucion / st.session_state.num_capitulos)
            # time.sleep(1)  # Removed to improve speed
        
        progreso.empty()
        
        if capitulos_generados_ejecucion == st.session_state.num_capitulos:
            st.success(f"Successfully generated {capitulos_generados_ejecucion} chapters.")
            st.session_state.titulo_obra = st.text_input("Title of the adventure tales:", value=st.session_state.titulo_obra)
            if st.session_state.titulo_obra:
                documento = crear_documento(st.session_state.capitulos, st.session_state.titulo_obra)
                st.download_button(
                    label="Download Tales in Word",
                    data=documento,
                    file_name="adventure_tales.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                # Optional: Add PDF download
                # documento_pdf = crear_pdf(st.session_state.capitulos, st.session_state.titulo_obra)
                # st.download_button(
                #     label="Download Tales in PDF",
                #     data=documento_pdf,
                #     file_name="adventure_tales.pdf",
                #     mime="application/pdf"
                # )
        else:
            st.info(f"Generation interrupted. You have generated {capitulos_generados_ejecucion} out of {st.session_state.num_capitulos} chapters.")

# Mostrar los capítulos generados
if st.session_state.capitulos and st.session_state.proceso_generado:
    st.markdown("---")
    st.header("📖 Generated Adventure Tales")
    for idx, (titulo_capitulo, capitulo) in enumerate(st.session_state.capitulos, 1):
        st.subheader(f"CHAPTER {idx}: {titulo_capitulo}")
        st.write(capitulo)
