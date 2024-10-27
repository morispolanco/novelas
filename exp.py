import streamlit as st
import requests
import json
import time
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from io import BytesIO
import re
import random
import matplotlib.pyplot as plt

# Importaciones adicionales para la tabla de contenidos
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# Configuración del modelo y tokens
TOGETHER_API_URL = "https://api.together.xyz/v1/chat/completions"
MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct-Turbo"
MAX_MODEL_TOKENS = 10000  # Según la especificación de tu cURL
STOP_SEQUENCE = "<|eot_id|>"

# Configuración de la página
st.set_page_config(
    page_title="Generador de Novelas de Suspenso Político",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Título de la aplicación
st.title("Generador de Novelas de Suspenso Político")
st.write("""
Esta aplicación genera una novela en el género de thriller político.
Ingrese un tema y personalice el número de capítulos y escenas para crear una narrativa coherente y emocionante.
""")

# Barra lateral para opciones de usuario
st.sidebar.header("Configuración de la Novela")
num_capitulos = st.sidebar.slider("Número de capítulos", min_value=8, max_value=12, value=10)
num_escenas = st.sidebar.slider("Número de escenas por capítulo", min_value=3, max_value=5, value=4)
porcentaje_trama_principal = st.sidebar.slider("Porcentaje de palabras para la trama principal (%)", min_value=60, max_value=80, value=70)
porcentaje_subtramas = 100 - porcentaje_trama_principal
st.sidebar.write(f"Porcentaje de palabras para subtramas: {porcentaje_subtramas}%")

# Inicializar el estado de la aplicación
if 'etapa' not in st.session_state:
    st.session_state.etapa = "inicio"  # etapas: inicio, aprobacion, generacion, completado

if 'estructura' not in st.session_state:
    st.session_state.estructura = None
if 'novela_completa' not in st.session_state:
    st.session_state.novela_completa = None
if 'titulo' not in st.session_state:
    st.session_state.titulo = ""
if 'trama' not in st.session_state:
    st.session_state.trama = ""
if 'subtramas' not in st.session_state:
    st.session_state.subtramas = ""
if 'personajes' not in st.session_state:
    st.session_state.personajes = ""
if 'ambientacion' not in st.session_state:
    st.session_state.ambientacion = ""
if 'tecnica' not in st.session_state:
    st.session_state.tecnica = ""

# Función para llamar a la API de Together
def call_together_api(messages, max_tokens, temperature=0.7, top_p=0.7, top_k=50, repetition_penalty=1, stop=STOP_SEQUENCE, stream=False):
    headers = {
        "Authorization": f"Bearer {st.secrets['TOGETHER_API_KEY']}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "top_k": top_k,
        "repetition_penalty": repetition_penalty,
        "stop": [stop],
        "stream": stream
    }
    try:
        response = requests.post(TOGETHER_API_URL, headers=headers, data=json.dumps(payload), stream=stream)
        if response.status_code != 200:
            st.error(f"Error en la llamada a la API de Together: {response.status_code} - {response.text}")
            return None
        if stream:
            # Manejo de respuestas en streaming (si es necesario)
            # Este ejemplo no implementa el manejo de streaming
            # Puedes implementar esto si la API lo soporta
            pass
        else:
            data = response.json()
            return data.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
    except Exception as e:
        st.error(f"Error en la llamada a la API de Together: {e}")
        return None

# Función para generar la estructura inicial de la novela
def generar_estructura(theme):
    system_message = {
        "role": "system",
        "content": "Eres un asistente que ayuda a generar estructuras detalladas para novelas de suspenso político."
    }
    user_prompt = f"""
Quiero que generes una estructura detallada para una novela de suspenso político basada en el siguiente tema:

### Tema:
{theme}

### Instrucciones:

- La estructura debe estar en formato Markdown.
- Utiliza **exactamente** los siguientes encabezados, con el mismo formato y orden:

#### Título:

#### Trama Principal:

#### Subtramas:

#### Personajes:

#### Ambientación:

#### Técnicas Literarias a Utilizar:

- Asegúrate de que cada sección tenga contenido detallado y relevante.
- No agregues secciones adicionales ni modifiques los encabezados.

Por favor, proporciona la estructura ahora.
"""
    user_message = {
        "role": "user",
        "content": user_prompt
    }
    messages = [system_message, user_message]
    estructura = call_together_api(messages, max_tokens=MAX_MODEL_TOKENS)
    return estructura

# Función para extraer los elementos de la estructura usando expresiones regulares
def extraer_elementos(estructura):
    # Mostrar la estructura completa para depuración
    st.write("### Estructura generada por la API:")
    st.text_area("Respuesta de la API:", estructura, height=300)

    # Patrones ajustados
    patrones = {
        'titulo': r"#### Título:\s*(.*)",
        'trama': r"#### Trama Principal:\s*((?:.|\n)*?)(?=#### Subtramas:)",
        'subtramas': r"#### Subtramas:\s*((?:.|\n)*?)(?=#### Personajes:)",
        'personajes': r"#### Personajes:\s*((?:.|\n)*?)(?=#### Ambientación:)",
        'ambientacion': r"#### Ambientación:\s*((?:.|\n)*?)(?=#### Técnicas Literarias a Utilizar:)",
        'tecnica': r"#### Técnicas Literarias a Utilizar:\s*((?:.|\n)*)"
    }

    # Extraer cada sección usando expresiones regulares
    titulo_match = re.search(patrones['titulo'], estructura, re.IGNORECASE)
    trama_match = re.search(patrones['trama'], estructura, re.IGNORECASE)
    subtramas_match = re.search(patrones['subtramas'], estructura, re.IGNORECASE)
    personajes_match = re.search(patrones['personajes'], estructura, re.IGNORECASE)
    ambientacion_match = re.search(patrones['ambientacion'], estructura, re.IGNORECASE)
    tecnica_match = re.search(patrones['tecnica'], estructura, re.IGNORECASE)

    # Mostrar los resultados de las expresiones regulares
    st.write("### Resultados de las expresiones regulares:")
    st.write(f"**Título Match:** {bool(titulo_match)}")
    st.write(f"**Trama Match:** {bool(trama_match)}")
    st.write(f"**Subtramas Match:** {bool(subtramas_match)}")
    st.write(f"**Personajes Match:** {bool(personajes_match)}")
    st.write(f"**Ambientación Match:** {bool(ambientacion_match)}")
    st.write(f"**Técnicas Match:** {bool(tecnica_match)}")

    # Extraer el contenido
    titulo = titulo_match.group(1).strip() if titulo_match else "Sin título"
    trama = trama_match.group(1).strip() if trama_match else "Sin trama principal"
    subtramas = subtramas_match.group(1).strip() if subtramas_match else "Sin subtramas"
    personajes = personajes_match.group(1).strip() if personajes_match else "Sin personajes"
    ambientacion = ambientacion_match.group(1).strip() if ambientacion_match else "Sin ambientación"
    tecnica = tecnica_match.group(1).strip() if tecnica_match else "Sin técnicas literarias"

    # Mostrar los elementos extraídos
    st.write("### Elementos Extraídos:")
    st.write(f"**Título:** {titulo}")
    st.write(f"**Trama Principal:** {trama}")
    st.write(f"**Subtramas:** {subtramas}")
    st.write(f"**Personajes:** {personajes}")
    st.write(f"**Ambientación:** {ambientacion}")
    st.write(f"**Técnicas Literarias:** {tecnica}")

    return titulo, trama, subtramas, personajes, ambientacion, tecnica

# Función para generar cada escena
def generar_escena(capitulo, escena, trama, subtramas, personajes, ambientacion, tecnica, palabras_trama, palabras_subtramas):
    # Estimar tokens: Reducimos la estimación para adaptarnos al límite
    total_palabras_escena = palabras_trama + palabras_subtramas
    total_max_tokens = int(total_palabras_escena * 1.5)

    # Asegurar que no excedamos los límites del modelo
    total_max_tokens = min(total_max_tokens, MAX_MODEL_TOKENS)

    system_message = {
        "role": "system",
        "content": "Eres un asistente que ayuda a generar escenas detalladas para una novela de suspenso político."
    }
    user_prompt = f"""
Escribe la **Escena {escena}** del **Capítulo {capitulo}** de una novela de suspenso político de alta calidad.

**Instrucciones para la Escena:**

- **Extensión**: La escena debe tener al menos **{total_palabras_escena} palabras**.

- **Trama Principal**: {trama}

- **Subtramas**: {subtramas}

- **Personajes**: {personajes}

- **Ambientación**: {ambientacion}

- **Técnicas Literarias a Utilizar**: {tecnica}

### Requisitos Específicos:

1. Desarrolla la trama principal con profundidad y añade giros inesperados que mantengan al lector intrigado.

2. Integra las subtramas de manera que complementen y enriquezcan la trama principal.

3. Muestra las interacciones y evoluciones de los personajes, destacando sus motivaciones y conflictos internos.

4. Mantén un ritmo dinámico que equilibre acción y desarrollo emocional.

5. Utiliza descripciones vívidas y detalladas que permitan al lector visualizar las escenas y sentir las emociones de los personajes.

6. Emplea técnicas literarias avanzadas como metáforas, simbolismo y foreshadowing.

7. Asegura coherencia y cohesión en toda la escena, conectándola lógicamente con los eventos anteriores y preparando el terreno para los futuros.

### Formato y Estilo:

- Utiliza rayas (—) para los diálogos.

- Estructura el texto con párrafos claros y bien organizados.

- Evita clichés y frases hechas, enfocándote en originalidad y frescura.

Recuerda que la escena debe tener **al menos {total_palabras_escena} palabras**.
"""
    user_message = {
        "role": "user",
        "content": user_prompt
    }
    messages = [system_message, user_message]
    escena_texto = call_together_api(messages, max_tokens=total_max_tokens, temperature=0.7, top_p=0.7, top_k=50, repetition_penalty=1, stop=STOP_SEQUENCE, stream=False)
    return escena_texto

# Función para generar la novela completa
def generar_novela_completa(num_capitulos, num_escenas):
    titulo = st.session_state.titulo
    trama = st.session_state.trama
    subtramas = st.session_state.subtramas
    personajes = st.session_state.personajes
    ambientacion = st.session_state.ambientacion
    tecnica = st.session_state.tecnica

    total_palabras = 20000  # Objetivo de 20,000 palabras
    total_escenas = num_capitulos * num_escenas

    # Distribuir las palabras entre trama principal y subtramas
    porcentaje_trama_principal_decimal = porcentaje_trama_principal / 100
    porcentaje_subtramas_decimal = porcentaje_subtramas / 100

    palabras_trama_principal_total = int(total_palabras * porcentaje_trama_principal_decimal)
    palabras_subtramas_total = total_palabras - palabras_trama_principal_total

    # Distribuir palabras por escena
    palabras_por_escena_trama = palabras_trama_principal_total // total_escenas
    palabras_restantes_trama = palabras_trama_principal_total - (palabras_por_escena_trama * total_escenas)

    palabras_por_escena_subtramas = palabras_subtramas_total // total_escenas
    palabras_restantes_subtramas = palabras_subtramas_total - (palabras_por_escena_subtramas * total_escenas)

    # Crear listas de palabras por escena con variación
    palabras_por_escena_trama_lista = []
    palabras_por_escena_subtramas_lista = []
    for _ in range(total_escenas):
        variacion_trama = random.randint(-100, 100)
        palabras_trama = palabras_por_escena_trama + variacion_trama
        palabras_trama = max(400, palabras_trama)  # Ajustamos el mínimo
        palabras_por_escena_trama_lista.append(palabras_trama)

        variacion_subtramas = random.randint(-50, 50)
        palabras_subtramas = palabras_por_escena_subtramas + variacion_subtramas
        palabras_subtramas = max(200, palabras_subtramas)  # Ajustamos el mínimo
        palabras_por_escena_subtramas_lista.append(palabras_subtramas)

    # Ajustar las palabras restantes
    for i in range(palabras_restantes_trama):
        palabras_por_escena_trama_lista[i % total_escenas] += 1

    for i in range(palabras_restantes_subtramas):
        palabras_por_escena_subtramas_lista[i % total_escenas] += 1

    novela = f"**{titulo}**\n\n"

    # Inicializar la barra de progreso
    progress_bar = st.progress(0)
    progress_text = st.empty()
    current = 0

    escena_index = 0  # Índice para acceder a las listas de palabras
    palabras_por_capitulo = {cap: [] for cap in range(1, num_capitulos + 1)}  # Para la gráfica

    # Generar cada capítulo y escena
    for cap in range(1, num_capitulos + 1):
        novela += f"## Capítulo {cap}\n\n"
        for esc in range(1, num_escenas + 1):
            palabras_trama_escena = palabras_por_escena_trama_lista[escena_index]
            palabras_subtramas_escena = palabras_por_escena_subtramas_lista[escena_index]
            total_palabras_escena = palabras_trama_escena + palabras_subtramas_escena

            # Asegurar que total_max_tokens no exceda el límite
            total_max_tokens = int(total_palabras_escena * 1.5)
            if total_max_tokens > MAX_MODEL_TOKENS:
                total_palabras_escena = int(MAX_MODEL_TOKENS / 1.5)
                palabras_trama_escena = int(total_palabras_escena * porcentaje_trama_principal_decimal)
                palabras_subtramas_escena = total_palabras_escena - palabras_trama_escena
                total_max_tokens = MAX_MODEL_TOKENS

            palabras_por_capitulo[cap].append(total_palabras_escena)
            with st.spinner(f"Generando Capítulo {cap}, Escena {esc} ({total_palabras_escena} palabras)..."):
                escena = generar_escena(cap, esc, trama, subtramas, personajes, ambientacion, tecnica,
                                        palabras_trama_escena, palabras_subtramas_escena)
                if not escena:
                    st.error(f"No se pudo generar la Escena {esc} del Capítulo {cap}.")
                    return None
                # Limpiar saltos de línea
                escena = escena.replace('\r\n', '\n').replace('\n', '\n\n')
                novela += f"### Escena {esc}\n\n{escena}\n\n"
                # Actualizar la barra de progreso
                current += 1
                progress_bar.progress(current / total_escenas)
                progress_text.text(f"Progreso: {current}/{total_escenas} escenas generadas.")
                escena_index += 1
                # Retraso para evitar exceder los límites de la API
                time.sleep(1)

    # Ocultar la barra de progreso
    progress_bar.empty()
    progress_text.empty()

    # Mostrar el total de palabras generadas estimadas
    total_palabras_generadas = len(novela.split())
    st.write(f"**Total de palabras generadas estimadas:** {total_palabras_generadas}")

    # Graficar la distribución de palabras por capítulo
    fig, ax = plt.subplots(figsize=(10, 6))
    for cap in palabras_por_capitulo:
        ax.plot(range(1, num_escenas + 1), palabras_por_capitulo[cap], marker='o', label=f'Capítulo {cap}')
    ax.set_xlabel('Escena')
    ax.set_ylabel('Palabras')
    ax.set_title('Distribución de Palabras por Escena en Cada Capítulo')
    ax.legend()
    st.pyplot(fig)

    st.session_state.novela_completa = novela
    st.session_state.etapa = "completado"

    return novela

# Función para exportar la novela a un archivo de Word
def exportar_a_word(titulo, novela_completa):
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
    font.name = 'Times New Roman'
    font.size = Pt(12)

    # Agregar el título
    titulo_paragraph = document.add_heading(titulo, level=0)
    titulo_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

    # Agregar la tabla de contenidos
    agregar_tabla_de_contenidos(document)
    document.add_paragraph("\n*Nota: Después de abrir el documento en Word, actualiza la tabla de contenidos seleccionándola y presionando F9.*")
    document.add_page_break()

    # Separar la novela por capítulos
    capitulos = novela_completa.split("## Capítulo")
    for cap in capitulos:
        cap = cap.strip()
        if not cap:
            continue
        cap_num_match = re.match(r"(\d+)", cap)
        cap_num = cap_num_match.group(1) if cap_num_match else "Sin número"
        cap_content = cap.split('\n', 1)[1].strip() if '\n' in cap else ""

        # Agregar el capítulo
        document.add_heading(f"Capítulo {cap_num}", level=1)

        # Separar por escenas
        escenas = cap_content.split("### Escena")
        for esc in escenas:
            esc = esc.strip()
            if not esc:
                continue
            esc_num_match = re.match(r"(\d+)", esc)
            esc_num = esc_num_match.group(1) if esc_num_match else "Sin número"
            esc_text = esc.split('\n', 1)[1].strip() if '\n' in esc else ""

            # Agregar la escena
            document.add_heading(f"Escena {esc_num}", level=2)

            # Agregar el texto de la escena
            for paragraph_text in esc_text.split('\n\n'):
                paragraph_text = paragraph_text.strip()
                if paragraph_text:
                    paragraph = document.add_paragraph(paragraph_text)
                    paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY
                    paragraph_format = paragraph.paragraph_format
                    paragraph_format.line_spacing = 1.15
                    paragraph_format.space_after = Pt(6)

    # Agregar el conteo total de palabras al final del documento
    total_palabras = len(novela_completa.split())
    document.add_page_break()
    document.add_paragraph(f"**Total de palabras generadas:** {total_palabras}", style='Intense Quote')

    # Guardar el documento en memoria
    buffer = BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer

# Función para agregar una tabla de contenidos automática
def agregar_tabla_de_contenidos(document):
    paragraph = document.add_paragraph()
    run = paragraph.add_run()
    fldChar1 = OxmlElement('w:fldChar')
    fldChar1.set(qn('w:fldCharType'), 'begin')
    instrText = OxmlElement('w:instrText')
    instrText.text = 'TOC \\o "1-3" \\h \\z \\u'
    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'separate')
    fldChar3 = OxmlElement('w:fldChar')
    fldChar3.set(qn('w:fldCharType'), 'end')
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)
    run._r.append(fldChar3)

