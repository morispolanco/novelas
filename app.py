import streamlit as st
import requests
from io import BytesIO
import re
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import random
import json

# =====================
# Configuración Inicial
# =====================

OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "gpt-4-mini"  # Asegúrate de que este es el nombre correcto del modelo

# =====================
# Funciones Auxiliares
# =====================

def generar_contenido(prompt, max_tokens=3000, temperature=0.7, repetition_penalty=1.2, frequency_penalty=0.5):
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
        "max_tokens": max_tokens,  # Corregido
        "temperature": temperature,
        "repetition_penalty": repetition_penalty,
        "frequency_penalty": frequency_penalty
    }
    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=60)  # Aumentar timeout si es necesario
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

def exportar_a_docx(contenido_novela):
    doc = Document()
    try:
        # Configuración de la página
        sections = doc.sections
        for section in sections:
            section.page_width = Inches(5)
            section.page_height = Inches(8)
            section.top_margin = Inches(0.6)
            section.bottom_margin = Inches(0.6)
            section.left_margin = Inches(0.6)
            section.right_margin = Inches(0.6)

        # Configuración de la fuente predeterminada a Alegreya, tamaño 11
        style_normal = doc.styles['Normal']
        font_normal = style_normal.font
        font_normal.name = 'Alegreya'
        font_normal.size = Pt(11)
        style_normal.element.rPr.rFonts.set(qn('w:eastAsia'), 'Alegreya')

        # Configurar fuentes para los estilos de encabezado
        for heading in ['Heading 1', 'Heading 2', 'Heading 3']:
            style_heading = doc.styles[heading]
            font_heading = style_heading.font
            font_heading.name = 'Alegreya'  # Cambiado de 'Calibri' a 'Alegreya' para consistencia
            font_heading.size = Pt(14)
            style_heading.element.rPr.rFonts.set(qn('w:eastAsia'), 'Alegreya')

        # Procesar el contenido
        for linea in contenido_novela.split('\n'):
            linea = linea.strip()
            if not linea:
                continue

            if linea.startswith("Capítulo"):
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

    except Exception as e:
        st.error(f"Error al formatear el documento DOCX: {e}")
        return None

# =====================
# Cacheo de Funciones
# =====================

@st.cache_data(show_spinner=False, ttl=3600)
def generar_contenido_cache(prompt, max_tokens=3000, temperature=0.7, repetition_penalty=1.2, frequency_penalty=0.5):
    return generar_contenido(prompt, max_tokens, temperature, repetition_penalty, frequency_penalty)

# =====================
# Validación de Entrada
# =====================

def validar_tema(tema):
    if not tema:
        return False, "El tema no puede estar vacío."
    if len(tema) < 5:
        return False, "El tema es demasiado corto. Por favor, introduce un tema más descriptivo."
    if len(tema) > 250:
        return False, "El tema es demasiado largo. Por favor, introduce un tema más corto."
    if not re.match("^[a-zA-Z0-9\s\-.,áéíóúñüÁÉÍÓÚÑÜ]+$", tema):
        return False, "El tema contiene caracteres no permitidos."
    return True, ""

# =====================
# Generación de Inicios Variados para Escenas
# =====================

inicios_escena = [
    "La escena comienza con",
    "En esta parte de la historia,",
    "De repente,",
    "Mientras tanto,",
    "En un giro inesperado,",
    "El ambiente se tensa cuando",
    "Con determinación,",
    "Sorprendentemente,",
    "En medio del caos,",
    "Silenciosamente,"
]

def obtener_inicio_escena():
    return random.choice(inicios_escena)

# =====================
# Inicialización de Variables de Sesión
# =====================

if 'personajes' not in st.session_state:
    st.session_state.personajes = []  # Lista de personajes
if 'eventos' not in st.session_state:
    st.session_state.eventos = []      # Lista de eventos clave
if 'trama_general' not in st.session_state:
    st.session_state.trama_general = ""  # Resumen de la trama

# =====================
# Interfaz de Usuario
# =====================

st.set_page_config(page_title="Generador de Novelas", layout="wide")

# Barra Lateral
st.sidebar.title("Opciones de Generación de la Novela")

