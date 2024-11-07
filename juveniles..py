import streamlit as st
import requests
import time
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
Esta aplicación genera hasta 24 capítulos de cuentos de aventuras para niños de 9 a 12 años en inglés.
Mantiene los mismos personajes pero varía las circunstancias y la trama en cada capítulo.
Cada capítulo se identifica como una aventura independiente y comienza con la palabra "CHAPTER".
""")

# Inicializar estado de la sesión
if 'capitulos' not in st.session_state:
    st.session_state.capitulos = []
if 'titulo_obra' not in st.session_state:
    st.session_state.titulo_obra = "Cuentos de Aventuras"
if 'proceso_generado' not in st.session_state:
    st.session_state.proceso_generado = False
if 'personajes' not in st.session_state:
    st.session_state.personajes = ""
if 'num_capitulos' not in st.session_state:
    st.session_state.num_capitulos = 1

# Características de un buen cuento de aventuras para niños de 9 a 12 años
caracteristicas_cuento = """
**Características de un buen cuento de aventuras para niños de 9 a 12 años:**

1. **Extensión**
   - **Adecuada para la edad**: Aproximadamente 1000 palabras por capítulo, apropiado para su nivel de lectura y atención.

2. **Estilo**
   - **Lenguaje claro y enriquecido**: Vocabulario adecuado que desafíe pero no frustre al lector.
   - **Narración en tercera persona**: Facilita la comprensión y conexión con los personajes.
   - **Diálogos naturales**: Reflejan la comunicación típica de niños de esta edad.

3. **Tema**
   - **Valores positivos**: Amistad, valentía, honestidad, empatía, etc.
   - **Lecciones de vida**: Enseñanzas que fomenten el desarrollo moral y emocional.
   - **Elementos de aventura y fantasía**: Para estimular la imaginación y el interés.

4. **Protagonistas Atractivos**
   - Personajes con los que los niños puedan identificarse, generalmente niños o animales antropomórficos, con personalidades bien definidas.

5. **Estructura Clara**
   - **Inicio, desarrollo y desenlace**: Facilita la comprensión de la trama.
   - **Conflicto sencillo y resoluciones positivas**: Inspira al lector y refuerza los valores enseñados.

6. **Ritmo Agradable**
   - Narrativa ágil que mantenga el interés sin ser apresurada, con un balance adecuado entre acción y descripción.

7. **Consistencia de Personajes**
   - Mantener las mismas características y personalidades de los personajes a lo largo de todos los capítulos, incluso cuando las circunstancias y tramas varían.
