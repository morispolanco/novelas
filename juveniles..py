import streamlit as st
import requests
import time
from docx import Document
from io import BytesIO
import nltk
import pickle
import os

# Descargar recursos de NLTK si no están ya descargados
nltk.download('punkt', quiet=True)

# Configuración de la página
st.set_page_config(
    page_title="📝 Generador de Novelas Juveniles",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📝 Generador de Novelas Juveniles")
st.write("Esta aplicación genera una novela juvenil basada en el tema o idea que ingreses, dividida en capítulos con títulos, evitando la repetición de contenido.")

# Ruta del archivo donde se guardará el estado
ESTADO_ARCHIVO = 'estado_generacion.pkl'

def guardar_estado():
    """Guarda el estado de la sesión en un archivo local."""
    with open(ESTADO_ARCHIVO, 'wb') as f:
        pickle.dump({
            'capitulos': st.session_state.capitulos,
            'resumenes': st.session_state.resumenes,
            'titulo_obra': st.session_state.titulo_obra,
            'proceso_generado': st.session_state.proceso_generado
        }, f)

def cargar_estado():
    """Carga el estado de la sesión desde un archivo local."""
    if os.path.exists(ESTADO_ARCHIVO):
        with open(ESTADO_ARCHIVO, 'rb') as f:
            estado = pickle.load(f)
            st.session_state.capitulos = estado.get('capitulos', [])
            st.session_state.resumenes = estado.get('resumenes', [])
            st.session_state.titulo_obra = estado.get('titulo_obra', "Novela Juvenil")
            st.session_state.proceso_generado = estado.get('proceso_generado', False)
        return True
    return False

def limpiar_estado():
    """Limpia el estado de la sesión y elimina el archivo de estado si existe."""
    st.session_state.capitulos = []
    st.session_state.resumenes = []
    st.session_state.titulo_obra = "Novela Juvenil"
    st.session_state.proceso_generado = False
    if os.path.exists(ESTADO_ARCHIVO):
        os.remove(ESTADO_ARCHIVO)

# Inicializar estado de la sesión
if 'capitulos' not in st.session_state:
    st.session_state.capitulos = []
if 'resumenes' not in st.session_state:
    st.session_state.resumenes = []
if 'titulo_obra' not in st.session_state:
    st.session_state.titulo_obra = "Novela Juvenil"
if 'proceso_generado' not in st.session_state:
    st.session_state.proceso_generado = False

# Intentar cargar el estado guardado al iniciar la aplicación
estado_cargado = cargar_estado()

# Texto que define las características de una novela juvenil
caracteristicas_novela_juvenil = """
**Características de una buena novela juvenil:**

1. **Extensión**
   - **Longitud moderada**: Entre 40,000 y 80,000 palabras. Adaptar la extensión de cada capítulo para alcanzar la longitud total deseada.

2. **Estilo**
   - **Lenguaje accesible**: Directo y sencillo, reflejando el mundo juvenil sin ser condescendiente.
   - **Narración en primera o tercera persona**: Para una conexión íntima con los personajes o para múltiples perspectivas.
   - **Diálogos auténticos**: Realistas y creíbles, reflejando la comunicación cotidiana de los jóvenes.

3. **Tema**
   - **Problemas universales y específicos de la juventud**: Identidad, independencia, conflictos familiares, amistad, primer amor, presión social, descubrimiento personal, salud mental, acoso, racismo, discriminación, etc.
   - **Desarrollo emocional**: Enfocado en el crecimiento emocional de los personajes, mostrando cómo enfrentan y superan sus miedos y limitaciones.

4. **Protagonistas atractivos y cercanos**
   - Jóvenes de edades cercanas a la audiencia, con características atractivas pero imperfectas, enfrentando dilemas morales y evolucionando a lo largo de la historia.

5. **Subgéneros variados**
   - Romance, ciencia ficción, fantasía, aventuras, misterio, horror, etc., manteniendo el enfoque en temas relevantes para la adolescencia.

6. **Narrativa ágil**
   - Ritmo rápido para captar la atención, con capítulos cortos y giros frecuentes en la trama.

7. **Mensaje positivo o inspirador**
   - Transmitir mensajes de superación, esperanza, autenticidad, tolerancia y empatía, ayudando a los lectores a enfrentar sus propios desafíos personales.
"""

# Función para generar un capítulo de la novela juvenil
def generar_capitulo(prompt, capitulo_num, resumen_previas):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}"
    }
    # Instrucciones específicas para novelas juveniles con títulos de capítulos
    instrucciones = (
        "Asegúrate de que el contenido generado cumpla con las características de una novela juvenil. "
        "Debes utilizar un lenguaje accesible, desarrollar personajes jóvenes y cercanos a la audiencia, "
        "abordar temas relevantes para adolescentes y jóvenes adultos, y mantener una narrativa ágil con diálogos auténticos. "
        "Evita repetir información ya mencionada en capítulos anteriores."
        " Además, cada capítulo debe comenzar con un título apropiado."
    )
    if resumen_previas:
        resumen_texto = " Hasta ahora, la novela ha cubierto los siguientes puntos: " + resumen_previas
    else:
        resumen_texto = ""
    # Incorporar las características de la novela juvenil en el prompt
    mensaje = (
        f"**Características de la novela juvenil:** {caracteristicas_novela_juvenil}\n\n"
        f"Escribe el capítulo {capitulo_num} de una novela juvenil sobre el siguiente tema: {prompt}. "
        f"El capítulo debe comenzar con un título apropiado y tener aproximadamente 2000 palabras. No debe contener subdivisiones ni subcapítulos.{resumen_texto} {instrucciones}"
    )
    data = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": mensaje
            }
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        respuesta = response.json()
        if 'choices' in respuesta and len(respuesta['choices']) > 0:
            contenido_completo = respuesta['choices'][0]['message']['content']
            # Separar el título del capítulo y el contenido
            # Asumimos que el modelo responde con el título en la primera línea seguida del contenido
            lineas = contenido_completo.strip().split('\n', 1)
            if len(lineas) == 2:
                titulo_capitulo = lineas[0].strip().replace("Título:", "").replace("Titulo:", "").strip()
                contenido = lineas[1].strip()
                return titulo_capitulo, contenido
            else:
                # Si no se puede separar, devolver sin título
                st.warning(f"No se pudo extraer el título del Capítulo {capitulo_num}.")
                return f"Capítulo {capitulo_num}", contenido_completo
        else:
            st.error(f"Respuesta inesperada de la API al generar el capítulo {capitulo_num}.")
            return None, None
    except requests.exceptions.RequestException as e:
        st.error(f"Error al generar el capítulo {capitulo_num}: {e}")
        return None, None

