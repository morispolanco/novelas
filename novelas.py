import streamlit as st
import requests
from io import BytesIO
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
MODEL = "openai/gpt-4"  # Puedes ajustar el modelo según tus necesidades

# =====================
# Inicialización de Variables de Sesión
# =====================

if 'novela' not in st.session_state:
    st.session_state.novela = {
        'personajes': [],          # Lista de personajes con su evolución por capítulo
        'eventos': [],             # Lista de eventos clave
        'trama_general': "",       # Resumen de la trama
        'resumen_capitulos': [],   # Lista de resúmenes por capítulo
        'contenido_inicial': "",   # Estructura inicial de la novela
        'contenido_final': "",     # Contenido completo de la novela
        'aprobado': False,         # Bandera para aprobación de la estructura
        'novela_generada': False,  # Bandera para evitar regeneración
        'tema': "",                # Tema de la novela
        'genero': "Suspense"       # Género de la novela
    }

# =====================
# Funciones Auxiliares
# =====================

def generar_contenido(prompt, max_tokens=1500, temperature=0.7, repetition_penalty=1.2, frequency_penalty=0.5):
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
        response = requests.post(API_URL, headers=headers, json=data, timeout=120)  # Aumentar timeout si es necesario
        response.raise_for_status()
        # Ajusta la extracción del contenido según la estructura de la respuesta de OpenRouter
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

# Lista de inicios para escenas
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
    """
    Selecciona un inicio aleatorio para una escena.
    """
    return random.choice(inicios_escena)

def extraer_personajes(contenido):
    """
    Extrae personajes del contenido proporcionado.
    """
    prompt = (
        f"Del siguiente esquema de la novela, extrae una lista de personajes principales junto con sus características y motivaciones en formato JSON. "
        f"Incluye campos para 'nombre', 'descripcion', 'decisiones', 'emociones' y 'eventos_clave'.\n\n"
        f"{contenido}"
    )
    personajes_info = generar_contenido(prompt, max_tokens=1500, temperature=0.5)
    if personajes_info:
        # Asegurar que la respuesta es un JSON válido
        try:
            personajes = json.loads(personajes_info)
            # Asegurar que cada personaje tiene los campos necesarios
            for personaje in personajes:
                for campo in ['nombre', 'descripcion', 'decisiones', 'emociones', 'eventos_clave']:
                    if campo not in personaje:
                        personaje[campo] = ""
            return personajes
        except json.JSONDecodeError:
            st.warning("La API no devolvió un JSON válido. Intentando extraer personajes manualmente.")
            # Intentar extraer personajes de forma manual usando expresiones regulares
            personajes = []
            for linea in contenido.split('\n'):
                match = re.match(r"- \*\*(.+?)\*\*: (.+)", linea)
                if match:
                    nombre = match.group(1).strip()
                    descripcion = match.group(2).strip()
                    personajes.append({
                        "nombre": nombre,
                        "descripcion": descripcion,
                        "decisiones": "",
                        "emociones": "",
                        "eventos_clave": ""
                    })
            return personajes if personajes else None
    return None

def actualizar_personajes_y_resumen(capitulo_num, contenido_escenas):
    """
    Actualiza el estado de los personajes basado en los eventos del capítulo,
    y genera un resumen del capítulo para usar en el siguiente.
    """
    # Generar el resumen del capítulo
    prompt_resumen = (
        f"Genera un resumen coherente y bien estructurado del capítulo {capitulo_num} basado en las siguientes escenas:\n\n"
        f"{contenido_escenas}"
    )
    resumen_capitulo = generar_contenido(prompt_resumen, max_tokens=500, temperature=0.5)

    if resumen_capitulo:
        st.session_state.novela['resumen_capitulos'].append(resumen_capitulo)
    else:
        resumen_capitulo = f"Resumen del capítulo {capitulo_num}: [Error al generar el resumen]"
        st.session_state.novela['resumen_capitulos'].append(resumen_capitulo)

    # Actualizar el desarrollo de personajes
    for personaje in st.session_state.novela['personajes']:
        prompt_desarrollo = (
            f"Basado en los eventos del capítulo {capitulo_num}, actualiza el desarrollo del personaje "
            f"**{personaje['nombre']}**. Describe sus decisiones, emociones y eventos clave ocurridos en este capítulo."
        )
        desarrollo_personaje = generar_contenido(prompt_desarrollo, max_tokens=300, temperature=0.5)

        if desarrollo_personaje:
            # Asumimos que la respuesta es una descripción que se puede agregar a los campos respectivos
            personaje['eventos_clave'] += desarrollo_personaje + " "
        else:
            personaje['eventos_clave'] += "Sin cambios significativos. "

