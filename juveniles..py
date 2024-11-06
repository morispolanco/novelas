import streamlit as st
import requests
import time
from docx import Document
from io import BytesIO
import os

# Configuración de la página
st.set_page_config(
    page_title="📝 Generador de Cuentos Infantiles",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📝 Generador de Cuentos Infantiles")
st.write("Esta aplicación genera un cuento infantil en inglés o español basado en el tema o idea que ingreses, adaptado al rango de edades seleccionado y dividido en capítulos con títulos, evitando la repetición de contenido.")

# Inicializar estado de la sesión
if 'capitulos' not in st.session_state:
    st.session_state.capitulos = []
if 'resumenes' not in st.session_state:
    st.session_state.resumenes = []
if 'titulo_obra' not in st.session_state:
    st.session_state.titulo_obra = "Cuento Infantil"
if 'proceso_generado' not in st.session_state:
    st.session_state.proceso_generado = False
if 'prompt' not in st.session_state:
    st.session_state.prompt = ""
if 'idioma' not in st.session_state:
    st.session_state.idioma = "Español"
if 'rango_edades' not in st.session_state:
    st.session_state.rango_edades = "6-8 años"

# Características de un buen cuento infantil
caracteristicas_cuento_infantil = """
**Características de un buen cuento infantil:**

1. **Extensión**
   - **Brevedad adecuada**: Adaptado a la capacidad de atención del rango de edad seleccionado, generalmente entre 500 y 2000 palabras.

2. **Estilo**
   - **Lenguaje simple y claro**: Adecuado para la edad, con vocabulario accesible.
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

# Función para generar un capítulo de cuento infantil
def generar_capitulo(prompt, capitulo_num, resumen_previas, idioma, rango_edades):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}"
    }
    instrucciones = (
        "Asegúrate de que el contenido generado cumpla con las características de un cuento infantil. "
        "Desarrolla personajes atractivos y cercanos a la audiencia infantil, adapta el lenguaje al rango de edades seleccionado, "
        "incluye valores positivos y una lección de vida. Mantén una narrativa ágil con diálogos sencillos y expresivos. "
        "Evita repetir información ya mencionada en capítulos anteriores. Cada capítulo debe comenzar con un título apropiado."
    )
    if resumen_previas:
        resumen_texto = " Hasta ahora, el cuento ha cubierto los siguientes puntos: " + resumen_previas
    else:
        resumen_texto = ""
    
    mensaje = (
        f"**Características del cuento infantil:** {caracteristicas_cuento_infantil}\n\n"
        f"Escribe el capítulo {capitulo_num} de un cuento infantil en {idioma} sobre el siguiente tema: {prompt}. "
        f"El capítulo debe comenzar con un título apropiado y tener una extensión adecuada para el rango de edades {rango_edades}. "
        f"No debe contener subdivisiones ni subcapítulos.{resumen_texto} {instrucciones}"
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
                titulo_capitulo = lineas[0].strip().replace("Título:", "").replace("Titulo:", "").strip()
                contenido = lineas[1].strip()
                return titulo_capitulo, contenido
            else:
                st.warning(f"No se pudo extraer el título del Capítulo {capitulo_num}.")
                return f"Capítulo {capitulo_num}", contenido_completo
        else:
            st.error(f"Respuesta inesperada de la API al generar el capítulo {capitulo_num}.")
            return None, None
    except requests.exceptions.RequestException as e:
        st.error(f"Error al generar el capítulo {capitulo_num}: {e}")
        return None, None

# Función para resumir un capítulo utilizando la API de OpenRouter
def resumir_capitulo(capitulo, idioma):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}"
    }
    prompt_resumen = (
        "Proporciona un resumen conciso y relevante del siguiente capítulo de un cuento infantil en "
        f"{idioma}. El resumen debe resaltar los puntos clave de la trama, los desarrollos de los personajes y los eventos principales, evitando detalles redundantes.\n\n"
        f"Capítulo:\n{capitulo}\n\nResumen:"
    )
    data = {
        "model": "openai/gpt-4o-mini",  # Manteniendo el modelo original
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
            resumen = ' '.join(resumen.split())
            return resumen
        else:
            st.error("Respuesta inesperada de la API al resumir el capítulo.")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error al resumir el capítulo: {e}")
        return None

# Función para crear el documento Word con títulos
def crear_documento(capitulo_list, titulo, idioma):
    doc = Document()
    doc.add_heading(titulo, 0)
    for idx, (titulo_capitulo, capitulo) in enumerate(capitulo_list, 1):
        doc.add_heading(f"Capítulo {idx}: {titulo_capitulo}", level=1)
        doc.add_paragraph(capitulo)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# Interfaz de usuario para seleccionar opción
st.sidebar.title("Opciones")

# Determinar las opciones disponibles en la barra lateral
opciones_disponibles = []
if len(st.session_state.capitulos) < 24 and st.session_state.capitulos:
    opciones_disponibles = ["Continuar Generando", "Iniciar Nueva Generación"]
else:
    opciones_disponibles = ["Iniciar Nueva Generación"]

# Radio buttons sin necesidad de botón de envío
opcion = st.sidebar.radio("¿Qué deseas hacer?", opciones_disponibles)

mostrar_formulario = False
if opcion == "Iniciar Nueva Generación":
    # Limpiar el estado de la sesión
    st.session_state.capitulos = []
    st.session_state.resumenes = []
    st.session_state.titulo_obra = "Cuento Infantil"
    st.session_state.proceso_generado = False
    st.session_state.prompt = ""
    st.session_state.idioma = "Español"
    st.session_state.rango_edades = "6-8 años"
    mostrar_formulario = True
elif opcion == "Continuar Generando":
    if len(st.session_state.capitulos) >= 24:
        st.sidebar.info("Has alcanzado el límite máximo de 24 capítulos.")
    else:
        mostrar_formulario = True

if mostrar_formulario:
    with st.form(key='form_cuento_infantil'):
        if opcion == "Iniciar Nueva Generación":
            st.session_state.prompt = st.text_area(
                "Ingresa el tema o idea para el cuento infantil:",
                height=200,
                value=""
            )
            st.session_state.idioma = st.selectbox(
                "Selecciona el idioma del cuento:",
                options=["Español", "Inglés"],
                index=0
            )
            st.session_state.rango_edades = st.selectbox(
                "Selecciona el rango de edades para el cuento:",
                options=["3-5 años", "6-8 años", "9-12 años"],
                index=1
            )
        else:
            st.text_area(
                "Tema o idea para el cuento infantil:",
                height=200,
                value=st.session_state.prompt,
                disabled=True
            )
            st.selectbox(
                "Idioma del cuento:",
                options=["Español", "Inglés"],
                index=0 if st.session_state.idioma == "Español" else 1,
                disabled=True,
                key='idioma_display'
            )
            st.selectbox(
                "Rango de edades del cuento:",
                options=["3-5 años", "6-8 años", "9-12 años"],
                index=["3-5 años", "6-8 años", "9-12 años"].index(st.session_state.rango_edades),
                disabled=True,
                key='rango_edades_display'
            )
        
        cap_generadas = len(st.session_state.capitulos)
        cap_restantes = 24 - cap_generadas
        num_capitulos = st.slider(
            "Número de capítulos a generar:",
            min_value=1,
            max_value=cap_restantes,
            value=min(3, cap_restantes)
        )
        submit_button = st.form_submit_button(label='Generar Cuento Infantil')

    if submit_button:
        if opcion == "Iniciar Nueva Generación":
            if not st.session_state.prompt.strip():
                st.error("Por favor, ingresa un tema o idea válida para el cuento infantil.")
                st.stop()
            elif len(st.session_state.prompt.strip()) < 5:
                st.error("El tema o idea debe tener al menos 5 caracteres.")
                st.stop()
        else:
            pass
        
        st.success("Iniciando la generación del cuento infantil...")
        st.session_state.proceso_generado = True
        progreso = st.progress(0)
        
        inicio = len(st.session_state.capitulos) + 1
        fin = inicio + num_capitulos - 1
        if fin > 24:
            fin = 24
        cap_generadas_en_ejecucion = 0
        
        for i in range(inicio, fin + 1):
            st.write(f"Generando **Capítulo {i}**...")
            resumen_previas = ' '.join(st.session_state.resumenes) if st.session_state.resumenes else ''
            titulo_capitulo, capitulo = generar_capitulo(
                st.session_state.prompt, 
                i, 
                resumen_previas, 
                st.session_state.idioma, 
                st.session_state.rango_edades
            )
            if capitulo:
                st.session_state.capitulos.append((titulo_capitulo, capitulo))
                resumen = resumir_capitulo(capitulo, st.session_state.idioma)
                if resumen:
                    st.session_state.resumenes.append(resumen)
                else:
                    st.warning(f"No se pudo generar un resumen para el Capítulo {i}.")
                cap_generadas_en_ejecucion += 1
            else:
                st.error("La generación del cuento se ha detenido debido a un error.")
                break
            progreso.progress(cap_generadas_en_ejecucion / num_capitulos)
            time.sleep(2)
        
        progreso.empty()
        
        if cap_generadas_en_ejecucion == num_capitulos:
            st.success(f"Se han generado {cap_generadas_en_ejecucion} capítulos exitosamente.")
            st.session_state.titulo_obra = st.text_input("Título del cuento infantil:", value=st.session_state.titulo_obra)
            if st.session_state.titulo_obra:
                documento = crear_documento(st.session_state.capitulos, st.session_state.titulo_obra, st.session_state.idioma)
                st.download_button(
                    label="Descargar Cuento en Word",
                    data=documento,
                    file_name="cuento_infantil.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
        else:
            st.info(f"Generación interrumpida. Has generado {cap_generadas_en_ejecucion} de {num_capitulos} capítulos.")

# Mostrar el cuento generado
if st.session_state.capitulos and st.session_state.proceso_generado:
    st.markdown("---")
    st.header("📖 Cuento Infantil Generado")
    for idx, (titulo_capitulo, capitulo) in enumerate(st.session_state.capitulos, 1):
        st.subheader(f"Capítulo {idx}: {titulo_capitulo}")
        st.write(capitulo)
