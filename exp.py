import streamlit as st
import requests
import json
import time
from docx import Document
from io import BytesIO
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuración de la página
st.set_page_config(
    page_title="Analizador de Novelas de Suspenso Político",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Título de la aplicación
st.title("Analizador de Novelas de Suspenso Político")
st.write("""
Esta aplicación analiza una novela en el género de thriller político.
Sube tu novela en formato `.docx` o `.txt` y recibe un informe detallado de errores y mejoras por escena.
""")

# Barra lateral para opciones de usuario
st.sidebar.header("Configuración de Análisis")
file_upload = st.sidebar.file_uploader("Sube tu novela (.docx o .txt):", type=["docx", "txt"])

# Inicializar el estado de la aplicación
if 'etapa' not in st.session_state:
    st.session_state.etapa = "inicio"  # etapas: inicio, analisis, completado

if 'novela' not in st.session_state:
    st.session_state.novela = ""
if 'informe' not in st.session_state:
    st.session_state.informe = ""

# Función para llamar a la API de OpenRouter con reintentos y parámetros ajustables
def call_openrouter_api(prompt, max_tokens=1500, temperature=0.5, top_p=0.9, top_k=50, repetition_penalty=1.2):
    api_url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p,
        "top_k": top_k,
        "repetition_penalty": repetition_penalty,
        "stop": ["[\"<|eot_id|>\"]"],
        "stream": False
    }
    
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    
    try:
        response = session.post(api_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        response_json = response.json()
        if 'choices' in response_json and len(response_json['choices']) > 0:
            return response_json['choices'][0]['message']['content']
        else:
            st.error("La respuesta de la API no contiene 'choices'.")
            st.write("Respuesta completa de la API:", response_json)
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error en la llamada a la API: {e}")
        return None

# Función para dividir la novela en escenas
def dividir_en_escenas(texto):
    # Suponiendo que las escenas están marcadas con "### Escena X"
    escenas = re.split(r'### Escena \d+', texto)
    # Eliminar elementos vacíos y limpiar
    escenas = [esc.strip() for esc in escenas if esc.strip()]
    return escenas

# Función para analizar una escena
def analizar_escena(escena_num, contenido):
    prompt = f"""
    Analiza la siguiente escena de una novela de suspenso político. Identifica errores gramaticales, de coherencia, desarrollo de personajes y cualquier otro aspecto que pueda mejorar la calidad de la escena. Proporciona recomendaciones claras y específicas para cada área de mejora.

    ### Escena {escena_num}:
    {contenido}

    ### Informe de Análisis:
    """
    analisis = call_openrouter_api(prompt)
    return analisis

# Función para generar el informe completo
def generar_informe(escenas, analisis_por_escena):
    informe = f"# Informe de Análisis de la Novela\n\n"
    total_escenas = len(escenas)
    for i in range(total_escenas):
        informe += f"## Escena {i+1}\n\n"
        informe += f"**Contenido de la Escena:**\n\n{escenas[i]}\n\n"
        informe += f"**Análisis y Recomendaciones:**\n\n{analisis_por_escena[i]}\n\n"
        informe += "---\n\n"
    return informe

# Función para exportar el informe a Word
def exportar_informe_word(informe):
    document = Document()

    # Configurar el tamaño de la página y márgenes
    section = document.sections[0]
    section.page_width = Inches(6)
    section.page_height = Inches(9)
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.7)
    section.right_margin = Inches(0.7)

    # Establecer el estilo normal con una fuente común
    style = document.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'  # Cambiado a una fuente común
    font.size = Pt(12)

    # Agregar el título
    titulo_paragraph = document.add_heading("Informe de Análisis de la Novela", level=0)
    titulo_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

    document.add_page_break()

    # Separar el informe por escenas
    escenas = re.split(r'## Escena \d+', informe)
    escenas = [esc.strip() for esc in escenas if esc.strip()]
    for esc in escenas:
        # Dividir en contenido y análisis
        contenido_match = re.search(r'\*\*Contenido de la Escena:\*\*(.*?)\*\*Análisis y Recomendaciones:\*\*(.*?)(?=---|$)', esc, re.DOTALL)
        if contenido_match:
            contenido = contenido_match.group(1).strip()
            analisis = contenido_match.group(2).strip()

            # Agregar contenido de la escena
            document.add_heading("Contenido de la Escena", level=1)
            document.add_paragraph(contenido)

            # Agregar análisis y recomendaciones
            document.add_heading("Análisis y Recomendaciones", level=1)
            document.add_paragraph(analisis)

            document.add_page_break()

    # Agregar el conteo total de escenas analizadas al final del documento
    total_escenas = len(escenas)
    document.add_heading("Resumen del Análisis", level=1)
    document.add_paragraph(f"**Total de escenas analizadas:** {total_escenas}")

    # Guardar el documento en memoria
    buffer = BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer

