import streamlit as st
import requests
from docx import Document
from io import BytesIO
import backoff
import re
from difflib import SequenceMatcher
import pandas as pd
from PIL import Image
from docx.shared import Inches

# Definir la cantidad máxima de capítulos
MAX_CAPITULOS = 24
MAX_INTENTOS = 3  # Número máximo de intentos para generar un capítulo único

# Configuración de la página
st.set_page_config(
    page_title="📝 Adventure Tales Generator for Kids",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📝 Adventure Tales Generator for Kids")
st.write("""
Esta aplicación genera hasta 24 capítulos de cuentos de aventuras para niños. El usuario puede seleccionar el rango de edad y proporcionar una Tabla de Contenidos con resúmenes. La aplicación generará cada cuento entre 500 y 700 palabras, incluyendo tres ilustraciones por capítulo.
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

# Prompt personalizado refinado
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
1. **CHAPTER {n}: {Title}**
2. **Summary:** A brief summary of the chapter.
3. **Theme:** The main theme of the chapter.
4. **Illustrations:** Three descriptions for illustrations relevant to the story.
5. **Story Content:** The full story, between 500-700 words.

Each time a speaking character changes, use a line break for clarity.

# Chapter Title Format
Begin the story with "CHAPTER {n}: {Title}", where {n} is the chapter number and {Title} is the story's title.

# Unique Theme Instruction
Each chapter must have a unique theme that has not been used in previous chapters. Refer to the list of used themes below and choose a new, distinct theme for this story. Avoid using similar phrases or titles such as "The Quest for...", "The Mystery of...", or "The Adventure of...".
"""

# Función para extraer el título usando expresiones regulares
def extraer_titulo(respuesta, capitulo_num):
    patron = rf'CHAPTER\s*{capitulo_num}:\s*(.*)'
    match = re.search(patron, respuesta, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None

# Función para extraer el resumen del cuento
def extraer_resumen(respuesta):
    patron = r'Summary:\s*(.*)'
    match = re.search(patron, respuesta, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None

# Función para extraer el tema principal del cuento
def extraer_tema(respuesta):
    patron = r'Theme:\s*(.*)'
    match = re.search(patron, respuesta, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None

# Función para extraer las ilustraciones
def extraer_ilustraciones(respuesta):
    patron = r'Illustrations:\s*((?:.|\n)*?)\n{2,}'
    match = re.search(patron, respuesta, re.IGNORECASE)
    if match:
        ilustraciones_texto = match.group(1).strip()
        ilustraciones = re.findall(r'\d+\.\s*(.*)', ilustraciones_texto)
        return ilustraciones if len(ilustraciones) == 3 else None
    return None

# Función con reintentos para generar un capítulo
@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=3)
def generar_capitulo(capitulo_num, titulo, resumen, rango_edad):
    """
    Genera un capítulo completo incluyendo título, resumen, contenido, tema e ilustraciones.
    
    Args:
        capitulo_num (int): Número del capítulo.
        titulo (str): Título proporcionado para el capítulo.
        resumen (str): Resumen proporcionado para el capítulo.
        rango_edad (str): Rango de edad seleccionado.
    
    Returns:
        tuple: (titulo_generado, resumen_generado, contenido, tema_generado, ilustraciones_generadas)
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

    mensaje = (
        f"{prompt}\n\n"
        f"CHAPTER {capitulo_num}: {titulo}\n"
        f"Summary: {resumen}\n"
        f"Story Content:"
    )

    data = {
        "model": "openai/gpt-4",
        "messages": [
            {
                "role": "user",
                "content": mensaje
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        respuesta = response.json()
        if 'choices' in respuesta and len(respuesta['choices']) > 0:
            contenido_completo = respuesta['choices'][0]['message']['content']
            titulo_generado = extraer_titulo(contenido_completo, capitulo_num)
            resumen_generado = extraer_resumen(contenido_completo)
            tema_generado = extraer_tema(contenido_completo)
            ilustraciones_generadas = extraer_ilustraciones(contenido_completo)
            # Extraer el contenido sin el título, resumen, tema e ilustraciones
            contenido = contenido_completo
            if titulo_generado:
                contenido = contenido.replace(f"CHAPTER {capitulo_num}: {titulo_generado}", "", 1)
            if resumen_generado:
                contenido = contenido.replace(f"Summary: {resumen_generado}", "", 1)
            if tema_generado:
                contenido = contenido.replace(f"Theme: {tema_generado}", "", 1)
            if ilustraciones_generadas:
                contenido = contenido.replace("Illustrations:", "", 1)
                for idx, ilustracion in enumerate(ilustraciones_generadas, 1):
                    contenido = contenido.replace(f"{idx}. {ilustracion}", "", 1)
            contenido = contenido.strip()
            return titulo_generado, resumen_generado, contenido, tema_generado, ilustraciones_generadas
        else:
            st.error(f"Unexpected API response when generating Chapter {capitulo_num}.")
            return None, None, None, None, None
    except requests.exceptions.RequestException as e:
        st.error(f"Error al generar el capítulo {capitulo_num}: {e}")
        return None, None, None, None, None

# Función para generar una ilustración usando la API de Together
def generar_ilustracion(descripcion):
    """
    Genera una ilustración basada en la descripción proporcionada utilizando la API de Together.
    
    Args:
        descripcion (str): Descripción de la ilustración.
    
    Returns:
        Image: Objeto PIL Image de la ilustración generada.
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

# Función para crear el documento Word con tabla de contenidos, capítulos e ilustraciones
def crear_documento(capitulos_list, titulo):
    """
    Crea un documento Word que incluye la tabla de contenidos y los capítulos con sus ilustraciones.
    
    Args:
        capitulos_list (list): Lista de capítulos generados.
        titulo (str): Título de la obra.
    
    Returns:
        BytesIO: Buffer del documento Word generado.
    """
    doc = Document()
    doc.add_heading(titulo, 0)
    
    # Crear Tabla de Contenidos
    doc.add_heading("Table of Contents", level=1)
    for idx, (titulo_capitulo, resumen_capitulo, _, _, _) in enumerate(capitulos_list, 1):
        toc_entry = f"CHAPTER {idx}: {titulo_capitulo}"
        toc_summary = f"Summary: {resumen_capitulo}"
        doc.add_paragraph(toc_entry, style='List Number')
        doc.add_paragraph(toc_summary, style='List Bullet')
    
    doc.add_page_break()
    
    # Agregar cada capítulo con ilustraciones
    for idx, (titulo_capitulo, resumen_capitulo, capitulo, tema, ilustraciones) in enumerate(capitulos_list, 1):
        doc.add_heading(f"CHAPTER {idx}: {titulo_capitulo}", level=1)
        doc.add_paragraph(capitulo)
        
        # Agregar ilustraciones
        if ilustraciones:
            doc.add_heading("Illustrations", level=2)
            for ilustracion_num, descripcion in enumerate(ilustraciones, 1):
                imagen = generar_ilustracion(descripcion)
                if imagen:
                    # Convertir PIL Image a BytesIO
                    imagen_buffer = BytesIO()
                    imagen.save(imagen_buffer, format='PNG')
                    imagen_buffer.seek(0)
                    
                    doc.add_paragraph(f"Illustration {ilustracion_num}: {descripcion}")
                    doc.add_picture(imagen_buffer, width=Inches(6))
                else:
                    doc.add_paragraph(f"Illustration {ilustracion_num}: {descripcion} (Image not available)")
        
        doc.add_page_break()
    
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# Función para crear un DataFrame de la Tabla de Contenidos con Resúmenes
def crear_tabla_contenidos(capitulos_list):
    data = {
        "Chapter": [f"CHAPTER {idx}" for idx in range(1, len(capitulos_list)+1)],
        "Title": [capitulo[0] for capitulo in capitulos_list],
        "Summary": [capitulo[1] for capitulo in capitulos_list]
    }
    df = pd.DataFrame(data)
    return df

# Interfaz de usuario para subir un archivo CSV o ingresar manualmente
st.sidebar.title("Options")

opciones_disponibles = ["Upload CSV File", "Manual Input"]
opcion = st.sidebar.radio("How would you like to provide the Table of Contents?", opciones_disponibles)

# Agregar selección de rango de edad en la barra lateral
rangos_edades = ["7-9 años", "9-12 años", "12-15 años"]
rango_edad = st.sidebar.selectbox("Selecciona el rango de edad para las historias:", rangos_edades)

mostrar_formulario = False
if opcion == "Upload CSV File":
    archivo = st.sidebar.file_uploader("Upload a CSV file with columns: Chapter, Title, Summary", type=["csv"])
    if archivo:
        try:
            df = pd.read_csv(archivo)
            if not all(col in df.columns for col in ["Chapter", "Title", "Summary"]):
                st.error("El archivo CSV debe contener las columnas: Chapter, Title, Summary")
            else:
                st.session_state.capitulos_input = df
                mostrar_formulario = True
        except Exception as e:
            st.error(f"Error reading the CSV file: {e}")
else:
    mostrar_formulario = True

if opcion == "Manual Input" or (opcion == "Upload CSV File" and 'capitulos_input' in st.session_state):
    with st.form(key='form_cuento_infantil'):
        if opcion == "Manual Input":
            num_capitulos_input = st.number_input(
                "Número de capítulos a generar:",
                min_value=1,
                max_value=MAX_CAPITULOS,
                value=3
            )
            capitulos_manual = []
            for i in range(1, num_capitulos_input + 1):
                st.markdown(f"### Chapter {i}")
                titulo = st.text_input(f"Title for Chapter {i}", key=f"title_{i}")
                resumen = st.text_area(f"Summary for Chapter {i}", key=f"summary_{i}", height=100)
                capitulos_manual.append({"Chapter": f"CHAPTER {i}", "Title": titulo, "Summary": resumen})
        else:
            df = st.session_state.capitulos_input
            capitulos_manual = df.to_dict('records')
        
        submit_button = st.form_submit_button(label='Generate Adventure Tales')

    if submit_button:
        if opcion == "Manual Input":
            capitulos = capitulos_manual
            if any(not cap['Title'] or not cap['Summary'] for cap in capitulos):
                st.error("Por favor, asegúrate de que todos los capítulos tengan un título y un resumen.")
            else:
                st.session_state.capitulos_input = pd.DataFrame(capitulos)
        else:
            capitulos = capitulos_manual
        
        st.success("Starting the generation of adventure tales...")
        st.session_state.proceso_generado = True
        progreso = st.progress(0)
        
        capitulos_generados_ejecucion = 0
        total_capitulos = len(capitulos)
        
        for idx, capitulo in enumerate(capitulos, 1):
            titulo_input = capitulo["Title"]
            resumen_input = capitulo["Summary"]
            st.write(f"Generating **CHAPTER {idx}: {titulo_input}**...")
            titulo_generado, resumen_generado, contenido, tema_generado, ilustraciones_generadas = generar_capitulo(idx, titulo_input, resumen_input, rango_edad)
            if contenido and tema_generado and ilustraciones_generadas:
                # Verificar similitud con temas existentes
                repetido = False
                for tema in st.session_state.temas_utilizados:
                    if similar(tema_generado, tema) > 0.7:
                        repetido = True
                        break
                if not repetido:
                    st.session_state.capitulos.append((titulo_generado, resumen_generado, contenido, tema_generado, ilustraciones_generadas))
                    st.session_state.temas_utilizados.append(tema_generado)
                    capitulos_generados_ejecucion += 1
                else:
                    st.warning(f"The theme '{tema_generado}' is too similar to an existing theme. Attempting to generate a new chapter...")
                    # Intentar re-generar el capítulo hasta MAX_INTENTOS
                    intentos = 1
                    while intentos < MAX_INTENTOS:
                        titulo_generado_new, resumen_generado_new, contenido_new, tema_generado_new, ilustraciones_generadas_new = generar_capitulo(idx, titulo_input, resumen_input, rango_edad)
                        if contenido_new and tema_generado_new and ilustraciones_generadas_new:
                            similaridad = False
                            for tema in st.session_state.temas_utilizados:
                                if similar(tema_generado_new, tema) > 0.7:
                                    similaridad = True
                                    break
                            if not similaridad:
                                st.session_state.capitulos.append((titulo_generado_new, resumen_generado_new, contenido_new, tema_generado_new, ilustraciones_generadas_new))
                                st.session_state.temas_utilizados.append(tema_generado_new)
                                capitulos_generados_ejecucion += 1
                                break
                            else:
                                intentos += 1
                                st.warning(f"Attempt {intentos}: The new theme '{tema_generado_new}' is still too similar to existing themes.")
                        else:
                            intentos += 1
                            st.warning(f"Attempt {intentos}: Could not generate a valid chapter.")
                    if intentos == MAX_INTENTOS:
                        st.error("Could not generate a chapter with a unique theme after multiple attempts.")
                        break
            else:
                st.error("Generation of tales has been stopped due to an error.")
                break
            progreso.progress(capitulos_generados_ejecucion / total_capitulos)
        
        progreso.empty()
        
        if capitulos_generados_ejecucion == total_capitulos:
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
        else:
            st.info(f"Generation interrupted. You have generated {capitulos_generados_ejecucion} out of {total_capitulos} chapters.")

# Mostrar los capítulos generados
if st.session_state.capitulos and st.session_state.proceso_generado:
    st.markdown("---")
    st.header("📖 Generated Adventure Tales")
    
    # Mostrar Tabla de Contenidos
    st.subheader("Table of Contents")
    for idx, (titulo_capitulo, resumen_capitulo, _, _, _) in enumerate(st.session_state.capitulos, 1):
        st.markdown(f"**CHAPTER {idx}: {titulo_capitulo}**")
        st.markdown(f"*Summary:* {resumen_capitulo}")
        st.markdown("---")
    
    # Mostrar cada capítulo con ilustraciones
    for idx, (titulo_capitulo, resumen_capitulo, capitulo, tema, ilustraciones) in enumerate(st.session_state.capitulos, 1):
        st.markdown(f"### CHAPTER {idx}: {titulo_capitulo}")
        st.write(capitulo)
        if ilustraciones:
            st.subheader("📷 Illustrations")
            for ilustracion_num, descripcion in enumerate(ilustraciones, 1):
                imagen = generar_ilustracion(descripcion)
                if imagen:
                    st.image(imagen, caption=f"Illustration {ilustracion_num}: {descripcion}", use_column_width=True)
                else:
                    st.write(f"**Illustration {ilustracion_num}:** {descripcion} (Image not available)")
        st.markdown("---")
