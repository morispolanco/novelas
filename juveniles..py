import streamlit as st
import requests
from docx import Document
from io import BytesIO
import backoff
import re

# Definir la cantidad máxima de capítulos
MAX_CAPITULOS = 24

# Configuración de la página
st.set_page_config(
    page_title="📝 Generador de Cuentos de Aventuras para Niños (9-12 años)",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📝 Generador de Cuentos de Aventuras para Niños (9-12 años)")
st.write("""
Esta aplicación genera hasta 24 capítulos de cuentos de aventuras para niños de 9 a 12 años en el idioma seleccionado.
Cada capítulo presenta una aventura independiente con personajes únicos y escenarios imaginativos.
""")

# Inicializar estado de la sesión
if 'capitulos' not in st.session_state:
    st.session_state.capitulos = []
if 'titulo_obra' not in st.session_state:
    st.session_state.titulo_obra = "Cuentos de Aventuras"
if 'proceso_generado' not in st.session_state:
    st.session_state.proceso_generado = False
if 'num_capitulos' not in st.session_state:
    st.session_state.num_capitulos = 1
if 'idioma' not in st.session_state:
    st.session_state.idioma = "Inglés"

# Prompt personalizado proporcionado por el usuario
PROMPT_BASE = """
Escribe un cuento de aventuras destinado a niños y niñas de entre 9 a 12 años. La historia debe ser emocionante y apropiada para la edad, incluyendo elementos como desafíos, personajes valientes y escenarios imaginativos. Asegúrate de que el contenido sea entretenido, pero también seguro y adecuado para los niños. Incluye un conflicto interesante y una resolución que deje un mensaje positivo. Ponle título al cuento.

# Requisitos y Sugerencias
- El cuento debe tener entre 500 y 700 palabras, con un lenguaje accesible y comprensible para lectores de este grupo de edad.
- Introduce personajes entrañables con los que los lectores puedan empatizar, como niños con un fuerte sentido de curiosidad, animales mágicos o seres fantásticos.
- Debe haber al menos un obstáculo o desafío que los personajes deban superar, con un mensaje positivo sobre trabajo en equipo, valentía, o creatividad al final.
- Usa descripciones visuales para crear escenas vibrantes, pero evita el uso de términos o situaciones demasiado complejas.

# Estructura sugerida
1. **Introducción**: Presenta al protagonista y el escenario inicial donde se vive una situación tranquila antes de comenzar la aventura.
2. **Conflicto**: Un evento que cambia la rutina del protagonista y lo lleva a una misión inesperada.
3. **Desarrollo**: Los momentos de acción en los que el protagonista debe enfrentar desafíos y obstáculos. Puede haber algún compañero que ayude al protagonista.
4. **Resolución**: Desenlace de la aventura con una solución creativa y un final feliz que ofrezca una reflexión o un mensaje positivo.

# Tono y Estilo
- **Tono**: Aventurero, motivador, divertido.
- **Estilo Narrativo**: Tercera persona o primera persona.

# Output Format
La salida debe ser un cuento escrito en párrafos bien formados, con un flujo narrativo constante y diálogo claro cuando sea necesario. Cada vez que cambie un personaje que hable, usa un salto de línea para mayor claridad.
"""

# Función para extraer el título
def extraer_titulo(respuesta):
    # Suponiendo que el título es la primera línea
    lines = respuesta.strip().split('\n')
    if lines:
        return lines[0].strip()
    return "Título No Encontrado"

# Función con reintentos para generar un capítulo
@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=3)
def generar_capitulo(capitulo_num, idioma):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}"
    }

    # Seleccionar el modelo según la solicitud del usuario
    modelo = "openai/gpt-4o-mini"  # Modelo solicitado por el usuario

    # Construir el prompt dependiendo del idioma
    if idioma.lower() == "inglés":
        prompt = PROMPT_BASE
    elif idioma.lower() == "español":
        prompt = PROMPT_BASE.replace(
            "Escribe un cuento de aventuras destinado a niños y niñas de entre 9 a 12 años.",
            "Escribe un cuento de aventuras destinado a niños y niñas de entre 9 a 12 años en español."
        )
    elif idioma.lower() == "latín":
        prompt = PROMPT_BASE.replace(
            "Escribe un cuento de aventuras destinado a niños y niñas de entre 9 a 12 años.",
            "Escribe un cuento de aventuras destinado a niños y niñas de entre 9 a 12 años en latín."
        )
    else:
        prompt = PROMPT_BASE  # Por defecto en inglés

    mensaje = (
        f"{prompt}\n\n"
        f"Titulo: "
    )

    data = {
        "model": modelo,
        "messages": [
            {
                "role": "user",
                "content": mensaje
            }
        ]
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    respuesta = response.json()
    if 'choices' in respuesta and len(respuesta['choices']) > 0:
        contenido_completo = respuesta['choices'][0]['message']['content']
        titulo_capitulo = extraer_titulo(contenido_completo)
        # Extraer el contenido sin el título
        contenido = contenido_completo.replace(titulo_capitulo, "", 1).strip()
        return titulo_capitulo, contenido
    else:
        st.error(f"Respuesta inesperada de la API al generar el Capítulo {capitulo_num}.")
        return None, None

# Función para crear el documento Word con títulos
def crear_documento(capitulos_list, titulo):
    doc = Document()
    doc.add_heading(titulo, 0)
    for idx, (titulo_capitulo, capitulo) in enumerate(capitulos_list, 1):
        doc.add_heading(f"{titulo_capitulo}", level=1)
        doc.add_paragraph(capitulo)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# Interfaz de usuario para seleccionar opción
st.sidebar.title("Opciones")

# Selección de idioma
idiomas = ["Inglés", "Español", "Latín"]
idioma_seleccionado = st.sidebar.selectbox("Selecciona el idioma del cuento:", idiomas)

# Determinar las opciones disponibles en la barra lateral
opciones_disponibles = []
if len(st.session_state.capitulos) < MAX_CAPITULOS and st.session_state.capitulos:
    opciones_disponibles = ["Continuar Generando", "Iniciar Nueva Generación"]
else:
    opciones_disponibles = ["Iniciar Nueva Generación"]

# Radio buttons sin necesidad de botón de envío
opcion = st.sidebar.radio("¿Qué deseas hacer?", opciones_disponibles)

mostrar_formulario = False
if opcion == "Iniciar Nueva Generación":
    # Limpiar el estado de la sesión
    st.session_state.capitulos = []
    st.session_state.titulo_obra = "Cuentos de Aventuras"
    st.session_state.proceso_generado = False
    st.session_state.num_capitulos = 1
    st.session_state.idioma = idioma_seleccionado
    mostrar_formulario = True
elif opcion == "Continuar Generando":
    if len(st.session_state.capitulos) >= MAX_CAPITULOS:
        st.sidebar.info(f"Has alcanzado el límite máximo de {MAX_CAPITULOS} capítulos.")
    else:
        st.session_state.idioma = idioma_seleccionado
        mostrar_formulario = True

if mostrar_formulario:
    with st.form(key='form_cuento_infantil'):
        if opcion == "Iniciar Nueva Generación":
            st.session_state.num_capitulos = st.number_input(
                "Número de capítulos a generar:",
                min_value=1,
                max_value=MAX_CAPITULOS,
                value=3
            )
        else:
            historias_generadas = len(st.session_state.capitulos)
            historias_restantes = MAX_CAPITULOS - historias_generadas
            st.session_state.num_capitulos = st.number_input(
                "Número de capítulos a generar:",
                min_value=1,
                max_value=historias_restantes,
                value=min(3, historias_restantes)
            )
        
        submit_button = st.form_submit_button(label='Generar Cuentos de Aventuras')

    if submit_button:
        st.success("Iniciando la generación de los cuentos de aventuras...")
        st.session_state.proceso_generado = True
        progreso = st.progress(0)
        
        inicio = len(st.session_state.capitulos) + 1
        fin = inicio + st.session_state.num_capitulos - 1
        if fin > MAX_CAPITULOS:
            fin = MAX_CAPITULOS
        capitulos_generados_ejecucion = 0
        
        for i in range(inicio, fin + 1):
            st.write(f"Generando **Cuento {i}**...")
            titulo_capitulo, capitulo = generar_capitulo(i, st.session_state.idioma)
            if capitulo:
                st.session_state.capitulos.append((titulo_capitulo, capitulo))
                capitulos_generados_ejecucion += 1
            else:
                st.error("La generación de los cuentos se ha detenido debido a un error.")
                break
            progreso.progress(capitulos_generados_ejecucion / st.session_state.num_capitulos)
            # time.sleep(1)  # Eliminado para mejorar la velocidad
        
        progreso.empty()
        
        if capitulos_generados_ejecucion == st.session_state.num_capitulos:
            st.success(f"Se han generado {capitulos_generados_ejecucion} capítulos exitosamente.")
            st.session_state.titulo_obra = st.text_input("Título de los cuentos de aventuras:", value=st.session_state.titulo_obra)
            if st.session_state.titulo_obra:
                documento = crear_documento(st.session_state.capitulos, st.session_state.titulo_obra)
                st.download_button(
                    label="Descargar Cuentos en Word",
                    data=documento,
                    file_name="cuentos_de_aventuras.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                # Opcional: Añadir descarga en PDF
                # documento_pdf = crear_pdf(st.session_state.capitulos, st.session_state.titulo_obra)
                # st.download_button(
                #     label="Descargar Cuentos en PDF",
                #     data=documento_pdf,
                #     file_name="cuentos_de_aventuras.pdf",
                #     mime="application/pdf"
                # )
        else:
            st.info(f"Generación interrumpida. Has generado {capitulos_generados_ejecucion} de {st.session_state.num_capitulos} capítulos.")

# Mostrar los capítulos generados
if st.session_state.capitulos and st.session_state.proceso_generado:
    st.markdown("---")
    st.header("📖 Cuentos de Aventuras Generados")
    for idx, (titulo_capitulo, capitulo) in enumerate(st.session_state.capitulos, 1):
        st.subheader(f"{titulo_capitulo}")
        st.write(capitulo)
