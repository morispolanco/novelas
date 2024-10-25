import streamlit as st
import requests
from io import BytesIO, StringIO
import re
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import random
import json

# =====================
# Configuración Inicial
# =====================

# Asegúrate de que `OPENROUTER_API_KEY` esté configurado en tus secretos de Streamlit.
OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-4o-mini"

# =====================
# Inicialización de Variables de Sesión
# =====================

if 'novela' not in st.session_state:
    st.session_state.novela = {
        'personajes': [],
        'eventos': [],
        'trama_general': "",
        'resumen_capitulos': [],
        'contenido_inicial': "",
        'contenido_final': "",
        'aprobado': False,
        'novela_generada': False,
        'tema': "",
        'genero': "Suspense",
        'analisis': [],
        'escenas': [],
        'novela_original': ""
    }

# =====================
# Funciones Auxiliares
# =====================

def generar_contenido(prompt, max_tokens=1500, temperature=0.7):
    """
    Envía una solicitud a la API de OpenRouter para generar contenido basado en el prompt proporcionado.
    """
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
        "top_p": 1.0,
        "n": 1,
        "stop": None
    }
    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=120)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"Error al generar contenido: {e}")
        return ""

def add_table_of_contents(paragraph):
    """
    Inserta una Tabla de Contenido en el documento DOCX utilizando XML.
    """
    run = paragraph.add_run()
    fldChar_begin = OxmlElement('w:fldChar')
    fldChar_begin.set(qn('w:fldCharType'), 'begin')

    instrText = OxmlElement('w:instrText')
    instrText.text = 'TOC \\o "1-3" \\h \\z \\u'

    fldChar_separate = OxmlElement('w:fldChar')
    fldChar_separate.set(qn('w:fldCharType'), 'separate')

    fldChar_end = OxmlElement('w:fldChar')
    fldChar_end.set(qn('w:fldCharType'), 'end')

    run._r.append(fldChar_begin)
    run._r.append(instrText)
    run._r.append(fldChar_separate)
    run._r.append(fldChar_end)

def exportar_a_docx(contenido_novela):
    """
    Genera un archivo DOCX a partir del contenido proporcionado.
    """
    doc = Document()
    try:
        # Configuración de la página
        sections = doc.sections
        for section in sections:
            section.page_width = Inches(6)
            section.page_height = Inches(9)
            section.top_margin = Inches(0.7)
            section.bottom_margin = Inches(0.5)
            section.left_margin = Inches(0.7)
            section.right_margin = Inches(0.5)

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
            font_heading.size = Pt(16)
            style_heading.element.rPr.rFonts.set(qn('w:eastAsia'), 'Alegreya')

        # Añadir una Tabla de Contenido
        toc_paragraph = doc.add_paragraph('', style='Normal')
        add_table_of_contents(toc_paragraph)
        doc.add_page_break()

        # Procesar el contenido
        for linea in contenido_novela.split('\n'):
            linea = linea.strip()
            if not linea:
                continue

            if linea.startswith("Capítulo"):
                p = doc.add_heading(linea, level=2)
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                p.paragraph_format.line_spacing = 1.15
                p.paragraph_format.space_after = Pt(12)
            else:
                p = doc.add_paragraph(linea, style='Normal')
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                p.paragraph_format.line_spacing = 1.15
                p.paragraph_format.space_after = Pt(9)

        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer

    except Exception as e:
        st.error(f"Error al formatear el documento DOCX: {e}")
        return None

def validar_tema(tema):
    """
    Valida que el tema proporcionado cumpla con los requisitos.
    """
    if not tema:
        return False, "El tema no puede estar vacío."
    if len(tema) < 5:
        return False, "El tema es demasiado corto. Por favor, introduce un tema más descriptivo."
    if len(tema) > 250:
        return False, "El tema es demasiado largo. Por favor, introduce un tema más corto."
    if not re.match("^[a-zA-Z0-9\s\-.,áéíóúñüÁÉÍÓÚÑÜ¡!¿?]+$", tema):
        return False, "El tema contiene caracteres no permitidos."

    # Validación adicional: evitar temas demasiado genéricos
    temas_genericos = ["amor", "aventura", "misterio", "suspense", "acción", "fantasía", "terror", "ciencia ficción"]
    if tema.lower() in temas_genericos:
        return False, "El tema es demasiado genérico. Por favor, introduce un tema más específico."

    return True, ""

def obtener_inicio_escena():
    """
    Selecciona un inicio aleatorio para una escena.
    """
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
    return random.choice(inicios_escena)