# Función para mostrar la aprobación de elementos iniciales
def mostrar_aprobacion():
    st.header("Aprobación de Elementos Iniciales")
    st.subheader("Título")
    st.write(st.session_state.titulo)

    st.subheader("Trama Principal")
    st.write(st.session_state.trama)

    st.subheader("Subtramas")
    st.write(st.session_state.subtramas)

    st.subheader("Personajes")
    st.write(st.session_state.personajes)

    st.subheader("Ambientación")
    st.write(st.session_state.ambientacion)

    st.subheader("Técnicas Literarias")
    st.write(st.session_state.tecnica)

    # Botones de aprobación y rechazo
    aprobar = st.button("Aprobar y Generar Novela", key="aprobar")
    if aprobar:
        st.session_state.etapa = "generacion"

    rechazar = st.button("Rechazar y Regenerar Estructura", key="rechazar")
    if rechazar:
        # Reiniciamos los valores
        st.session_state.estructura = None
        st.session_state.titulo = ""
        st.session_state.trama = ""
        st.session_state.subtramas = ""
        st.session_state.personajes = ""
        st.session_state.ambientacion = ""
        st.session_state.tecnica = ""
        st.session_state.etapa = "inicio"

# Interfaz de usuario principal
st.write(f"**Etapa actual:** {st.session_state.etapa}")  # Depuración