# Función para resumir un capítulo utilizando la API de OpenRouter
def resumir_capitulo(capitulo):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}"
    }
    prompt_resumen = (
        "Proporciona un resumen conciso y relevante del siguiente capítulo de una novela juvenil. "
        "El resumen debe resaltar los puntos clave de la trama, los desarrollos de los personajes y los eventos principales, evitando detalles redundantes.\n\n"
        f"Capítulo:\n{capitulo}\n\nResumen:"
    )
    data = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": prompt_resumen
            }
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        respuesta = response.json()
        if 'choices' in respuesta and len(respuesta['choices']) > 0:
            resumen = respuesta['choices'][0]['message']['content']
            # Limpiar el resumen eliminando posibles saltos de línea adicionales
            resumen = ' '.join(resumen.split())
            return resumen
        else:
            st.error("Respuesta inesperada de la API al resumir el capítulo.")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error al resumir el capítulo: {e}")
        return None

# Función para crear el documento Word con títulos
def crear_documento(capitulo_list, titulo):
    doc = Document()
    doc.add_heading(titulo, 0)
    for idx, (titulo_capitulo, capitulo) in enumerate(capitulo_list, 1):
        doc.add_heading(f"Capítulo {idx}: {titulo_capitulo}", level=1)
        doc.add_paragraph(capitulo)
    # Guardar el documento en un buffer
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# Botón para reiniciar la generación
if st.sidebar.button("Reiniciar Generación"):
    limpiar_estado()
    st.success("El estado de la generación ha sido reiniciado.")
    st.experimental_rerun()

