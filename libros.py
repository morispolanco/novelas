import streamlit as st
import requests
import time
from docx import Document
from io import BytesIO
import pickle
import os
import re  # Importar regex

# Configuración de la página
st.set_page_config(
    page_title="📚 Generador de Libros",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📚 Generador de Libros")
st.write("Esta aplicación genera un libro basado en la idea que ingreses, dividido en capítulos con títulos, evitando la repetición de contenido.")

# Ruta del archivo donde se guardará el estado
ESTADO_ARCHIVO = 'estado_generacion.pkl'

# Definir características para diferentes géneros o tipos de libro
CARACTERISTICAS_LIBRO = {
    "Autoayuda": """
    **Características de un buen libro de autoayuda:**
    1. **Objetivo Claro**
       - **Enfoque específico** en mejorar aspectos concretos de la vida del lector.
    2. **Estructura Práctica**
       - **Incluye ejercicios, ejemplos y consejos** aplicables a situaciones reales.
    3. **Lenguaje Motivador**
       - **Tonos positivos y alentadores** que inspiran al lector a tomar acción.
    4. **Testimonios y Casos de Estudio**
       - **Historias reales** que ilustran los puntos clave y demuestran eficacia.
    5. **Conclusiones Accionables**
       - **Pasos concretos** que el lector puede seguir para implementar los consejos.
    6. **Accesibilidad**
       - **Contenido fácil de entender** y aplicar para cualquier persona, independientemente de su trasfondo.
    7. **Inspiración y Empoderamiento**
       - **Fomenta la confianza** y la capacidad del lector para superar desafíos personales.
    """,
    "Psicología": """
    **Características de un buen libro de psicología:**
    1. **Fundamento Científico**
       - **Basado en teorías y estudios** psicológicos reconocidos.
    2. **Análisis Profundo**
       - **Exploración detallada** de conceptos y fenómenos psicológicos.
    3. **Casos de Estudio**
       - **Ejemplos prácticos** que ilustran teorías y aplicaciones.
    4. **Claridad y Precisión**
       - **Lenguaje técnico pero accesible**, adecuado para lectores no especializados.
    5. **Aplicaciones Prácticas**
       - **Cómo aplicar los conceptos** en la vida diaria para mejorar el bienestar psicológico.
    6. **Estructura Coherente**
       - **Organización lógica** que facilita la comprensión y retención del contenido.
    7. **Reflexión y Autoconocimiento**
       - **Fomenta la introspección** y el entendimiento personal del lector.
    """,
    "Relaciones": """
    **Características de un buen libro sobre relaciones:**
    1. **Dinámica Interpersonal**
       - **Exploración de diferentes tipos de relaciones** (amistades, parejas, familiares).
    2. **Consejos Prácticos**
       - **Estrategias para mejorar la comunicación** y resolver conflictos.
    3. **Desarrollo Emocional**
       - **Fomento de la inteligencia emocional** y la empatía.
    4. **Historias y Ejemplos**
       - **Narrativas que ejemplifican conceptos clave** y facilitan la comprensión.
    5. **Reflexión Personal**
       - **Ejercicios para que el lector evalúe** y mejore sus propias relaciones.
    6. **Diversidad y Inclusión**
       - **Consideración de diferentes perspectivas** y experiencias en las relaciones.
    7. **Construcción de Confianza**
       - **Métodos para establecer y mantener la confianza** en las relaciones interpersonales.
    """,
    "Negocios": """
    **Características de un buen libro de negocios:**
    1. **Estrategias Empresariales**
       - **Métodos para iniciar, gestionar y escalar** negocios de manera efectiva.
    2. **Análisis de Mercado**
       - **Técnicas para investigar y comprender** el mercado objetivo y la competencia.
    3. **Gestión Financiera**
       - **Fundamentos de finanzas empresariales**, incluyendo presupuestos, inversiones y flujo de caja.
    4. **Liderazgo y Gestión de Equipos**
       - **Desarrollo de habilidades de liderazgo** efectivo y gestión de equipos de alto rendimiento.
    5. **Innovación y Competitividad**
       - **Fomento de la creatividad** y adaptación al cambio para mantener la competitividad.
    6. **Planificación Estratégica**
       - **Definición de objetivos claros** y desarrollo de planes para alcanzarlos.
    7. **Casos de Éxito y Fracaso**
       - **Ejemplos reales** que ilustran mejores prácticas y lecciones aprendidas.
    """
    # Puedes agregar más tipos según sea necesario
}

def guardar_estado():
    """Guarda el estado de la sesión en un archivo local."""
    with open(ESTADO_ARCHIVO, 'wb') as f:
        pickle.dump({
            'capitulos': st.session_state.capitulos,
            'resumenes': st.session_state.resumenes,
            'titulo_obra': st.session_state.titulo_obra,
            'proceso_generado': st.session_state.proceso_generado,
            'prompt': st.session_state.prompt,
            'tipo_libro': st.session_state.tipo_libro,
            'idioma': st.session_state.idioma  # Guardar el idioma seleccionado
        }, f)

def cargar_estado():
    """Carga el estado de la sesión desde un archivo local."""
    if os.path.exists(ESTADO_ARCHIVO):
        with open(ESTADO_ARCHIVO, 'rb') as f:
            estado = pickle.load(f)
            st.session_state.capitulos = estado.get('capitulos', [])
            st.session_state.resumenes = estado.get('resumenes', [])
            st.session_state.titulo_obra = estado.get('titulo_obra', "Libro")
            st.session_state.proceso_generado = estado.get('proceso_generado', False)
            st.session_state.prompt = estado.get('prompt', "")
            st.session_state.tipo_libro = estado.get('tipo_libro', list(CARACTERISTICAS_LIBRO.keys())[0])
            st.session_state.idioma = estado.get('idioma', "Español")  # Cargar el idioma seleccionado
        return True
    return False

def limpiar_estado():
    """Limpia el estado de la sesión y elimina el archivo de estado si existe."""
    st.session_state.capitulos = []
    st.session_state.resumenes = []
    st.session_state.titulo_obra = "Libro"
    st.session_state.proceso_generado = False
    st.session_state.prompt = ""
    st.session_state.tipo_libro = list(CARACTERISTICAS_LIBRO.keys())[0]
    st.session_state.idioma = "Español"  # Valor por defecto
    if os.path.exists(ESTADO_ARCHIVO):
        os.remove(ESTADO_ARCHIVO)

# Inicializar estado de la sesión
if 'capitulos' not in st.session_state:
    st.session_state.capitulos = []
if 'resumenes' not in st.session_state:
    st.session_state.resumenes = []
if 'titulo_obra' not in st.session_state:
    st.session_state.titulo_obra = "Libro"
if 'proceso_generado' not in st.session_state:
    st.session_state.proceso_generado = False
if 'prompt' not in st.session_state:
    st.session_state.prompt = ""
if 'tipo_libro' not in st.session_state:
    st.session_state.tipo_libro = list(CARACTERISTICAS_LIBRO.keys())[0]  # Valor por defecto
if 'idioma' not in st.session_state:
    st.session_state.idioma = "Español"  # Valor por defecto

# Intentar cargar el estado guardado al iniciar la aplicación
estado_cargado = cargar_estado()

def eliminar_secciones(contenido):
    """
    Elimina secciones, subcapítulos y subdivisiones del contenido generado.
    """
    # Patrón para detectar encabezados (por ejemplo, líneas que comienzan con ###, ##, etc.)
    patron_encabezados = re.compile(r"^(#+\s).+", re.MULTILINE)
    # Eliminar los encabezados
    contenido_sin_secciones = patron_encabezados.sub("", contenido)
    # Eliminar líneas vacías resultantes de la eliminación
    contenido_sin_secciones = "\n".join([linea for linea in contenido_sin_secciones.split("\n") if linea.strip() != ""])
    return contenido_sin_secciones

def generar_capitulo(prompt, capitulo_num, resumen_previas, tipo_libro, idioma, intentos=3):
    for intento in range(intentos):
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}"
        }
        instrucciones = (
            "Asegúrate de que el contenido generado cumpla con las características del tipo de libro seleccionado. "
            "Desarrolla los conceptos clave y explora sus aplicaciones. "
            "Utiliza un lenguaje adecuado al género, desarrolla ideas relevantes y cercanas a la audiencia, "
            "aborda temas pertinentes para el tipo de libro y mantiene una narrativa coherente con el género. "
            "Evita repetir información ya mencionada en capítulos anteriores. "
            "Cada capítulo debe comenzar con un título apropiado."
        )
        if resumen_previas:
            resumen_texto = " Hasta ahora, el libro ha cubierto los siguientes puntos: " + resumen_previas
        else:
            resumen_texto = ""
        
        caracteristicas = CARACTERISTICAS_LIBRO.get(tipo_libro, "")
        
        # Prompt mejorado para evitar secciones
        mensaje = (
            f"{caracteristicas}\n\n"
            f"Escribe el capítulo {capitulo_num} de un libro de tipo '{tipo_libro}' en **{idioma}** sobre el siguiente tema: {prompt}. "
            f"El capítulo debe seguir el formato exacto a continuación y ser **aproximadamente 3000 palabras**.\n\n"
            f"**Título:** [Título del Capítulo]\n\n"
            f"---\n\n"
            f"[Contenido del Capítulo] (Debe ser un texto continuo sin secciones, subcapítulos ni subdivisiones)\n\n"
            f"{instrucciones}\n\n"
            f"**Por favor, asegúrate de seguir este formato exactamente sin añadir texto adicional ni secciones.**"
        )
        data = {
            "model": "openai/gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": mensaje
                }
            ],
            "temperature": 0.2,  # Reducir la temperatura para mayor coherencia
            "max_tokens": 4000     # Aumentar el límite de tokens para capítulos más largos
        }
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            respuesta = response.json()
            if 'choices' in respuesta and len(respuesta['choices']) > 0:
                contenido_completo = respuesta['choices'][0]['message']['content']
                
                # Utilizar regex para extraer el título
                titulo_match = re.search(r"\*\*Título:\*\*\s*(.+)", contenido_completo, re.IGNORECASE)
                if titulo_match:
                    titulo_capitulo = titulo_match.group(1).strip()
                    # Extraer el contenido después del título y los guiones
                    contenido_match = re.search(r"\*\*Título:\*\*.*?\n\n---\n\n(.+)", contenido_completo, re.DOTALL)
                    if contenido_match:
                        contenido = contenido_match.group(1).strip()
                    else:
                        # Intentar extraer contenido después de los guiones
                        contenido = contenido_completo.split('\n\n---\n\n', 1)[-1].strip()
                    
                    # Limpiar el contenido para eliminar secciones
                    contenido = eliminar_secciones(contenido)
                    
                    return titulo_capitulo, contenido
                else:
                    st.warning(f"No se pudo extraer el título del Capítulo {capitulo_num} en el intento {intento + 1}.")
                    # Mostrar la respuesta completa para depuración
                    st.text_area(f"Respuesta de la API para el Capítulo {capitulo_num} en el intento {intento + 1}:", contenido_completo, height=300)
            else:
                st.error(f"Respuesta inesperada de la API al generar el capítulo {capitulo_num} en el intento {intento + 1}.")
        except requests.exceptions.RequestException as e:
            st.error(f"Error al generar el capítulo {capitulo_num} en el intento {intento + 1}: {e}")
        
        # Esperar antes de reintentar
        time.sleep(2)
    
    st.error(f"No se pudo generar el Capítulo {capitulo_num} después de {intentos} intentos.")
    return None, None