# 1. Opciones de personalización
num_capitulos = st.sidebar.slider("Número de Capítulos", min_value=5, max_value=20, value=12)
num_escenas = st.sidebar.slider("Número de Escenas por Capítulo", min_value=3, max_value=10, value=5)

# 2. Modo Avanzado
modo_avanzado = st.sidebar.checkbox("Modo Avanzado")
if modo_avanzado:
    max_tokens = st.sidebar.number_input("Máximo de Tokens por Solicitud", min_value=500, max_value=5000, value=3000, step=100)
    temperature = st.sidebar.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
    repetition_penalty = st.sidebar.slider("Repetition Penalty", min_value=1.0, max_value=2.0, value=1.2, step=0.1)
    frequency_penalty = st.sidebar.slider("Frequency Penalty", min_value=0.0, max_value=2.0, value=0.5, step=0.1)
else:
    max_tokens = 3000
    temperature = 0.7
    repetition_penalty = 1.2
    frequency_penalty = 0.5

# Título principal
st.title("Generador de Novelas")

# Paso 1: Solicitar el tema al usuario
st.subheader("Paso 1: Introduce el Tema de la Novela")
tema = st.text_input("Introduce el tema de la novela:")

# Botón "Enviar" para generar el contenido inicial
if st.button("Enviar", key="enviar_tema"):
    tema_valido, mensaje_error = validar_tema(tema)
    if not tema_valido:
        st.error(mensaje_error)
    else:
        with st.spinner("Generando la estructura de la novela..."):
            prompt_intro = (
                f"Escribe un resumen detallado de la novela y un esquema de los {num_capitulos} capítulos, "
                f"cada uno con {num_escenas} escenas únicas para un thriller con elementos de aventura y misterio basado en el tema: {tema}. "
                f"Incluye descripciones claras de las motivaciones de los personajes principales y asegúrate de que la trama sea coherente y libre de inconsistencias. "
                f"En los diálogos, utiliza la raya (—) en lugar de comillas para marcar el inicio de las conversaciones."
            )
            contenido_inicial = generar_contenido_cache(prompt_intro, max_tokens, temperature, repetition_penalty, frequency_penalty)
            if contenido_inicial:
                st.session_state.contenido_inicial = contenido_inicial
                st.session_state.aprobado = False
                st.session_state.tema = tema
                # Inicializar el resumen de la trama
                st.session_state.trama_general = ""
                # Inicializar personajes y eventos
                st.session_state.personajes = []
                st.session_state.eventos = []
                st.success("Estructura de la novela generada exitosamente.")

# Mostrar el contenido generado y permitir aprobar y continuar
if 'contenido_inicial' in st.session_state and 'tema' in st.session_state:
    st.subheader("Paso 2: Revisa la Estructura Generada")
    contenido_editable = st.text_area("Edita la estructura si es necesario:", st.session_state.contenido_inicial, height=300)

    if st.button("Aprobar y Continuar", key="aprobar_continuar"):
        st.session_state.aprobado = True
        st.session_state.contenido_final = contenido_editable
        st.success("Estructura aprobada y lista para la generación de la novela.")
        
        # Extraer personajes y motivaciones desde el contenido aprobado
        with st.spinner("Extrayendo personajes y sus motivaciones..."):
            prompt_extraer_personajes = (
                f"Del siguiente esquema de la novela, extrae una lista de personajes principales junto con sus características y motivaciones:\n\n"
                f"{st.session_state.contenido_final}"
            )
            personajes_info = generar_contenido_cache(prompt_extraer_personajes, max_tokens=1500, temperature=0.5, repetition_penalty=1.0, frequency_penalty=0.0)
            if personajes_info:
                try:
                    # Intentar parsear la respuesta como JSON
                    personajes = json.loads(personajes_info)
                except json.JSONDecodeError:
                    # Si no es JSON, tratar de extraer la información de forma estructurada
                    personajes = []
                    for linea in personajes_info.split('\n'):
                        if linea.strip().startswith("-"):
                            partes = linea.strip("- ").split(":", 1)
                            if len(partes) == 2:
                                nombre = partes[0].strip()
                                descripcion = partes[1].strip()
                                personajes.append({"nombre": nombre, "descripcion": descripcion})
                st.session_state.personajes = personajes
                st.success("Personajes extraídos exitosamente.")
            else:
                st.warning("No se pudieron extraer los personajes.")

        # Inicializar el resumen de la trama
        st.session_state.trama_general = "Resumen inicial de la trama:\n" + st.session_state.contenido_final