# Interfaz de usuario para seleccionar opción
st.sidebar.title("Opciones")
opcion = None
if estado_cargado:
    opcion = st.sidebar.radio("¿Qué deseas hacer?", ("Continuar Generando", "Iniciar Nueva Generación"))
else:
    opcion = st.sidebar.radio("¿Qué deseas hacer?", ("Iniciar Nueva Generación",))

mostrar_formulario = False
if opcion == "Iniciar Nueva Generación":
    limpiar_estado()
    mostrar_formulario = True
elif opcion == "Continuar Generando":
    mostrar_formulario = True

if mostrar_formulario:
    with st.form(key='form_novela_juvenil'):
        prompt = st.text_area(
            "Ingresa el tema o idea para la novela juvenil:",
            height=200,
            value=st.session_state.capitulos[-1][1] if (st.session_state.capitulos and opcion == "Continuar Generando") else ""
        )
        num_capitulos_max = 24
        cap_generadas = len(st.session_state.capitulos)
        cap_restantes = num_capitulos_max - cap_generadas
        num_capitulos = st.slider(
            "Número de capítulos a generar:",
            min_value=1,
            max_value=cap_restantes,
            value=min(10, cap_restantes)
        )
        submit_button = st.form_submit_button(label='Generar Novela Juvenil')

    if submit_button:
        if not prompt.strip():
            st.error("Por favor, ingresa un tema o idea válida para la novela juvenil.")
        else:
            st.success("Iniciando la generación de la novela juvenil...")
            st.session_state.proceso_generado = True
            progreso = st.progress(0)
            # Determinar el siguiente capítulo a generar
            inicio = len(st.session_state.capitulos) + 1
            fin = inicio + num_capitulos - 1
            if fin > 24:
                fin = 24
            for i in range(inicio, fin + 1):
                st.write(f"Generando **Capítulo {i}**...")
                # Crear un resumen de capítulos previas para evitar repeticiones
                if st.session_state.resumenes:
                    resumen_previas = ' '.join(st.session_state.resumenes)
                else:
                    resumen_previas = ''
                titulo_capitulo, capitulo = generar_capitulo(prompt, i, resumen_previas)
                if capitulo:
                    st.session_state.capitulos.append((titulo_capitulo, capitulo))
                    # Resumir el capítulo generado
                    resumen = resumir_capitulo(capitulo)
                    if resumen:
                        st.session_state.resumenes.append(resumen)
                    else:
                        st.warning(f"No se pudo generar un resumen para el Capítulo {i}.")
                    # Guardar el estado después de cada capítulo generado
                    guardar_estado()
                else:
                    st.error("La generación de la novela se ha detenido debido a un error.")
                    break
                progreso.progress(i / num_capitulos_max)
                time.sleep(2)  # Reducir la pausa a 2 segundos para mayor eficiencia
            progreso.empty()
            if len(st.session_state.capitulos) == 24:
                st.success("Novela juvenil generada exitosamente.")
                st.session_state.titulo_obra = st.text_input("Título de la novela juvenil:", value=st.session_state.titulo_obra)
                if st.session_state.titulo_obra:
                    documento = crear_documento(st.session_state.capitulos, st.session_state.titulo_obra)
                    st.download_button(
                        label="Descargar Novela en Word",
                        data=documento,
                        file_name="novela_juvenil.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
            else:
                st.info(f"Generación interrumpida. Has generado {len(st.session_state.capitulos)} de 24 capítulos.")
