import streamlit as st
import requests
import json
from docx import Document
from io import BytesIO
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from docx.shared import Inches, Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from datetime import datetime

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

# Estado de la aplicación
if 'etapa' not in st.session_state:
    st.session_state.etapa = "inicio"
if 'novela' not in st.session_state:
    st.session_state.novela = ""
if 'informe' not in st.session_state:
    st.session_state.informe = ""

def call_openrouter_api(prompt, max_tokens=3000):
    api_url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens
    }
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    try:
        response = session.post(api_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        response_json = response.json()
        return response_json['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        st.error(f"Error en la llamada a la API: {e}")
        return None

def leer_archivo(file):
    try:
        if file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(file)
            texto = "\n".join([para.text for para in doc.paragraphs])
        elif file.type == "text/plain":
            texto = file.read().decode("utf-8")
        else:
            st.error("Formato de archivo no soportado.")
            return None
        return texto
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        return None

def dividir_en_escenas(texto):
    escenas = texto.split('\n\n')
    escenas = [escena.strip() for escena in escenas if escena.strip()]
    return escenas

def analizar_novela(texto):
    escenas = dividir_en_escenas(texto)
    mejoras_por_escena = []

    for idx, escena in enumerate(escenas, start=1):
        prompt = f"""
        Por favor, analiza la siguiente escena de una novela de suspenso político. Identifica errores gramaticales, de coherencia, desarrollo de personajes, ritmo y cualquier otro aspecto que pueda mejorar la calidad de la escena. Proporciona recomendaciones claras y específicas para cada área de mejora. Responde en formato JSON con las siguientes claves: "escena", "issues", "suggestions".
        
        Escena {idx}:
        {escena}
        
        ### Informe de Análisis:
        """
        analisis = call_openrouter_api(prompt)
        if analisis:
            try:
                analisis_json = json.loads(analisis)
                mejoras_por_escena.append({
                    "escena": analisis_json.get("escena", f"Escena {idx}"),
                    "issues": analisis_json.get("issues", "No se identificaron problemas específicos."),
                    "suggestions": analisis_json.get("suggestions", "No se proporcionaron sugerencias específicas.")
                })
            except json.JSONDecodeError:
                st.error(f"Error al decodificar la respuesta JSON para la Escena {idx}.")
                continue
        else:
            st.error(f"No se pudo obtener análisis para la Escena {idx}.")

    prompt_global = f"""
    Proporciona un análisis global de la novela basada en las mejoras específicas de cada escena y asigna una calificación de 1 a 10 puntos.
    
    Mejoras por Escena:
    {json.dumps(mejoras_por_escena, ensure_ascii=False)}
    """
    return call_openrouter_api(prompt_global)

def generar_informe(analisis):
    try:
        analisis_json = json.loads(analisis)
        calificacion = analisis_json.get('calificacion', 'No disponible')
        errores = analisis_json.get('errores', 'No se identificaron errores.')
        recomendaciones = analisis_json.get('recomendaciones', 'No se proporcionaron recomendaciones.')
        mejoras_por_escena = analisis_json.get('mejoras_por_escena', [])

        informe = f"# Informe de Análisis de la Novela\n\n"
        informe += f"**Calificación General:** {calificacion} / 10\n\n"
        informe += f"**Errores Identificados:**\n{errores}\n\n"
        informe += f"**Recomendaciones para Mejoras:**\n{recomendaciones}\n\n"
        informe += f"## Mejoras Específicas por Escena\n\n"
        
        for mejora in mejoras_por_escena:
            informe += f"Escena {mejora['escena']}\n\n"
            informe += f"**Problemas Identificados:** {mejora['issues']}\n\n"
            informe += f"**Sugerencias de Mejora:** {mejora['suggestions']}\n\n"
        
        return informe
    except json.JSONDecodeError:
        return f"# Informe de Análisis de la Novela\n\nCalificación General: No disponible\n\nErrores y Recomendaciones:\n{analisis}\n\n"

def exportar_informe_word(informe):
    document = Document()
    section = document.sections[0]
    section.page_width = Inches(8.27)
    section.page_height = Inches(11.69)
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)

    style = document.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)

    titulo_paragraph = document.add_heading("Informe de Análisis de la Novela", level=1)
    titulo_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

    for line in informe.split('\n'):
        if line.startswith("# "):
            document.add_heading(line.replace("# ", ""), level=2)
        elif line.startswith("## "):
            document.add_heading(line.replace("## ", ""), level=3)
        elif line.startswith("Escena"):
            document.add_heading(line, level=3)
        elif line.startswith("**"):
            match = re.match(r'\*\*(.*?)\*\*:\s*(.*)', line)
            if match:
                term, desc = match.groups()
                p = document.add_paragraph()
                p.add_run(f"{term}: ").bold = True
                p.add_run(desc)
        else:
            if line.strip():
                document.add_paragraph(line)

    buffer = BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer

def mostrar_inicio():
    st.header("Carga y Análisis de la Novela")
    if file_upload:
        texto = leer_archivo(file_upload)
        if texto:
            st.session_state.novela = texto
            st.session_state.etapa = "analisis"

def mostrar_analisis():
    st.header("Análisis en Proceso")
    enviar = st.button("Enviar")

    if enviar:
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            status_text.text("Iniciando el análisis de la novela...")
            progress_bar.progress(10)
            analisis = analizar_novela(st.session_state.novela)
            progress_bar.progress(50)

            status_text.text("Generando el informe...")
            informe = generar_informe(analisis)
            progress_bar.progress(80)

            st.session_state.informe = informe
            st.session_state.etapa = "completado"
            progress_bar.progress(100)
            status_text.text("Análisis completado exitosamente.")
        except Exception as e:
            st.error(f"Ocurrió un error durante el análisis: {e}")
            progress_bar.progress(0)

def mostrar_completado():
    st.header("Informe de Análisis Generado")
    st.markdown(st.session_state.informe)

    doc_buffer = exportar_informe_word(st.session_state.informe)
    st.download_button(
        label="Descargar Informe en Word",
        data=doc_buffer,
        file_name=f"informe_analisis_novela_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

if st.session_state.etapa == "inicio":
    mostrar_inicio()
elif st.session_state.etapa == "analisis":
    mostrar_analisis()
elif st.session_state.etapa == "completado":
    mostrar_completado()