"""

# Función para extraer el título usando expresiones regulares
def extraer_titulo(respuesta, capitulo_num):
    # Buscamos "CHAPTER {n}: Título"
    patron = rf'CHAPTER\s*{capitulo_num}:\s*(.*)'
    match = re.search(patron, respuesta, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "Título No Encontrado"

# Función con reintentos para generar un capítulo
@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=3)
def generar_capitulo(personajes, capitulo_num, es_primer_capitulo):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}"
    }
    instrucciones = (
        "Asegúrate de que el contenido generado cumpla con las características de un cuento de aventuras para niños de 9 a 12 años. "
        "Mantén los mismos personajes proporcionados por el usuario, pero varía las circunstancias y la trama en cada capítulo. "
        "Incluye valores positivos y una lección de vida. Mantén una narrativa ágil con diálogos naturales. "
        "Cada capítulo debe comenzar con la palabra 'CHAPTER' seguida del número del capítulo y un título apropiado."
    )
    
    # Construir el prompt dependiendo si es el primer capítulo o no
    if es_primer_capitulo:
        # Incluir la presentación de los personajes solo en el primer capítulo
        mensaje = (
            f"**Características del cuento:** {caracteristicas_cuento}\n\n"
            f"Escribe el capítulo {capitulo_num} de una serie de cuentos de aventuras para niños de 9 a 12 años en inglés, "
            f"manteniendo los siguientes personajes: {personajes}. "
            f"El capítulo debe comenzar con la palabra 'CHAPTER {capitulo_num}: [Título]', seguido de la historia. "
            f"La historia debe tener aproximadamente 1000 palabras y ser una aventura independiente. {instrucciones} "
            f"Asegúrate de que el tono sea emocionante y adecuado para niños de esta edad, con un nivel de detalle que permita a los lectores imaginar claramente las escenas y los personajes."
        )
    else:
        # No incluir la presentación de los personajes en capítulos posteriores
        mensaje = (
            f"**Características del cuento:** {caracteristicas_cuento}\n\n"
            f"Escribe el capítulo {capitulo_num} de una serie de cuentos de aventuras para niños de 9 a 12 años en inglés. "
            f"El capítulo debe comenzar con la palabra 'CHAPTER {capitulo_num}: [Título]', seguido de la historia. "
            f"La historia debe tener aproximadamente 1000 palabras y ser una aventura independiente. {instrucciones} "
            f"Referente a los personajes ya introducidos en el primer capítulo, desarrolla nuevas circunstancias y tramas sin reintroducirlos."
        )
    data = {
        "model": "openai/gpt-4",  # Asegúrate de que el nombre del modelo sea correcto
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
        titulo_capitulo = extraer_titulo(contenido_completo, capitulo_num)
        # Extraer el contenido sin el título
        contenido = contenido_completo.replace(f"CHAPTER {capitulo_num}: {titulo_capitulo}", "").strip()
        return titulo_capitulo, contenido
    else:
        st.error(f"Respuesta inesperada de la API al generar el Capítulo {capitulo_num}.")
        return None, None

# Función para crear el documento Word con títulos
def crear_documento(capitulos_list, titulo):
    doc = Document()
    doc.add_heading(titulo, 0)
    for idx, (titulo_capitulo, capitulo) in enumerate(capitulos_list, 1):
        doc.add_heading(f"CHAPTER {idx}: {titulo_capitulo}", level=1)
        doc.add_paragraph(capitulo)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# Interfaz de usuario para seleccionar opción
st.sidebar.title("Opciones")

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
    st.session_state.personajes = ""
    st.session_state.num_capitulos = 1
    mostrar_formulario = True
elif opcion == "Continuar Generando":
    if len(st.session_state.capitulos) >= MAX_CAPITULOS:
        st.sidebar.info(f"Has alcanzado el límite máximo de {MAX_CAPITULOS} capítulos.")
    else:
        mostrar_formulario = True

if mostrar_formulario:
    with st.form(key='form_cuento_infantil'):
        if opcion == "Iniciar Nueva Generación":
            st.session_state.personajes = st.text_area(
                "Ingresa los detalles de los personajes (uno por línea) en el siguiente formato:\n\n"
                "Nombre: Alex\n"
                "Edad: 10\n"
                "Personalidad: Valiente y curioso\n"
                "Habilidad Especial: Resolver acertijos\n\n"
                "Nombre: Mia\n"
                "Edad: 11\n"
                "Personalidad: Inteligente y amable\n"
                "Habilidad Especial: Comunicación con animales",
                height=300,
                value=""
            )
            st.session_state.num_capitulos = st.number_input(
                "Número de capítulos a generar:",
                min_value=1,
                max_value=MAX_CAPITULOS,
                value=3
            )
        else:
            st.text_area(
                "Detalles de los personajes para los cuentos:",
                height=300,
                value=st.session_state.personajes,
                disabled=True
            )
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
        if opcion == "Iniciar Nueva Generación":
            if not st.session_state.personajes.strip():
                st.error("Por favor, ingresa los detalles de los personajes para los cuentos.")
                st.stop()
            elif len(st.session_state.personajes.strip()) < 10:
                st.error("La descripción de los personajes debe tener al menos 10 caracteres.")
                st.stop()
        else:
            pass  # No hay validaciones adicionales al continuar

        # Procesar las descripciones de los personajes
        personajes_input = st.session_state.personajes.strip().split('\n')
        personajes = []
        personaje_actual = {}
        for linea in personajes_input:
            if linea.strip() == "":
                if personaje_actual:
                    personajes.append(personaje_actual)
                    personaje_actual = {}
                continue
            if ':' in linea:
                clave, valor = linea.split(':', 1)
                personaje_actual[clave.strip().lower()] = valor.strip()
        if personaje_actual:
            personajes.append(personaje_actual)
        
        # Convertir la lista de personajes a un formato legible para la IA
        personajes_formateados = "; ".join([
            f"Name: {p.get('nombre', '')}, Age: {p.get('edad', '')}, Personality: {p.get('personalidad', '')}, Special Ability: {p.get('habilidad especial', '')}"
            for p in personajes
        ])
        
        st.success("Iniciando la generación de los cuentos de aventuras...")
        st.session_state.proceso_generado = True
        progreso = st.progress(0)
        
        inicio = len(st.session_state.capitulos) + 1
        fin = inicio + st.session_state.num_capitulos - 1
        if fin > MAX_CAPITULOS:
            fin = MAX_CAPITULOS
        capitulos_generados_ejecucion = 0
        
        for i in range(inicio, fin + 1):
            st.write(f"Generando **CHAPTER {i}**...")
            es_primer_capitulo = (i == 1)
            titulo_capitulo, capitulo = generar_capitulo(
                personajes_formateados, 
                i,
                es_primer_capitulo
            )
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
        else:
            st.info(f"Generación interrumpida. Has generado {capitulos_generados_ejecucion} de {st.session_state.num_capitulos} capítulos.")

# Mostrar los capítulos generados
if st.session_state.capitulos and st.session_state.proceso_generado:
    st.markdown("---")
    st.header("📖 Cuentos de Aventuras Generados")
    for idx, (titulo_capitulo, capitulo) in enumerate(st.session_state.capitulos, 1):
        st.subheader(f"CHAPTER {idx}: {titulo_capitulo}")
        st.write(capitulo)
