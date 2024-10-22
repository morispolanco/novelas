import streamlit as st
import requests
from io import BytesIO
import re
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import json

# =====================
# Configuración Inicial
# =====================

OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "anthropic/claude-3.5-sonnet:beta"  # Asegúrate de que este es el nombre correcto del modelo

# =====================
# Funciones Auxiliares
# =====================

def generar_contenido(prompt, max_tokens=5000, temperature=0.7, repetition_penalty=1.2, frequency_penalty=0.5):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}"
    }
    data = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "repetition_penalty": repetition_penalty,
        "frequency_penalty": frequency_penalty
    }
    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=120)  # Aumentar timeout si es necesario
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.Timeout:
        st.error("La solicitud a la API de OpenRouter ha excedido el tiempo de espera.")
        return ""
    except requests.exceptions.ConnectionError:
        st.error("Error de conexión al intentar comunicarse con la API de OpenRouter.")
        return ""
    except requests.exceptions.HTTPError as e:
        st.error(f"Error HTTP de la API de OpenRouter: {e.response.status_code} - {e.response.text}")
        return ""
    except (KeyError, IndexError) as e:
        st.error("Respuesta inesperada de la API de OpenRouter.")
        st.error(str(e))
        return ""
    except Exception as e:
        st.error(f"Ocurrió un error inesperado: {e}")
        return ""

def exportar_a_docx(contenido_novela, titulo="Novela Mejorada"):
    doc = Document()
    try:
        # Configuración de la página
        sections = doc.sections
        for section in sections:
            section.page_width = Inches(6)
            section.page_height = Inches(9)
            section.top_margin = Inches(0.75)
            section.bottom_margin = Inches(0.75)
            section.left_margin = Inches(0.75)
            section.right_margin = Inches(0.75)

        # Configuración de la fuente predeterminada a Alegreya, tamaño 12
        style_normal = doc.styles['Normal']
        font_normal = style_normal.font
        font_normal.name = 'Alegreya'
        font_normal.size = Pt(12)
        style_normal.element.rPr.rFonts.set(qn('w:eastAsia'), 'Alegreya')

        # Configurar fuentes para los estilos de encabezado
        for heading in ['Heading 1', 'Heading 2', 'Heading 3']:
            style_heading = doc.styles[heading]
            font_heading = style_heading.font
            font_heading.name = 'Alegreya'
            font_heading.size = Pt(14)
            style_heading.element.rPr.rFonts.set(qn('w:eastAsia'), 'Alegreya')

        # Título de la novela
        doc.add_heading(titulo, level=1).alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph("\n")  # Espacio después del título

        # Procesar el contenido
        for linea in contenido_novela.split('\n'):
            linea = linea.strip()
            if not linea:
                continue

            if re.match(r"^Capítulo\s+\d+", linea, re.IGNORECASE):
                p = doc.add_heading(linea, level=2)
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                p.paragraph_format.line_spacing = 1.15
                p.paragraph_format.space_after = Pt(6)
            else:
                p = doc.add_paragraph(linea, style='Normal')
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                p.paragraph_format.line_spacing = 1.15
                p.paragraph_format.space_after = Pt(6)

        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer

def leer_docx(file):
    try:
        doc = Document(file)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)
    except Exception as e:
        st.error(f"Error al leer el archivo DOCX: {e}")
        return ""

# =====================
# Cacheo de Funciones
# =====================

@st.cache_data(show_spinner=False, ttl=3600)
def generar_contenido_cache(prompt, max_tokens=5000, temperature=0.7, repetition_penalty=1.2, frequency_penalty=0.5):
    return generar_contenido(prompt, max_tokens, temperature, repetition_penalty, frequency_penalty)

# =====================
# Validación de Entrada
# =====================

def validar_correcciones(correcciones):
    if not correcciones:
        return False, "Las correcciones y mejoras no pueden estar vacías."
    if len(correcciones) < 10:
        return False, "Las correcciones y mejoras son demasiado cortas. Por favor, proporciona más detalles."
    if len(correcciones) > 2000:
        return False, "Las correcciones y mejoras son demasiado largas. Por favor, proporciona una descripción más concisa."
    return True, ""

# =====================
# Inicialización de Variables de Sesión
# =====================