# Interfaz de usuario para aprobar la carga y comenzar el análisis
def mostrar_inicio():
    st.header("Carga y Análisis de la Novela")
    if file_upload:
        if file_upload.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            # Leer archivo .docx
            doc = Document(file_upload)
            texto = "\n".join([para.text for para in doc.paragraphs])
        elif file_upload.type == "text/plain":
            # Leer archivo .txt
            texto = file_upload.read().decode("utf-8")
        else:
            st.error("Formato de archivo no soportado.")
            return
        
        if "### Escena" not in texto:
            st.warning("""
            **Advertencia:** No se encontraron marcadores de escenas ("### Escena X") en tu novela.
            Asegúrate de que cada escena esté marcada de la siguiente manera para un análisis correcto:

            ```
            ### Escena 1
            [Contenido de la Escena 1]

            ### Escena 2
            [Contenido de la Escena 2]
            ```
            """)
        
        st.session_state.novela = texto
        st.session_state.etapa = "analisis"

# Interfaz de usuario para mostrar el análisis y generar el informe
def mostrar_analisis():
    st.header("Análisis en Proceso")
    novela = st.session_state.novela

    # Dividir la novela en escenas
    escenas = dividir_en_escenas(novela)
    total_escenas = len(escenas)
    st.write(f"**Total de escenas identificadas:** {total_escenas}")

    if total_escenas == 0:
        st.error("No se pudieron identificar escenas en la novela. Asegúrate de que las escenas estén correctamente marcadas.")
        return

    # Inicializar listas para almacenar análisis
    analisis_por_escena = []

    # Inicializar la barra de progreso
    progress_bar = st.progress(0)
    progress_text = st.empty()
    current = 0

    # Analizar cada escena
    for i, escena in enumerate(escenas):
        escena_num = i + 1
        with st.spinner(f"Analizando Escena {escena_num} de {total_escenas}..."):
            analisis = analizar_escena(escena_num, escena)
            if analisis:
                analisis_por_escena.append(analisis)
            else:
                analisis_por_escena.append("No se pudo generar el análisis para esta escena.")
        # Actualizar la barra de progreso
        current += 1
        progress_bar.progress(current / total_escenas)
        progress_text.text(f"Progreso: {current}/{total_escenas} escenas analizadas.")
        # Retraso para evitar exceder los límites de la API
        time.sleep(1)
    
    # Ocultar la barra de progreso y el texto de progreso
    progress_bar.empty()
    progress_text.empty()

    # Generar el informe completo
    informe = generar_informe(escenas, analisis_por_escena)
    st.session_state.informe = informe
    st.session_state.etapa = "completado"

# Interfaz de usuario para mostrar el informe y opciones de descarga
def mostrar_completado():
    st.header("Informe de Análisis Generado")
    informe = st.session_state.informe
    st.text_area("Informe Detallado:", informe, height=600)

    # Exportar a Word
    doc_buffer = exportar_informe_word(informe)
    st.download_button(
        label="Descargar Informe en Word",
        data=doc_buffer,
        file_name=f"informe_analisis_novela_{int(time.time())}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

    # Opcional: Mostrar resúmenes adicionales
    st.subheader("Resumen General")
    total_escenas = len(re.findall(r'## Escena \d+', informe))
    st.write(f"**Total de escenas analizadas:** {total_escenas}")
    # Puedes agregar más resúmenes o visualizaciones aquí según tus necesidades

# Interfaz de usuario principal
if st.session_state.etapa == "inicio":
    mostrar_inicio()

elif st.session_state.etapa == "analisis":
    mostrar_analisis()

elif st.session_state.etapa == "completado":
    mostrar_completado()

# Manejo de estados adicionales si es necesario
