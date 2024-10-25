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
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# =====================
# Configuración Inicial
# =====================

# Asegúrate de que `OPENROUTER_API_KEY` esté configurado en tus secretos de Streamlit.
OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-4o-mini"  # Actualizado al modelo solicitado

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
        'tema': ""                 # Tema de la novela
    }

# =====================
# Funciones Auxiliares
# =====================

def generar_contenido(prompt, max_tokens=1500, temperature=0.7, repetition_penalty=1.2, frequency_penalty=0.5, retries=3):
    """
    Envía una solicitud a la API de OpenRouter para generar contenido basado en el prompt proporcionado.
    Implementa reintentos en caso de fallos transitorios.
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
        "repetition_penalty": repetition_penalty,
        "frequency_penalty": frequency_penalty
    }
    
    session = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["POST"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    
    try:
        response = session.post(API_URL, headers=headers, json=data, timeout=120)
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

        # Configuración de la fuente predeterminada a Times New Roman, tamaño 12
        style_normal = doc.styles['Normal']
        font_normal = style_normal.font
        font_normal.name = 'Times New Roman'
        font_normal.size = Pt(12)
        style_normal.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')

        # Configurar fuentes para los estilos de encabezado
        for heading in ['Heading 1', 'Heading 2', 'Heading 3']:
            style_heading = doc.styles[heading]
            font_heading = style_heading.font
            font_heading.name = 'Times New Roman'
            font_heading.size = Pt(16)
            style_heading.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')

        # Procesar el contenido
        for linea in contenido_novela.split('\n'):
            linea = linea.strip()
            if not linea:
                continue

            if linea.startswith("Capítulo"):
                p = doc.add_heading(linea, level=2)
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                p.paragraph_format.line_spacing = 1.15
                p.paragraph_format.space_after = Pt(120)
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
    
    # Lista negra de temas inapropiados
    lista_negra = ["violencia extrema", "odio", "discriminación", "contenido para adultos"]  # Agrega más según sea necesario
    for palabra in lista_negra:
        if palabra in tema.lower():
            return False, f"El tema contiene contenido no permitido: '{palabra}'. Por favor, elige otro tema."
    
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
        f"Del siguiente esquema de la novela, extrae una lista de personajes principales junto con sus características y motivaciones en formato JSON:\n\n"
        f"{contenido}"
    )
    personajes_info = generar_contenido(prompt, max_tokens=1500, temperature=0.5, repetition_penalty=1.0, frequency_penalty=0.0)
    if personajes_info:
        # Asegurar que la respuesta es un JSON válido
        try:
            personajes = json.loads(personajes_info)
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
                    personajes.append({"nombre": nombre, "descripcion": descripcion, "desarrollo": "Sin cambios significativos."})
            return personajes if personajes else None
    return None

def actualizar_personajes_y_resumen(capitulo_num, contenido_escenas):
    """
    Actualiza el estado de los personajes basado en los eventos del capítulo,
    y genera un resumen del capítulo para usar en el siguiente.
    """
    # Generar el resumen del capítulo
    prompt_resumen = (
        f"Resumen del capítulo {capitulo_num} basado en las siguientes escenas:\n\n"
        f"{contenido_escenas}"
    )
    resumen_capitulo = generar_contenido(prompt_resumen, max_tokens=500, temperature=0.5, repetition_penalty=1.0, frequency_penalty=0.0)

    if resumen_capitulo:
        st.session_state.novela['resumen_capitulos'].append(resumen_capitulo)
    else:
        resumen_capitulo = f"Resumen del capítulo {capitulo_num}: [Error al generar el resumen]"
        st.session_state.novela['resumen_capitulos'].append(resumen_capitulo)

    # Actualizar el desarrollo de personajes
    for personaje in st.session_state.novela['personajes']:
        prompt_desarrollo = (
            f"Basado en los eventos del capítulo {capitulo_num}, actualiza el desarrollo del personaje "
            f"**{personaje['nombre']}**. Describe cómo ha cambiado su perspectiva o motivaciones."
        )
        desarrollo_personaje = generar_contenido(prompt_desarrollo, max_tokens=200, temperature=0.5, repetition_penalty=1.0, frequency_penalty=0.0)

        if desarrollo_personaje:
            personaje['desarrollo'] = desarrollo_personaje
        else:
            personaje['desarrollo'] = "Sin cambios significativos."

@st.cache_data(show_spinner=False, ttl=3600)
def generar_contenido_cache(tema, num_capitulos, num_escenas, max_tokens=3000, temperature=0.7, repetition_penalty=1.2, frequency_penalty=0.5):
    """
    Genera la estructura inicial de la novela basada en el tema proporcionado.
    """
    prompt_intro = (
        f"Escribe un thriller político.\n\n"
        f"Su escritura debe centrarse en eliminar cualquier inconsistencia o incoherencia entre escenas, ofreciendo una narrativa sin fisuras. "
        f"Desarrollar personajes con perfiles psicológicos profundos y motivaciones complejas. Asegúrate de que el ritmo sea rápido y atraiga al lector, "
        f"animándolo a seguir pasando las páginas. Incluye descripciones vívidas y ricas para mejorar la experiencia inmersiva. "
        f"Escribe diálogos que sean agudos y dinámicos. Evita a toda costa los clichés, las frases trilladas y los personajes increíbles.\n\n"
        f"# Pasos\n\n"
        f"- Desarrolla un esquema argumental fuerte y cautivador para el thriller político.\n"
        f"- Crea personajes multidimensionales con historias de fondo que expliquen sus motivaciones.\n"
        f"- Asegúrate de que las transiciones de escena sean lógicas y mantengan la coherencia en todo momento.\n"
        f"- Utiliza un lenguaje descriptivo para crear imágenes y escenarios vívidos.\n"
        f"- Construye diálogos que reflejen las personalidades y motivaciones de los personajes.\n"
        f"- Mantén una narrativa de ritmo rápido que genere suspenso y emoción.\n\n"
        f"# Formato de salida\n\n"
        f"El resultado debe ser un texto narrativo, bien estructurado en capítulos, si es necesario. Cada escena debe contribuir a la trama y al desarrollo de los personajes, con descripciones vívidas y diálogos atractivos.\n\n"
        f"# Ejemplos\n\n"
        f"[Ejemplo de inicio]\n"
        f"**Escena 1:**\n"
        f"*Escenario*: La oficina tenuemente iluminada del senador James.\n"
        f"*Personajes*: Senador James, su ayudante Lucy.\n"
        f"*Descripción*: La tenue luz de la calle se derrama en la habitación, proyectando sombras sobre el escritorio de caoba. Los libros se alinean en una pared, sus títulos oscurecidos en la oscuridad.\n"
        f"*Diálogo*:  \n"
        f"El senador James dijo: \"Lucy, ¿has visto el último informe? Es condenatorio para nuestra campaña\".\n"
        f"Lucy: \"Sí, senador, pero hay maneras en que podemos cambiar esto a nuestro favor\".\n"
        f"*Desarrollo de la trama*: El senador James recibe noticias inesperadas que amenazan su carrera política. El tiempo avanza en su proceso de toma de decisiones.\n"
        f"[Fin del ejemplo]\n\n"
        f"(*En un thriller real, las escenas variarían en duración y detalle dependiendo de las necesidades narrativas.*)\n\n"
        f"# Notas\n\n"
        f"- Presta atención a los temas políticos y asegúrate de que resuenen con los contextos globales o locales actuales.\n"
        f"- Incorpora giros inesperados de la trama para mantener al lector interesado.\n"
        f"- Utiliza elementos psicológicos para profundizar en el aspecto del thriller, haciendo que el lector se cuestione las motivaciones y prediga los acontecimientos.\n\n"
        f"Crea un esquema para una novela de thriller político de 35,000 palabras basada en el tema: '{tema}'. "
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
    return generar_contenido(prompt_intro, max_tokens, temperature, repetition_penalty, frequency_penalty)

@st.cache_data(show_spinner=False, ttl=3600)
def generar_contenido_generico(prompt, max_tokens=1500, temperature=0.5, repetition_penalty=1.0, frequency_penalty=0.0):
    """
    Genera contenido genérico basado en el prompt proporcionado.
    """
    return generar_contenido(prompt, max_tokens, temperature, repetition_penalty, frequency_penalty)

def generar_escena_con_referencias(capitulo_num, escena_num, titulo_capitulo, personajes, resumen_anterior):
    """
    Genera el contenido de una escena, haciendo referencia a eventos y personajes
    de capítulos anteriores y potenciales eventos futuros.
    """
    inicio = obtener_inicio_escena()
    
    # Crear el prompt con referencias cruzadas en español
    prompt_escena = (
        f"Escribe un thriller político.\n\n"
        f"Su escritura debe centrarse en eliminar cualquier inconsistencia o incoherencia entre escenas, ofreciendo una narrativa sin fisuras. "
        f"Desarrollar personajes con perfiles psicológicos profundos y motivaciones complejas. Asegúrate de que el ritmo sea rápido y atraiga al lector, "
        f"animándolo a seguir pasando las páginas. Incluye descripciones vívidas y ricas para mejorar la experiencia inmersiva. "
        f"Escribe diálogos que sean agudos y dinámicos. Evita a toda costa los clichés, las frases trilladas y los personajes increíbles.\n\n"
        f"# Pasos\n\n"
        f"- Desarrolla un esquema argumental fuerte y cautivador para el thriller político.\n"
        f"- Crea personajes multidimensionales con historias de fondo que expliquen sus motivaciones.\n"
        f"- Asegúrate de que las transiciones de escena sean lógicas y mantengan la coherencia en todo momento.\n"
        f"- Utiliza un lenguaje descriptivo para crear imágenes y escenarios vívidos.\n"
        f"- Construye diálogos que reflejen las personalidades y motivaciones de los personajes.\n"
        f"- Mantén una narrativa de ritmo rápido que genere suspenso y emoción.\n\n"
        f"# Formato de salida\n\n"
        f"El resultado debe ser un texto narrativo, bien estructurado en capítulos, si es necesario. Cada escena debe contribuir a la trama y al desarrollo de los personajes, con descripciones vívidas y diálogos atractivos.\n\n"
        f"# Ejemplos\n\n"
        f"[Ejemplo de inicio]\n"
        f"**Escena 1:**\n"
        f"*Escenario*: La oficina tenuemente iluminada del senador James.\n"
        f"*Personajes*: Senador James, su ayudante Lucy.\n"
        f"*Descripción*: La tenue luz de la calle se derrama en la habitación, proyectando sombras sobre el escritorio de caoba. Los libros se alinean en una pared, sus títulos oscurecidos en la oscuridad.\n"
        f"*Diálogo*:  \n"
        f"El senador James dijo: \"Lucy, ¿has visto el último informe? Es condenatorio para nuestra campaña\".\n"
        f"Lucy: \"Sí, senador, pero hay maneras en que podemos cambiar esto a nuestro favor\".\n"
        f"*Desarrollo de la trama*: El senador James recibe noticias inesperadas que amenazan su carrera política. El tiempo avanza en su proceso de toma de decisiones.\n"
        f"[Fin del ejemplo]\n\n"
        f"(*En un thriller real, las escenas variarían en duración y detalle dependiendo de las necesidades narrativas.*)\n\n"
        f"# Notas\n\n"
        f"- Presta atención a los temas políticos y asegúrate de que resuenen con los contextos globales o locales actuales.\n"
        f"- Incorpora giros inesperados de la trama para mantener al lector interesado.\n"
        f"- Utiliza elementos psicológicos para profundizar en el aspecto del thriller, haciendo que el lector se cuestione las motivaciones y prediga los acontecimientos.\n\n"
        f"{inicio} esta escena, escribe la escena {escena_num} del {titulo_capitulo} "
        f"de la novela sobre '{st.session_state.novela['tema']}'. Debe ser un thriller político con elementos de misterio y aventura. "
        f"Asegúrate de que las motivaciones de los personajes sean claras y que no haya incoherencias en la trama. "
        f"Refiérase a eventos y decisiones importantes ocurridos en los capítulos previos. "
        f"Considera también el desarrollo futuro que podría influenciar las acciones de los personajes.\n\n"
        f"Resumen de la trama hasta ahora:\n{st.session_state.novela['trama_general']}\n\n"
        f"Resumen del capítulo anterior:\n{resumen_anterior}\n\n"
        f"Información de los personajes y su desarrollo actual:\n"
    )
    
    # Añadir detalles de los personajes
    for personaje in personajes:
        prompt_escena += f"- **{personaje['nombre']}**: {personaje['descripcion']} (Desarrollo: {personaje.get('desarrollo', 'Sin cambios')})\n"

    return generar_contenido_generico(prompt_escena, max_tokens=1500, temperature=0.7, repetition_penalty=1.2, frequency_penalty=0.5)

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
    max_tokens = st.sidebar.number_input("Máximo de Tokens por Solicitud", min_value=500, max_value=10000, value=3000, step=100)
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
            contenido_inicial = generar_contenido_cache(tema, num_capitulos, num_escenas, max_tokens, temperature, repetition_penalty, frequency_penalty)
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
        titulo_capitulo = f"Capítulo {capitulo_num}: [Título del Capítulo {capitulo_num}]"
        contenido_novela += titulo_capitulo + "\n\n"
        contenido_escenas = ""

        for escena_num in range(1, num_escenas + 1):
            contenido_escena = generar_escena_con_referencias(capitulo_num, escena_num, titulo_capitulo, st.session_state.novela['personajes'], resumen_anterior)
            if contenido_escena:
                contenido_novela += contenido_escena + "\n\n"
                contenido_escenas += contenido_escena + "\n\n"
                # Actualizar el resumen de la trama general
                resumen_fragmento = contenido_escena[:150] + "..." if len(contenido_escena) > 150 else contenido_escena
                st.session_state.novela['trama_general'] += f"Escena {capitulo_num}.{escena_num}: {resumen_fragmento}\n"
                st.session_state.novela['eventos'].append(f"Escena {capitulo_num}.{escena_num}: {resumen_fragmento}")
            else:
                contenido_novela += f"[Error al generar la escena {escena_num} del capítulo {capitulo_num}]\n\n"
                st.session_state.novela['trama_general'] += f"Escena {capitulo_num}.{escena_num}: [Error al generar esta escena]\n"
                st.session_state.novela['eventos'].append(f"Escena {capitulo_num}.{escena_num}: [Error al generar esta escena]")

            tareas_completadas += 1
            status_text.text(f"Generada Escena {capitulo_num}.{escena_num}")
            progress_bar.progress(tareas_completadas / total_tareas)

        # Actualizar resúmenes y personajes al final del capítulo
        actualizar_personajes_y_resumen(capitulo_num, contenido_escenas)
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
            'tema': ""
        }
        st.experimental_rerun()