def resumir_capitulo(capitulo, tipo_libro, idioma):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}"
    }
    caracteristicas = CARACTERISTICAS_LIBRO.get(tipo_libro, "")
    prompt_resumen = (
        f"{caracteristicas}\n\n"
        f"Proporciona un resumen conciso y relevante del siguiente capítulo del libro en **{idioma}**. "
        "El resumen debe resaltar los puntos clave de la trama, los desarrollos de los conceptos y los eventos principales, "
        "evitando detalles redundantes.\n\n"
        f"Capítulo:\n{capitulo}\n\nResumen:"
    )
    data = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": prompt_resumen
            }
        ],
        "temperature": 0.2,  # Reducir la temperatura para mayor coherencia
        "max_tokens": 1500     # Ajustar el límite de tokens según la necesidad
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        respuesta = response.json()
        if 'choices' in respuesta and len(respuesta['choices']) > 0:
            resumen = respuesta['choices'][0]['message']['content']
            resumen = ' '.join(resumen.split())
            # Limpiar el resumen para eliminar secciones si es necesario
            resumen = eliminar_secciones(resumen)
            return resumen
        else:
            st.error("Respuesta inesperada de la API al resumir el capítulo.")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error al resumir el capítulo: {e}")
        return None

def crear_documento(capitulo_list, titulo, tipo_libro, idioma):
    doc = Document()
    doc.add_heading(titulo, 0)
    doc.add_paragraph(f"Tipo de Libro: {tipo_libro}")
    doc.add_paragraph(f"Idioma: {idioma}")  # Agregar el idioma como metadato
    doc.add_paragraph()
    for idx, (titulo_capitulo, capitulo) in enumerate(capitulo_list, 1):
        doc.add_heading(f"Capítulo {idx}: {titulo_capitulo}", level=1)
        doc.add_paragraph(capitulo)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# Interfaz de usuario para seleccionar opciones