def evaluar_coherencia(contenido):
    """
    Evalúa la coherencia y consistencia del contenido generado.
    """
    prompt_coherencia = (
        f"Revisa el siguiente contenido para asegurar que es coherente y consistente. Verifica que los nombres de los personajes sean consistentes, "
        f"que los eventos sigan un orden lógico y que no haya contradicciones en la trama.\n\n"
        f"Contenido:\n{contenido}\n\n"
        f"Devuelve 'Coherente' si todo está en orden, o proporciona una lista de inconsistencias encontradas."
    )
    evaluacion = generar_contenido(prompt_coherencia, max_tokens=500, temperature=0.3)
    return evaluacion.strip()

def generar_capitulo(capitulo_num, num_escenas, personajes, resumen_anterior, genero):
    """
    Genera todo el contenido de un capítulo.
    """
    titulo_capitulo = f"Capítulo {capitulo_num}: [Título del Capítulo {capitulo_num}]"
    contenido_capitulo = titulo_capitulo + "\n\n"
    contenido_escenas = ""

    for escena_num in range(1, num_escenas + 1):
        contenido_escena = generar_escena_con_referencias(
            capitulo_num,
            escena_num,
            titulo_capitulo,
            personajes,
            resumen_anterior,
            genero
        )
        if contenido_escena:
            # Evaluar coherencia antes de añadir
            evaluacion = evaluar_coherencia(contenido_capitulo + contenido_escena)
            if evaluacion.lower() == "coherente":
                contenido_capitulo += contenido_escena + "\n\n"
                contenido_escenas += contenido_escena + "\n\n"
                # Actualizar el resumen de la trama general
                resumen_fragmento = contenido_escena[:150] + "..." if len(contenido_escena) > 150 else contenido_escena
                st.session_state.novela['trama_general'] += f"Escena {capitulo_num}.{escena_num}: {resumen_fragmento}\n"
                st.session_state.novela['eventos'].append(f"Escena {capitulo_num}.{escena_num}: {resumen_fragmento}")
            else:
                st.warning(f"Inconsistencias encontradas en la escena {capitulo_num}.{escena_num}: {evaluacion}")
                contenido_capitulo += f"[Inconsistencias encontradas en la escena {escena_num} del capítulo {capitulo_num}]\n\n"
                st.session_state.novela['trama_general'] += f"Escena {capitulo_num}.{escena_num}: [Inconsistencias encontradas]\n"
                st.session_state.novela['eventos'].append(f"Escena {capitulo_num}.{escena_num}: [Inconsistencias encontradas]")
        else:
            contenido_capitulo += f"[Error al generar la escena {escena_num} del capítulo {capitulo_num}]\n\n"
            st.session_state.novela['trama_general'] += f"Escena {capitulo_num}.{escena_num}: [Error al generar esta escena]\n"
            st.session_state.novela['eventos'].append(f"Escena {capitulo_num}.{escena_num}: [Error al generar esta escena]")

    # Generar resumen coherente del capítulo
    actualizar_personajes_y_resumen(capitulo_num, contenido_escenas)
    if st.session_state.novela['resumen_capitulos']:
        resumen_anterior = st.session_state.novela['resumen_capitulos'][-1]

    return contenido_capitulo

def generar_escena_con_referencias(capitulo_num, escena_num, titulo_capitulo, personajes, resumen_anterior, genero):
    """
    Genera el contenido de una escena, haciendo referencia a eventos y personajes
    de capítulos anteriores y potenciales eventos futuros.
    """
    inicio = obtener_inicio_escena()

    # Crear el prompt con referencias cruzadas
    prompt_escena = (
        f"{inicio} esta escena, escribe la escena {escena_num} del {titulo_capitulo} "
        f"de la novela de género {genero.lower()} sobre '{st.session_state.novela['tema']}'. "
        f"Debe ser un {genero.lower()} con elementos de misterio y aventura. "
        f"Asegúrate de que las motivaciones de los personajes sean claras y que no haya incoherencias en la trama. "
        f"Refiérete a eventos y decisiones importantes ocurridos en los capítulos previos. "
        f"Considera también el desarrollo futuro que podría influenciar las acciones de los personajes.\n\n"
        f"Resumen de la trama hasta ahora:\n{st.session_state.novela['trama_general']}\n\n"
        f"Resumen del capítulo anterior:\n{resumen_anterior}\n\n"
        f"Información detallada de los personajes y su desarrollo actual:\n"
    )

    # Añadir detalles de los personajes
    for personaje in personajes:
        prompt_escena += (
            f"- **{personaje['nombre']}**: {personaje['descripcion']} "
            f"(Decisiones: {personaje.get('decisiones', 'Ninguna')}, "
            f"Emociones: {personaje.get('emociones', 'Ninguna')}, "
            f"Eventos Clave: {personaje.get('eventos_clave', 'Ninguno')})\n"
        )

    return generar_contenido(prompt_escena, max_tokens=1500, temperature=0.7)