def dividir_novela_en_escenas(texto_novela):
    """
    Divide la novela en escenas basadas en delimitadores como 'Capítulo' y 'Escena'.
    """
    escenas = []
    patrones = r"(Capítulo\s+\d+[:]?.*?)(?=Capítulo\s+\d+[:]?|$)"
    capitulos = re.findall(patrones, texto_novela, re.DOTALL | re.IGNORECASE)
    for capitulo in capitulos:
        numero_capitulo = re.search(r"Capítulo\s+(\d+)", capitulo, re.IGNORECASE)
        capitulo_num = int(numero_capitulo.group(1)) if numero_capitulo else 0
        escenas_patron = r"(Escena\s+\d+[:]?.*?)(?=Escena\s+\d+[:]?|$)"
        escenas_en_capitulo = re.findall(escenas_patron, capitulo, re.DOTALL | re.IGNORECASE)
        if escenas_en_capitulo:
            for escena in escenas_en_capitulo:
                numero_escena = re.search(r"Escena\s+(\d+)", escena, re.IGNORECASE)
                escena_num = int(numero_escena.group(1)) if numero_escena else 0
                escenas.append({
                    "capitulo_num": capitulo_num,
                    "escena_num": escena_num,
                    "contenido": escena.strip()
                })
        else:
            # Si no hay escenas, consideramos todo el capítulo como una escena
            escenas.append({
                "capitulo_num": capitulo_num,
                "escena_num": 1,
                "contenido": capitulo.strip()
            })
    return escenas

def analizar_escena(escena):
    """
    Analiza una escena en busca de incoherencias, inconsistencias y otros errores.
    """
    prompt_analisis = (
        f"Analiza la siguiente escena en busca de errores como incoherencias, inconsistencias, mal desarrollo de personajes, "
        f"problemas de ritmo, trama y otros errores narrativos. Proporciona un informe detallado de los problemas encontrados.\n\n"
        f"Escena:\n{escena['contenido']}"
    )
    analisis = generar_contenido(prompt_analisis, max_tokens=1000, temperature=0.5)
    return analisis

def regenerar_escena(escena, analisis):
    """
    Regenera una escena corrigiendo los problemas identificados en el análisis.
    """
    prompt_regeneracion = (
        f"Regenera la siguiente escena, corrigiendo los problemas identificados en el análisis adjunto. "
        f"Asegúrate de mantener la coherencia con el resto de la novela y mejorar el desarrollo de personajes, ritmo y trama.\n\n"
        f"Escena Original:\n{escena['contenido']}\n\n"
        f"Análisis de la Escena:\n{analisis}"
    )
    nueva_escena = generar_contenido(prompt_regeneracion, max_tokens=1500, temperature=0.7)
    return nueva_escena

# =====================
# Interfaz de Usuario
# =====================

st.set_page_config(page_title="Generador y Analizador de Novelas", layout="wide")

# Barra Lateral
st.sidebar.title("Opciones de Generación y Análisis de la Novela")

# Opciones de personalización
st.sidebar.markdown("## Opciones de Generación")
num_capitulos = st.sidebar.slider("Número de Capítulos", min_value=5, max_value=20, value=12)
num_escenas = st.sidebar.slider("Número de Escenas por Capítulo", min_value=3, max_value=10, value=5)

# Selección de Género
generos = ["Suspense", "Ciencia Ficción", "Romance", "Fantasía Oscura", "Terror", "Aventura", "Acción", "Misterio"]
genero_seleccionado = st.sidebar.selectbox("Selecciona el Género de la Novela", generos, index=0)
st.session_state.novela['genero'] = genero_seleccionado

# Modo Avanzado
modo_avanzado = st.sidebar.checkbox("Modo Avanzado")
if modo_avanzado:
    max_tokens = st.sidebar.number_input("Máximo de Tokens por Solicitud", min_value=500, max_value=10000, value=3000, step=100)
    temperature = st.sidebar.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
else:
    max_tokens = 3000
    temperature = 0.7

# Título principal
st.title("Generador y Analizador de Novelas")

# Opciones de la aplicación
opcion = st.selectbox("¿Qué te gustaría hacer?", ["Generar una nueva novela", "Analizar y regenerar una novela existente"])