if st.session_state.etapa == "inicio":
    st.header("Generación de Elementos Iniciales")
    theme = st.text_input("Ingrese el tema para su thriller político:", "")

    if st.button("Generar Elementos Iniciales"):
        if not theme:
            st.error("Por favor, ingrese un tema.")
        else:
            with st.spinner("Generando la estructura inicial..."):
                estructura = generar_estructura(theme)
                if estructura:
                    titulo, trama, subtramas, personajes, ambientacion, tecnica = extraer_elementos(estructura)
                    # Guardar en el estado de la sesión
                    st.session_state.estructura = estructura
                    st.session_state.titulo = titulo
                    st.session_state.trama = trama
                    st.session_state.subtramas = subtramas
                    st.session_state.personajes = personajes
                    st.session_state.ambientacion = ambientacion
                    st.session_state.tecnica = tecnica
                    st.session_state.etapa = "aprobacion"
                else:
                    st.error("No se pudo generar la estructura inicial. Por favor, intente nuevamente.")

if st.session_state.etapa == "aprobacion":
    mostrar_aprobacion()

if st.session_state.etapa == "generacion":
    with st.spinner("Generando la novela completa..."):
        novela_completa = generar_novela_completa(num_capitulos, num_escenas)
        if novela_completa:
            st.session_state.etapa = "completado"

if st.session_state.etapa == "completado":
    if st.session_state.novela_completa:
        st.success("Novela generada con éxito.")
        # Exportar a Word
        doc_buffer = exportar_a_word(st.session_state.titulo, st.session_state.novela_completa)
        st.download_button(
            label="Descargar Novela en Word",
            data=doc_buffer,
            file_name=f"novela_thriller_politico_{int(time.time())}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        # Mostrar la novela en la interfaz
        st.text_area("Novela Generada:", st.session_state.novela_completa, height=600)
