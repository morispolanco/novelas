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
Sube tu novela en formato `.docx` o `.txt` y recibe un informe detallado de errores y mejoras, además de una calificación global.
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
def call_openrouter_api(prompt, max_tokens=3000, temperature=0.5, top_p=0.9, top_k=50, repetition_penalty=1.2):
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

# Función para leer el contenido del archivo subido
def leer_archivo(file):
    if file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        # Leer archivo .docx
        doc = Document(file)
        texto = "\n".join([para.text for para in doc.paragraphs])
    elif file.type == "text/plain":
        # Leer archivo .txt
        texto = file.read().decode("utf-8")
    else:
        st.error("Formato de archivo no soportado.")
        return None
    return texto

# Función para analizar la novela completa
def analizar_novela(texto):
    prompt = f"""
    Analiza la siguiente novela de suspenso político de manera global. Identifica errores gramaticales, de coherencia, desarrollo de personajes, ritmo y cualquier otro aspecto que pueda mejorar la calidad de la novela. Proporciona recomendaciones claras y específicas para cada área de mejora y asigna una calificación de 1 a 10 puntos basada en la calidad general de la novela.
    
    ### Novela:
    {texto}
    
    ### Informe de Análisis:
    """
    analisis = call_openrouter_api(prompt)
    return analisis

# Función para generar el informe completo
def generar_informe(analisis):
    informe = f"# Informe de Análisis de la Novela\n\n"
    informe += f"**Calificación General:** {analisis.get('calificacion', 'No disponible')} / 10\n\n"
    informe += f"**Errores Identificados:**\n{analisis.get('errores', 'No se identificaron errores.')}\n\n"
    informe += f"**Recomendaciones para Mejoras:**\n{analisis.get('recomendaciones', 'No se proporcionaron recomendaciones.')}\n\n"
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

    # Agregar el contenido del informe
    for line in informe.split('\n'):
        if line.startswith("# "):
            # Títulos
            document.add_heading(line.replace("# ", ""), level=1)
        elif line.startswith("## "):
            # Subtítulos
            document.add_heading(line.replace("## ", ""), level=2)
        elif line.startswith("**"):
            # Negritas
            match = re.match(r'\*\*(.*?)\*\*:\s*(.*)', line)
            if match:
                term, desc = match.groups()
                p = document.add_paragraph()
                p.add_run(f"{term}: ").bold = True
                p.add_run(desc)
        else:
            # Párrafos normales
            if line.strip() != "":
                document.add_paragraph(line)

    # Guardar el documento en memoria
    buffer = BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer

# Interfaz de usuario para aprobar la carga y comenzar el análisis
def mostrar_inicio():
    st.header("Carga y Análisis de la Novela")
    if file_upload:
        texto = leer_archivo(file_upload)
        if texto:
            if "### Escena" not in texto and file_upload.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                st.warning("""
                **Advertencia:** No se encontraron marcadores de escenas ("### Escena X") en tu novela.
                Para un análisis global, no es necesario marcar las escenas, pero es recomendable revisar el formato de tu archivo.
                """)
            st.session_state.novela = texto
            st.session_state.etapa = "analisis"

# Interfaz de usuario para mostrar el análisis y generar el informe
def mostrar_analisis():
    st.header("Análisis en Proceso")
    novela = st.session_state.novela

    # Mostrar un extracto de la novela para confirmar
    st.subheader("Extracto de la Novela:")
    st.text_area("Contenido de la Novela:", novela[:1000] + "..." if len(novela) > 1000 else novela, height=200)

    # Botón para iniciar el análisis
    if st.button("Iniciar Análisis"):
        with st.spinner("Analizando la novela..."):
            analisis = analizar_novela(novela)
            if analisis:
                # Asumiendo que la respuesta de la API incluye un JSON con 'calificacion', 'errores' y 'recomendaciones'
                # Dependiendo de cómo OpenRouter formatee la respuesta, puede que necesites ajustar esto
                # Aquí, simplemente almacenaremos el análisis completo
                st.session_state.informe = analisis
                st.session_state.etapa = "completado"
            else:
                st.error("No se pudo generar el análisis. Por favor, intenta nuevamente.")

# Interfaz de usuario para mostrar el informe y opciones de descarga
def mostrar_completado():
    st.header("Informe de Análisis Generado")
    informe = st.session_state.informe

    # Mostrar el informe en la interfaz
    st.subheader("Informe Detallado:")
    st.text_area("Informe:", informe, height=600)

    # Exportar a Word
    doc_buffer = exportar_informe_word(informe)
    st.download_button(
        label="Descargar Informe en Word",
        data=doc_buffer,
        file_name=f"informe_analisis_novela_{int(time.time())}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

# Interfaz de usuario principal
if st.session_state.etapa == "inicio":
    mostrar_inicio()

elif st.session_state.etapa == "analisis":
    mostrar_analisis()

elif st.session_state.etapa == "completado":
    mostrar_completado()

# Manejo de estados adicionales si es necesario