# ==================================
# Generar una nueva novela
# ==================================
if opcion == "Generar una nueva novela":
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
                contenido_inicial = generar_contenido(
                    f"Crea un esquema para una novela de género {genero_seleccionado.lower()} de 35,000 palabras basada en el tema: '{tema}'. "
                    f"El esquema debe especificar {num_capitulos} capítulos, cada uno con {num_escenas} escenas. "
                    f"Incluye puntos clave de la trama, desarrollo de personajes, descripciones del escenario e indicadores de ritmo."
                )
                if contenido_inicial:
                    st.session_state.novela['contenido_inicial'] = contenido_inicial
                    st.session_state.novela['aprobado'] = False
                    st.session_state.novela['tema'] = tema
                    st.session_state.novela['trama_general'] = ""
                    st.session_state.novela['personajes'] = []
                    st.session_state.novela['eventos'] = []
                    st.session_state.novela['resumen_capitulos'] = []
                    st.session_state.novela['novela_generada'] = False
                    st.success("Estructura de la novela generada exitosamente.")

    # Mostrar el contenido generado y permitir aprobar y continuar
    if st.session_state.novela['contenido_inicial'] and st.session_state.novela['tema']:
        st.subheader("Paso 2: Revisa la Estructura Generada")
        contenido_editable = st.text_area("Edita la estructura si es necesario:", st.session_state.novela['contenido_inicial'], height=300)

        if st.button("Aprobar y Continuar", key="aprobar_continuar"):
            st.session_state.novela['aprobado'] = True
            st.session_state.novela['contenido_final'] = contenido_editable
            st.success("Estructura aprobada y lista para la generación de la novela.")

            # Extraer personajes y motivaciones desde el contenido aprobado
            with st.spinner("Extrayendo personajes y sus motivaciones..."):
                personajes_info = extraer_personajes(st.session_state.novela['contenido_final'])
                if personajes_info:
                    st.session_state.novela['personajes'] = personajes_info
                    st.success("Personajes extraídos exitosamente.")
                else:
                    st.warning("No se pudieron extraer los personajes.")

            st.session_state.novela['trama_general'] = "Resumen inicial de la trama:\n" + st.session_state.novela['contenido_final']

    # Visualizar y Editar Personajes y Resumen de la Trama
    if st.session_state.novela['aprobado']:
        st.subheader("Información de Personajes y Resumen de la Trama")

        # Mostrar personajes
        st.markdown("### Personajes Principales")
        if st.session_state.novela['personajes']:
            for personaje in st.session_state.novela['personajes']:
                st.markdown(f"- **{personaje['nombre']}**: {personaje['descripcion']}")
                st.markdown(f"  - **Decisiones:** {personaje['decisiones']}")
                st.markdown(f"  - **Emociones:** {personaje['emociones']}")
                st.markdown(f"  - **Eventos Clave:** {personaje['eventos_clave']}")
        else:
            st.write("No se han definido personajes.")

        # Mostrar resumen de la trama
        st.markdown("### Resumen de la Trama")
        trama_editable = st.text_area("Edita el resumen de la trama si es necesario:", st.session_state.novela['trama_general'], height=200)
        st.session_state.novela['trama_general'] = trama_editable

    # Paso 3: Generar el contenido de la novela
    if (st.session_state.novela['aprobado']
        and not st.session_state.novela['novela_generada']):
        st.header("Paso 3: Generando la Novela Completa...")

        contenido_novela = st.session_state.novela['contenido_final'] + "\n\n"
        resumen_anterior = ""

        total_tareas = (num_capitulos * num_escenas)
        tareas_completadas = 0
        progress_bar = st.progress(0)
        status_text = st.empty()

        for capitulo_num in range(1, num_capitulos + 1):
            contenido_capitulo = generar_capitulo(
                capitulo_num,
                num_escenas,
                st.session_state.novela['personajes'],
                resumen_anterior,
                genero_seleccionado
            )
            contenido_novela += contenido_capitulo + "\n\n"
            tareas_completadas += num_escenas  # Asumiendo que cada capítulo tiene num_escenas escenas
            status_text.text(f"Generado Capítulo {capitulo_num}")
            progress_bar.progress(tareas_completadas / total_tareas)

            if st.session_state.novela['resumen_capitulos']:
                resumen_anterior = st.session_state.novela['resumen_capitulos'][-1]

        # **Actualizar el contenido_final con el contenido completo generado**
        st.session_state.novela['contenido_final'] = contenido_novela

        st.session_state.novela['novela_generada'] = True  # Marcar como generada

        st.success("Generación de la novela completada con continuidad mejorada.")

    # Paso 4: Exportar la novela
    if st.session_state.novela['novela_generada']:
        st.subheader("Paso 4: Exportar Novela")

        # Mostrar el contenido completo antes de descargar
        st.markdown("### Verifica el contenido completo de la novela:")
        with st.expander("Mostrar Contenido Completo"):
            st.text_area("Contenido de la Novela:", st.session_state.novela['contenido_final'], height=600)

        buffer_docx = exportar_a_docx(st.session_state.novela['contenido_final'])
        if buffer_docx:
            st.download_button(
                label="Descargar Novela en DOCX",
                data=buffer_docx,
                file_name="novela.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="download_docx_final"
            )
            st.success("La novela ha sido generada y está lista para ser descargada.")
        else:
            st.error("No se pudo generar el documento DOCX.")

        if st.button("Generar Nueva Novela", key="nueva_novela"):
            st.session_state.novela = {
                'personajes': [],
                'eventos': [],
                'trama_general': "",
                'resumen_capitulos': [],
                'contenido_inicial': "",
                'contenido_final': "",
                'aprobado': False,
                'novela_generada': False,
                'tema': "",
                'genero': "Suspense",
                'analisis': [],
                'escenas': [],
                'novela_original': ""
            }
            st.experimental_rerun()