if 'novela_mejorada' not in st.session_state:
    st.session_state.novela_mejorada = False  # Bandera para evitar reprocesamiento

# =====================
# Interfaz de Usuario
# =====================

st.set_page_config(page_title="Mejorar tu Novela", layout="wide")

# Título principal
st.title("Mejorar tu Novela")

# ============================================
# Sección: Mejorar una Novela Subida por el Usuario
# ============================================

st.header("Mejorar tu Novela")

# Paso 1: Subir el archivo DOCX
st.subheader("Paso 1: Sube tu Novela en Formato DOCX")
archivo_subido = st.file_uploader("Selecciona tu archivo DOCX:", type=["docx"])

# Paso 2: Especificar las Correcciones y Mejoras
st.subheader("Paso 2: Especifica las Correcciones y Mejoras")
correcciones = st.text_area("Describe los defectos que has identificado en tu novela y las mejoras que deseas aplicar:", height=200)

# Botón para iniciar la mejora
if st.button("Aplicar Correcciones y Mejoras", key="aplicar_mejoras"):
    if not archivo_subido:
        st.error("Por favor, sube un archivo DOCX para poder proceder.")
    else:
        correcciones_validas, mensaje_error = validar_correcciones(correcciones)
        if not correcciones_validas:
            st.error(mensaje_error)
        else:
            with st.spinner("Procesando tu novela y aplicando las correcciones y mejoras..."):
                # Leer el contenido del archivo DOCX
                contenido_novela = leer_docx(archivo_subido)
                if not contenido_novela.strip():
                    st.error("El archivo DOCX está vacío o no se pudo extraer el contenido.")
                else:
                    # Crear el prompt para mejorar la novela
                    prompt_mejora = (
                        f"Corrige los defectos señalados y aplica las mejoras sugeridas en la siguiente novela. "
                        f"Defectos y mejoras a aplicar:\n{correcciones}\n\n"
                        f"Texto de la novela:\n{contenido_novela}\n\n"
                        f"Por favor, reescribe la novela incorporando las correcciones y mejoras mencionadas. "
                        f"Mantén la coherencia, el estilo y el tono original de la obra."
                    )
                    
                    # Generar el contenido mejorado
                    contenido_mejorado = generar_contenido_cache(
                        prompt_mejora,
                        max_tokens=10000,  # Ajusta según sea necesario
                        temperature=0.7,
                        repetition_penalty=1.2,
                        frequency_penalty=0.5
                    )
                    
                    if contenido_mejorado:
                        st.session_state.contenido_mejorado = contenido_mejorado
                        st.session_state.novela_mejorada = True
                        st.success("Tu novela ha sido mejorada exitosamente.")
                    else:
                        st.error("Ocurrió un error al intentar mejorar tu novela.")

# Mostrar el contenido mejorado y permitir la descarga
if 'contenido_mejorado' in st.session_state and st.session_state.novela_mejorada:
    st.subheader("Paso 3: Revisa y Descarga tu Novela Mejorada")
    contenido_editable_mejorado = st.text_area(
        "Revisa y edita el contenido mejorado si es necesario:", 
        st.session_state.contenido_mejorado, 
        height=600
    )

    # Botón para descargar el archivo mejorado
    if st.button("Descargar Novela Mejorada", key="descargar_mejorada"):
        buffer_docx_mejorada = exportar_a_docx(contenido_editable_mejorado, titulo="Novela Mejorada")
        if buffer_docx_mejorada:
            st.download_button(
                label="Descargar Novela Mejorada en DOCX",
                data=buffer_docx_mejorada,
                file_name="novela_mejorada.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            st.success("Descarga iniciada correctamente.")
        else:
            st.error("Ocurrió un error al generar el archivo DOCX.")

    # Botón para resetear la sección de mejora
    if st.button("Mejorar Otra Novela", key="reset_mejorar_novela"):
        for key in ['contenido_mejorado', 'novela_mejorada']:
            if key in st.session_state:
                del st.session_state[key]
        st.experimental_rerun()

# =====================
# Finalización
# =====================

st.markdown("""
---
*Nota: Asegúrate de que el archivo DOCX que subas no exceda el tamaño máximo permitido por la API de OpenRouter. Si tu novela es muy extensa, considera dividirla en secciones más pequeñas y procesarlas por separado.*
""")
