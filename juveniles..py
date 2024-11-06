import streamlit as st
import requests
import time
from docx import Document
from io import BytesIO

# Definir la cantidad máxima de historias
MAX_HISTORIAS = 24

# Configuración de la página
st.set_page_config(
    page_title="📝 Generador de Historias Infantiles",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📝 Generador de Historias Infantiles")
st.write("Esta aplicación genera hasta 24 historias infantiles en inglés basadas en el tema o idea que ingreses. Cada historia se identifica como un capítulo y tiene aproximadamente 1500 palabras.")

# Inicializar estado de la sesión
if 'historias' not in st.session_state:
    st.session_state.historias = []
if 'titulo_obra' not in st.session_state:
    st.session_state.titulo_obra = "Historias Infantiles"
if 'proceso_generado' not in st.session_state:
    st.session_state.proceso_generado = False
if 'prompt' not in st.session_state:
    st.session_state.prompt = ""

# Características de una buena historia infantil
caracteristicas_historia_infantil = """
**Características de una buena historia infantil:**

1. **Extensión**
   - **Brevedad adecuada**: Aproximadamente 1500 palabras, adaptada a la capacidad de atención de los niños.

2. **Estilo**
   - **Lenguaje simple y claro**: Adecuado para niños, con vocabulario accesible.
   - **Narración en tercera persona**: Facilita la comprensión y conexión con los personajes.
   - **Diálogos sencillos y expresivos**: Que reflejen la comunicación típica de los niños.

3. **Tema**
   - **Valores positivos**: Amistad, honestidad, valentía, empatía, etc.
   - **Lecciones de vida**: Enseñanzas que fomenten el desarrollo moral y emocional.
   - **Elementos mágicos o fantásticos**: Para estimular la imaginación.

4. **Protagonistas Atractivos**
   - Personajes con los que los niños puedan identificarse, generalmente niños o animales antropomórficos.

5. **Estructura Clara**
   - **Inicio, desarrollo y desenlace**: Facilita la comprensión de la trama.
   - **Conflicto sencillo**: Resolución positiva que inspire al lector.

6. **Ilustraciones (Opcional)**
   - Aunque no se generan en este proyecto, considerar la inclusión de imágenes para enriquecer la experiencia de lectura.

7. **Ritmo Agradable**
   - Narrativa ágil que mantenga el interés sin ser apresurada.
"""

# Función para generar una historia infantil
def generar_historia(prompt, historia_num):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}"
    }
    instrucciones = (
        "Asegúrate de que el contenido generado cumpla con las características de una historia infantil. "
        "Desarrolla personajes atractivos y cercanos a la audiencia infantil, adapta el lenguaje a niños, "
        "incluye valores positivos y una lección de vida. Mantén una narrativa ágil con diálogos sencillos y expresivos. "
        "Evita repetir información ya mencionada en historias anteriores. Cada historia debe comenzar con un título apropiado."
    )
    
    mensaje = (
        f"**Características de la historia infantil:** {caracteristicas_historia_infantil}\n\n"
        f"Escribe la historia {historia_num} de una serie de historias infantiles en inglés sobre el siguiente tema: {prompt}. "
        f"La historia debe comenzar con un título apropiado y tener aproximadamente 1500 palabras. "
        f"No debe contener subdivisiones ni subcapítulos. {instrucciones}"
    )
    data = {
        "model": "openai/gpt-4o-mini",  # Manteniendo el modelo original
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
            lineas = contenido_completo.strip().split('\n', 1)
            if len(lineas) == 2:
                titulo_historia = lineas[0].strip().replace("Título:", "").replace("Titulo:", "").strip()
                contenido = lineas[1].strip()
                return titulo_historia, contenido
            else:
                st.warning(f"No se pudo extraer el título de la Historia {historia_num}.")
                return f"Historia {historia_num}", contenido_completo
        else:
            st.error(f"Respuesta inesperada de la API al generar la Historia {historia_num}.")
            return None, None
    except requests.exceptions.RequestException as e:
        st.error(f"Error al generar la Historia {historia_num}: {e}")
        return None, None

# Función para crear el documento Word con títulos
def crear_documento(historias_list, titulo):
    doc = Document()
    doc.add_heading(titulo, 0)
    for idx, (titulo_historia, historia) in enumerate(historias_list, 1):
        doc.add_heading(f"Capítulo {idx}: {titulo_historia}", level=1)
        doc.add_paragraph(historia)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# Interfaz de usuario para seleccionar opción
st.sidebar.title("Opciones")

# Determinar las opciones disponibles en la barra lateral
opciones_disponibles = []
if len(st.session_state.historias) < MAX_HISTORIAS and st.session_state.historias:
    opciones_disponibles = ["Continuar Generando", "Iniciar Nueva Generación"]
else:
    opciones_disponibles = ["Iniciar Nueva Generación"]

# Radio buttons sin necesidad de botón de envío
opcion = st.sidebar.radio("¿Qué deseas hacer?", opciones_disponibles)

mostrar_formulario = False
if opcion == "Iniciar Nueva Generación":
    # Limpiar el estado de la sesión
    st.session_state.historias = []
    st.session_state.titulo_obra = "Historias Infantiles"
    st.session_state.proceso_generado = False
    st.session_state.prompt = ""
    mostrar_formulario = True
elif opcion == "Continuar Generando":
    if len(st.session_state.historias) >= MAX_HISTORIAS:
        st.sidebar.info(f"Has alcanzado el límite máximo de {MAX_HISTORIAS} historias.")
    else:
        mostrar_formulario = True

if mostrar_formulario:
    with st.form(key='form_historia_infantil'):
        if opcion == "Iniciar Nueva Generación":
            st.session_state.prompt = st.text_area(
                "Ingresa el tema o idea para las historias infantiles:",
                height=200,
                value=""
            )
        else:
            st.text_area(
                "Tema o idea para las historias infantiles:",
                height=200,
                value=st.session_state.prompt,
                disabled=True
            )
        
        historias_generadas = len(st.session_state.historias)
        historias_restantes = MAX_HISTORIAS - historias_generadas
        num_historias = st.slider(
            "Número de historias a generar:",
            min_value=1,
            max_value=historias_restantes,
            value=min(3, historias_restantes)
        )
        submit_button = st.form_submit_button(label='Generar Historias Infantiles')

    if submit_button:
        if opcion == "Iniciar Nueva Generación":
            if not st.session_state.prompt.strip():
                st.error("Por favor, ingresa un tema o idea válida para las historias infantiles.")
                st.stop()
            elif len(st.session_state.prompt.strip()) < 5:
                st.error("El tema o idea debe tener al menos 5 caracteres.")
                st.stop()
        else:
            pass
        
        st.success("Iniciando la generación de las historias infantiles...")
        st.session_state.proceso_generado = True
        progreso = st.progress(0)
        
        inicio = len(st.session_state.historias) + 1
        fin = inicio + num_historias - 1
        if fin > MAX_HISTORIAS:
            fin = MAX_HISTORIAS
        historias_generadas_ejecucion = 0
        
        for i in range(inicio, fin + 1):
            st.write(f"Generando **Capítulo {i}**...")
            titulo_historia, historia = generar_historia(
                st.session_state.prompt, 
                i
            )
            if historia:
                st.session_state.historias.append((titulo_historia, historia))
                historias_generadas_ejecucion += 1
            else:
                st.error("La generación de las historias se ha detenido debido a un error.")
                break
            progreso.progress(historias_generadas_ejecucion / num_historias)
            time.sleep(2)  # Opcional: Ajustar o eliminar según necesidad
        
        progreso.empty()
        
        if historias_generadas_ejecucion == num_historias:
            st.success(f"Se han generado {historias_generadas_ejecucion} historias exitosamente.")
            st.session_state.titulo_obra = st.text_input("Título de las historias infantiles:", value=st.session_state.titulo_obra)
            if st.session_state.titulo_obra:
                documento = crear_documento(st.session_state.historias, st.session_state.titulo_obra)
                st.download_button(
                    label="Descargar Historias en Word",
                    data=documento,
                    file_name="historias_infantiles.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
        else:
            st.info(f"Generación interrumpida. Has generado {historias_generadas_ejecucion} de {num_historias} historias.")

# Mostrar las historias generadas
if st.session_state.historias and st.session_state.proceso_generado:
    st.markdown("---")
    st.header("📖 Historias Infantiles Generadas")
    for idx, (titulo_historia, historia) in enumerate(st.session_state.historias, 1):
        st.subheader(f"Capítulo {idx}: {titulo_historia}")
        st.write(historia)