st.sidebar.title("Opciones")

# Determinar las opciones disponibles en la barra lateral
opciones_disponibles = []
if estado_cargado and len(st.session_state.capitulos) < 24:
    opciones_disponibles = ["Continuar Generando", "Iniciar Nueva Generación"]
else:
    opciones_disponibles = ["Iniciar Nueva Generación"]

# Radio buttons sin necesidad de botón de envío
opcion = st.sidebar.radio("¿Qué deseas hacer?", opciones_disponibles)

mostrar_formulario = False
if opcion == "Iniciar Nueva Generación":
    limpiar_estado()
    mostrar_formulario = True
elif opcion == "Continuar Generando":
    if len(st.session_state.capitulos) >= 24:
        st.sidebar.info("Has alcanzado el límite máximo de 24 capítulos.")
    else:
        mostrar_formulario = True

if mostrar_formulario:
    with st.form(key='form_libro'):
        if opcion == "Iniciar Nueva Generación":
            st.session_state.tipo_libro = st.selectbox(
                "Selecciona el tipo de libro que deseas generar:",
                options=list(CARACTERISTICAS_LIBRO.keys())
            )
            st.session_state.idioma = st.selectbox(
                "Selecciona el idioma del libro:",
                options=["Español", "Inglés"]
            )
            st.session_state.prompt = st.text_area(
                "Ingresa la idea o tema para el libro:",
                height=200,
                value=""
            )
        else:
            st.selectbox(
                "Tipo de libro:",
                options=list(CARACTERISTICAS_LIBRO.keys()),
                index=list(CARACTERISTICAS_LIBRO.keys()).index(st.session_state.tipo_libro),
                disabled=True
            )
            st.selectbox(
                "Idioma del libro:",
                options=["Español", "Inglés"],
                index=["Español", "Inglés"].index(st.session_state.idioma),
                disabled=True
            )
            st.text_area(
                "Idea o tema para el libro:",
                height=200,
                value=st.session_state.prompt,
                disabled=True
            )
        
        cap_generadas = len(st.session_state.capitulos)
        cap_restantes = 24 - cap_generadas
        num_capitulos = st.slider(
            "Número de capítulos a generar:",
            min_value=1,
            max_value=cap_restantes,
            value=min(3, cap_restantes)
        )
        submit_button = st.form_submit_button(label='Generar Libro')
    
    if submit_button:
        if opcion == "Iniciar Nueva Generación":
            if not st.session_state.prompt.strip():
                st.error("Por favor, ingresa una idea o tema válida para el libro.")
                st.stop()
        else:
            pass
        
        st.success("Iniciando la generación del libro...")
        st.session_state.proceso_generado = True
        progreso = st.progress(0)
        
        inicio = len(st.session_state.capitulos) + 1
        fin = inicio + num_capitulos - 1
        if fin > 24:
            fin = 24
        cap_generadas_en_ejecucion = 0
        
        for i in range(inicio, fin + 1):
            st.write(f"Generando **Capítulo {i}**...")
            if st.session_state.resumenes:
                resumen_previas = ' '.join(st.session_state.resumenes)
            else:
                resumen_previas = ''
            titulo_capitulo, capitulo = generar_capitulo(
                st.session_state.prompt, 
                i, 
                resumen_previas,
                st.session_state.tipo_libro,
                st.session_state.idioma  # Pasar el idioma seleccionado
            )
            if capitulo:
                st.session_state.capitulos.append((titulo_capitulo, capitulo))
                resumen = resumir_capitulo(capitulo, st.session_state.tipo_libro, st.session_state.idioma)  # Pasar el idioma seleccionado
                if resumen:
                    st.session_state.resumenes.append(resumen)
                else:
                    st.warning(f"No se pudo generar un resumen para el Capítulo {i}.")
                guardar_estado()
                cap_generadas_en_ejecucion += 1
            else:
                st.error("La generación del libro se ha detenido debido a un error.")
                break
            progreso.progress(cap_generadas_en_ejecucion / num_capitulos)
            time.sleep(2)
        
        progreso.empty()
        
        if cap_generadas_en_ejecucion == num_capitulos:
            st.success(f"Se han generado {cap_generadas_en_ejecucion} capítulos exitosamente.")
            st.session_state.titulo_obra = st.text_input("Título del libro:", value=st.session_state.titulo_obra)
            if st.session_state.titulo_obra:
                documento = crear_documento(
                    st.session_state.capitulos, 
                    st.session_state.titulo_obra, 
                    st.session_state.tipo_libro,
                    st.session_state.idioma  # Pasar el idioma seleccionado
                )
                st.download_button(
                    label="Descargar Libro en Word",
                    data=documento,
                    file_name="libro.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
        else:
            st.info(f"Generación interrumpida. Has generado {cap_generadas_en_ejecucion} de {num_capitulos} capítulos.")

# Mostrar el libro generado
if st.session_state.capitulos and st.session_state.proceso_generado:
    st.markdown("---")
    st.header("📖 Libro Generado")
    for idx, (titulo_capitulo, capitulo) in enumerate(st.session_state.capitulos, 1):
        st.subheader(f"Capítulo {idx}: {titulo_capitulo}")
        st.write(capitulo)