# ==================================
# Analizar y regenerar una novela existente
# ==================================
elif opcion == "Analizar y regenerar una novela existente":
    st.subheader("Paso 1: Sube tu Novela")
    uploaded_file = st.file_uploader("Elige un archivo de texto (TXT) o Word (DOCX):", type=["txt", "docx"])

    if uploaded_file is not None:
        if uploaded_file.type == "text/plain":
            # Leer archivo de texto
            texto_novela = StringIO(uploaded_file.getvalue().decode("utf-8")).read()
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            # Leer archivo DOCX
            doc = Document(uploaded_file)
            texto_novela = "\n".join([para.text for para in doc.paragraphs])
        else:
            st.error("Tipo de archivo no soportado.")
            texto_novela = ""

        if texto_novela:
            st.session_state.novela['novela_original'] = texto_novela
            st.success("Novela cargada exitosamente.")

            # Mostrar la novela cargada
            with st.expander("Mostrar Novela Cargada"):
                st.text_area("Novela Original:", texto_novela, height=400)

            # Paso 2: Analizar la novela
            if st.button("Analizar Novela"):
                with st.spinner("Dividiendo la novela en escenas..."):
                    escenas = dividir_novela_en_escenas(texto_novela)
                    st.session_state.novela['escenas'] = escenas
                    st.success(f"Novela dividida en {len(escenas)} escenas.")

                with st.spinner("Analizando escenas..."):
                    analisis_total = []
                    for idx, escena in enumerate(escenas):
                        analisis = analizar_escena(escena)
                        analisis_total.append({
                            "escena": escena,
                            "analisis": analisis
                        })
                        st.write(f"Escena {idx+1} analizada.")

                    st.session_state.novela['analisis'] = analisis_total
                    st.success("Análisis completado.")

                # Mostrar resultados del análisis
                st.subheader("Resultados del Análisis")
                for idx, item in enumerate(st.session_state.novela['analisis']):
                    with st.expander(f"Escena {idx+1} - Capítulo {item['escena']['capitulo_num']}"):
                        st.markdown(f"**Contenido de la Escena:**\n{item['escena']['contenido']}")
                        st.markdown(f"**Análisis de la Escena:**\n{item['analisis']}")

                # Paso 3: Regenerar la novela
                if st.button("Regenerar Novela"):
                    with st.spinner("Regenerando escenas..."):
                        nueva_novela = ""
                        for idx, item in enumerate(st.session_state.novela['analisis']):
                            nueva_escena = regenerar_escena(item['escena'], item['analisis'])
                            nueva_novela += nueva_escena + "\n\n"
                            st.write(f"Escena {idx+1} regenerada.")

                        st.session_state.novela['contenido_final'] = nueva_novela
                        st.success("Novela regenerada exitosamente.")

                    # Mostrar la novela regenerada
                    st.subheader("Novela Regenerada")
                    with st.expander("Mostrar Novela Regenerada"):
                        st.text_area("Novela Regenerada:", st.session_state.novela['contenido_final'], height=400)

                    # Paso 4: Exportar la novela regenerada
                    buffer_docx = exportar_a_docx(st.session_state.novela['contenido_final'])
                    if buffer_docx:
                        st.download_button(
                            label="Descargar Novela Regenerada en DOCX",
                            data=buffer_docx,
                            file_name="novela_regenerada.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key="download_docx_regenerada"
                        )
                        st.success("La novela regenerada está lista para ser descargada.")
                    else:
                        st.error("No se pudo generar el documento DOCX.")