# =====================
# Cacheo de Funciones
# =====================

@st.cache_data(show_spinner=False, ttl=3600)
def generar_contenido_cache(tema, num_capitulos, num_escenas, genero, max_tokens=3000, temperature=0.7):
    """
    Genera la estructura inicial de la novela basada en el tema proporcionado.
    """
    prompt_intro = (
        f"Crea un esquema para una novela de género {genero.lower()} de 35,000 palabras basada en el tema: '{tema}'. "
        f"El esquema debe especificar {num_capitulos} capítulos, cada uno con {num_escenas} escenas. "
        f"Incluye puntos clave de la trama, desarrollo de personajes, descripciones del escenario e indicadores de ritmo. "
        f"Utiliza los siguientes pasos para estructurar el esquema:\n"
        f"1. Introducción: Define el tema principal y el escenario de la historia. Presenta al protagonista y personajes secundarios.\n"
        f"2. Estructura de la Trama: Usa una estructura de tres actos para delinear la trama principal con los eventos clave y desafíos. "
        f"Asegúrate de que la trama principal se mantenga enfocada y que no se introduzcan subtramas innecesarias que distraigan al lector. "
        f"Todos los eventos deben contribuir al desarrollo de la historia central.\n"
        f"3. Capítulos y Escenas: Desglosa la trama en capítulos y escenas, indicando transiciones y contribuciones al ritmo. "
        f"Verifica que los desplazamientos de los personajes entre ubicaciones sean realistas y que el tiempo transcurrido entre eventos sea consistente.\n"
        f"4. Arcos de Personajes: Describe cómo evolucionan los personajes principales a lo largo de la historia.\n"
        f"5. Escenas Clímax: Detalla las escenas que conducen al clímax, asegurando que generen tensión.\n"
        f"6. Resolución: Asegúrate de que la historia cierre las líneas argumentales de forma satisfactoria.\n"
        f"7. Asignación de Palabras: Calcula la distribución aproximada de palabras para cada capítulo para un total de 35,000 palabras."
    )
    return generar_contenido(prompt_intro, max_tokens, temperature)

@st.cache_data(show_spinner=False, ttl=3600)
def generar_contenido_generico(prompt, max_tokens=1500, temperature=0.5):
    """
    Genera contenido genérico basado en el prompt proporcionado.
    """
    return generar_contenido(prompt, max_tokens, temperature)

# =====================
# Interfaz de Usuario
# =====================

st.set_page_config(page_title="Generador de Novelas", layout="wide")

# Barra Lateral
st.sidebar.title("Opciones de Generación de la Novela")

# 1. Opciones de personalización
num_capitulos = st.sidebar.slider("Número de Capítulos", min_value=5, max_value=20, value=12)
num_escenas = st.sidebar.slider("Número de Escenas por Capítulo", min_value=3, max_value=10, value=5)

# 2. Selección de Género
generos = ["Suspense", "Ciencia Ficción", "Romance", "Fantasía Oscura", "Terror", "Aventura", "Acción", "Misterio"]
genero_seleccionado = st.sidebar.selectbox("Selecciona el Género de la Novela", generos, index=0)
st.session_state.novela['genero'] = genero_seleccionado

# 3. Modo Avanzado
modo_avanzado = st.sidebar.checkbox("Modo Avanzado")
if modo_avanzado:
    max_tokens = st.sidebar.number_input("Máximo de Tokens por Solicitud", min_value=500, max_value=10000, value=3000, step=100)
    temperature = st.sidebar.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
else:
    max_tokens = 3000
    temperature = 0.7

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
            contenido_inicial = generar_contenido_cache(
                tema,
                num_capitulos,
                num_escenas,
                genero_seleccionado,
                max_tokens,
                temperature
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

    # **Depuración:** Mostrar la longitud del contenido
    st.markdown(f"### **Longitud del Contenido:** {len(st.session_state.novela['contenido_final'])} caracteres")

    # **Depuración:** Mostrar el contenido completo antes de descargar
    st.markdown("### **Verifica el contenido completo de la novela:**")
    with st.expander("Mostrar Contenido Completo"):
        st.text_area("Contenido de la Novela:", st.session_state.novela['contenido_final'], height=600)

    buffer_docx = exportar_a_docx(st.session_state.novela['contenido_final'])
    if buffer_docx:
        st.download_button(
            label="Descargar Novela en DOCX",
            data=buffer_docx,
            file_name="novela.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key="download_docx_final"  # Clave única asignada
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
            'genero': "Suspense"
        }
        st.experimental_rerun()