# Visualizar y Editar Personajes y Resumen de la Trama
if 'aprobado' in st.session_state and st.session_state.aprobado:
    st.subheader("Información de Personajes y Resumen de la Trama")
    
    # Mostrar personajes
    st.markdown("### Personajes Principales")
    if st.session_state.personajes:
        for personaje in st.session_state.personajes:
            st.markdown(f"- **{personaje['nombre']}**: {personaje['descripcion']}")
    else:
        st.write("No se han definido personajes.")

    # Mostrar resumen de la trama
    st.markdown("### Resumen de la Trama")
    trama_editable = st.text_area("Edita el resumen de la trama si es necesario:", st.session_state.trama_general, height=200)
    st.session_state.trama_general = trama_editable

# Paso 3: Generar el contenido de la novela
if 'aprobado' in st.session_state and st.session_state.aprobado:
    st.header("Paso 3: Generando la Novela Completa...")
    contenido_novela = st.session_state.contenido_final + "\n\n"

    progress_bar = st.progress(0)
    status_text = st.empty()
    total_tareas = (num_capitulos * num_escenas)
    tareas_completadas = 0

    for capitulo_num in range(1, num_capitulos + 1):
        titulo_capitulo = f"Capítulo {capitulo_num}: [Título del Capítulo {capitulo_num}]"
        contenido_novela += titulo_capitulo + "\n\n"

        for escena_num in range(1, num_escenas + 1):
            inicio = obtener_inicio_escena()
            prompt_escena = (
                f"{inicio} esta escena, escribe la escena {escena_num} del {titulo_capitulo} "
                f"de la novela sobre {st.session_state.tema}. Debe ser un thriller con elementos de misterio y aventura. "
                f"Asegúrate de que las motivaciones de los personajes sean claras y que no haya incoherencias en la trama. "
                f"Utiliza la raya (—) para los diálogos y mantén la coherencia con los eventos anteriores de la novela.\n\n"
                f"Resumen de la trama hasta ahora:\n{st.session_state.trama_general}\n\n"
                f"Información de los personajes:\n"
            )
            # Incluir información de los personajes en el prompt
            for personaje in st.session_state.personajes:
                prompt_escena += f"- **{personaje['nombre']}**: {personaje['descripcion']}\n"

            contenido_escena = generar_contenido_cache(prompt_escena, max_tokens, temperature, repetition_penalty, frequency_penalty)
            if contenido_escena:
                contenido_novela += contenido_escena + "\n\n"
                # Actualizar el resumen de la trama con un fragmento de la escena
                resumen_fragmento = contenido_escena[:150] + "..." if len(contenido_escena) > 150 else contenido_escena
                st.session_state.trama_general += f"Escena {capitulo_num}.{escena_num}: {resumen_fragmento}\n"
                # Agregar evento clave (puedes mejorar esto extrayendo eventos específicos)
                st.session_state.eventos.append(f"Escena {capitulo_num}.{escena_num}: {resumen_fragmento}")
            else:
                contenido_novela += f"[Error al generar la escena {escena_num} del capítulo {capitulo_num}]\n\n"
                st.session_state.trama_general += f"Escena {capitulo_num}.{escena_num}: [Error al generar esta escena]\n"
                st.session_state.eventos.append(f"Escena {capitulo_num}.{escena_num}: [Error al generar esta escena]")

            tareas_completadas += 1
            status_text.text(f"Generada Escena {capitulo_num}.{escena_num}")
            progress_bar.progress(tareas_completadas / total_tareas)

    # Exportar la novela
    st.subheader("Paso 4: Exportar Novela")

    buffer_docx = exportar_a_docx(contenido_novela)
    if buffer_docx:
        st.download_button(
            label="Descargar Novela en DOCX",
            data=buffer_docx,
            file_name="novela.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    st.success("Generación de la novela completada.")

    if st.button("Generar Nueva Novela", key="nueva_novela"):
        for key in ['contenido_inicial', 'tema', 'aprobado', 'contenido_final', 'personajes', 'eventos', 'trama_general']:
            if key in st.session_state:
                del st.session_state[key]
        st.experimental_rerun()
