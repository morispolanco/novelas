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
MODEL = "anthropic/claude-3.5-sonnet:beta"  # Asegúrate de que este es el nombre correcto del modelo

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

# Variables para generación de nueva novela
if 'personajes' not in st.session_state:
    st.session_state.personajes = []  # Lista de personajes
if 'eventos' not in st.session_state:
    st.session_state.eventos = []      # Lista de eventos clave
if 'trama_general' not in st.session_state:
    st.session_state.trama_general = ""  # Resumen de la trama
if 'novela_generada' not in st.session_state:
    st.session_state.novela_generada = False  # Bandera para evitar regeneración

# Variables para mejora/reescritura de novela
if 'novela_mejorada' not in st.session_state:
    st.session_state.novela_mejorada = False  # Bandera para evitar reprocesamiento

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

# =========================================
# Sección 1: Generación de una Nueva Novela
# =========================================

st.header("Generar una Nueva Novela")

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
                # Resetear la bandera de novela generada
                st.session_state.novela_generada = False
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
if ('aprobado' in st.session_state and st.session_state.aprobado 
    and not st.session_state.novela_generada):
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
    
    # Establecer la bandera de novela generada para evitar regeneración
    st.session_state.novela_generada = True

# Paso 4: Exportar la novela (mover el bloque dentro de la generación)
if 'novela_generada' in st.session_state and st.session_state.novela_generada:
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
        for key in ['contenido_inicial', 'tema', 'aprobado', 'contenido_final', 'personajes', 'eventos', 'trama_general', 'novela_generada']:
            if key in st.session_state:
                del st.session_state[key]
        st.experimental_rerun()

# ============================================
# Sección 2: Mejorar o Reescribir una Novela Subida por el Usuario
# ============================================

st.header("Mejorar o Reescribir tu Novela")

# Paso 1: Subir el archivo DOCX
st.subheader("Paso 1: Sube tu Novela en Formato DOCX")
archivo_subido = st.file_uploader("Selecciona tu archivo DOCX:", type=["docx"])

# Paso 2: Seleccionar acción (Mejorar o Reescribir)
st.subheader("Paso 2: Selecciona la Acción Deseada")
accion = st.radio(
    "¿Qué deseas hacer con tu novela?",
    ("Mejorar aspectos específicos", "Reescribir la novela completa")
)

# Paso 3: Especificar qué se quiere corregir, mejorar o reescribir
if accion == "Mejorar aspectos específicos":
    st.subheader("Paso 3A: Especifica las Correcciones o Mejoras")
    correcciones = st.text_area("Describe qué aspectos quieres corregir o mejorar en tu novela:", height=150)
elif accion == "Reescribir la novela completa":
    st.subheader("Paso 3B: Especifica las Instrucciones para la Reescritura")
    correcciones = st.text_area("Describe cómo deseas que se reescriba tu novela (por ejemplo, cambiar el tono, el estilo, el desarrollo de personajes, etc.):", height=150)

# Botón para iniciar la mejora o reescritura
if st.button("Aplicar Acción", key="aplicar_accion"):
    if not archivo_subido:
        st.error("Por favor, sube un archivo DOCX para poder proceder.")
    elif not correcciones.strip():
        if accion == "Mejorar aspectos específicos":
            st.error("Por favor, describe qué quieres corregir o mejorar en tu novela.")
        else:
            st.error("Por favor, describe cómo deseas que se reescriba tu novela.")
    else:
        with st.spinner("Procesando tu novela y aplicando las acciones solicitadas..."):
            # Leer el contenido del archivo DOCX
            contenido_novela = leer_docx(archivo_subido)
            if not contenido_novela:
                st.error("No se pudo extraer el contenido de la novela.")
            else:
                # Crear el prompt según la acción seleccionada
                if accion == "Mejorar aspectos específicos":
                    prompt_accion = (
                        f"Mejora el siguiente texto de una novela de acuerdo con las siguientes especificaciones: {correcciones}\n\n"
                        f"Texto de la novela:\n{contenido_novela}"
                    )
                else:  # Reescribir la novela completa
                    prompt_accion = (
                        f"Reescribe el siguiente texto de una novela según las siguientes especificaciones: {correcciones}\n\n"
                        f"Texto de la novela:\n{contenido_novela}"
                    )
                
                contenido_modificado = generar_contenido_cache(
                    prompt_accion,
                    max_tokens=5000,  # Ajusta según sea necesario
                    temperature=0.7,
                    repetition_penalty=1.2,
                    frequency_penalty=0.5
                )
                if contenido_modificado:
                    st.session_state.contenido_mejorado = contenido_modificado
                    st.session_state.novela_mejorada = True
                    st.success("Tu novela ha sido procesada exitosamente.")
                else:
                    st.error("Ocurrió un error al intentar procesar tu novela.")

# Mostrar el contenido mejorado o reescrito y permitir la descarga
if 'contenido_mejorado' in st.session_state and st.session_state.novela_mejorada:
    st.subheader("Paso 4: Revisa y Descarga tu Novela Procesada")
    contenido_editable_mejorado = st.text_area(
        "Revisa y edita el contenido procesado si es necesario:", 
        st.session_state.contenido_mejorado, 
        height=400
    )

    # Botón para descargar el archivo mejorado o reescrito
    if st.button("Descargar Novela Procesada", key="descargar_procesada"):
        buffer_docx_mejorada = exportar_a_docx(contenido_editable_mejorado)
        if buffer_docx_mejorada:
            st.download_button(
                label="Descargar Novela Procesada en DOCX",
                data=buffer_docx_mejorada,
                file_name="novela_procesada.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            st.success("Descarga iniciada correctamente.")
        else:
            st.error("Ocurrió un error al generar el archivo DOCX.")

    # Botón para resetear la sección de mejora/reescritura
    if st.button("Procesar Otra Novela", key="reset_procesar_novela"):
        for key in ['contenido_mejorado', 'novela_mejorada']:
            if key in st.session_state:
                del st.session_state[key]
        st.experimental_rerun()

# =====================
# Finalización
# =====================

# Nota: Puedes ajustar la posición de esta sección según prefieras en la interfaz.
