import streamlit as st
import requests
import re
import json

# Configuración de la página
st.set_page_config(page_title="Asistente para Escribir Novelas", layout="wide")

# Título de la aplicación
st.title("📚 Asistente para Escribir tu Novela Capítulo por Capítulo")

# Función para llamar a la API de OpenRouter con el modelo especificado
def call_openrouter_api(prompt, max_tokens=5000):
    api_url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}",
        "HTTP-Referer": st.secrets.get('YOUR_SITE_URL', ''),
        "X-Title": st.secrets.get('YOUR_SITE_NAME', ''),
        "Content-Type": "application/json"
    }
    payload = {
        "model": "qwen/qwen-2.5-72b-instruct",  # Nombre del modelo actualizado
        "messages": [
            {"role": "system", "content": "Eres un escritor creativo que ayuda a desarrollar novelas."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,  # Ajustado a 5000 tokens por escena
        "temperature": 0.7,
        "top_p": 0.7,
        "stream": False
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        # Verificar si la respuesta contiene errores
        if 'error' in data:
            st.error(f"Error en la API: {data['error']['message']}")
            return None
        # Asumiendo que la respuesta contiene 'choices' con 'message' y 'content'
        return data['choices'][0]['message']['content'].strip()
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 401:
            st.error("Error de autenticación: Verifica tu clave API de OpenRouter.")
        else:
            st.error(f"Error HTTP en la llamada a la API: {http_err}")
        return None
    except requests.exceptions.ConnectionError:
        st.error("Error de conexión: Verifica tu conexión a Internet.")
        return None
    except (KeyError, IndexError, TypeError) as e:
        st.error(f"Formato inesperado de la respuesta de la API: {e}")
        st.write("### Respuesta Completa de la API para Depuración:")
        st.json(data)  # Mostrar la respuesta completa para depuración
        return None

# Inicialización del estado de la sesión
if 'elements' not in st.session_state:
    st.session_state.elements = {}
if 'chapters' not in st.session_state:
    st.session_state.chapters = []
if 'genre' not in st.session_state:
    st.session_state.genre = "Fantasía"  # Valor por defecto
if 'synopsis' not in st.session_state:
    st.session_state.synopsis = ""
if 'audience' not in st.session_state:
    st.session_state.audience = ""

# Función para generar los elementos fundamentales
def generar_elementos():
    if not st.session_state.genre:
        st.error("Por favor, selecciona un género antes de generar los elementos.")
        return
    if not st.session_state.synopsis:
        st.error("Por favor, ingresa una sinopsis antes de generar los elementos.")
        return
    if not st.session_state.audience:
        st.error("Por favor, define la audiencia antes de generar los elementos.")
        return
    
    # Ajustamos el prompt para que la respuesta sea en formato JSON
    prompt = (
        f"Necesito que me ayudes a crear una novela del género **{st.session_state.genre}** basada en la siguiente sinopsis:\n\n"
        f"**Sinopsis:** {st.session_state.synopsis}\n\n"
        f"**Audiencia:** {st.session_state.audience}\n\n"
        "Por favor, genera los siguientes elementos de manera detallada y coherente en formato JSON con las siguientes claves:\n"
        "1. **personajes_principales**: Lista de al menos tres personajes principales con sus características (personalidad, apariencia y motivaciones).\n"
        "2. **trama**: Descripción de la trama principal, incluyendo el conflicto central y los puntos de giro principales.\n"
        "3. **ambientacion**: Descripción del mundo o entorno donde se desarrolla la historia, incluyendo detalles geográficos, culturales y temporales.\n"
        "4. **tecnica_narrativa**: Descripción del punto de vista (primera persona, tercera persona, etc.) y el estilo narrativo que se utilizará (descriptivo, dinámico, etc.).\n"
    )
    
    with st.spinner("Generando elementos de la novela..."):
        resultado = call_openrouter_api(prompt, max_tokens=5000)  # Ajustado a 5000 tokens
    
    if resultado:
        # Mostrar la respuesta completa para depuración
        st.text_area("Respuesta de la API (para depuración):", value=resultado, height=300)
        try:
            # Intentar parsear la respuesta como JSON
            elementos = json.loads(resultado)
            
            # Validar que todas las claves estén presentes
            required_keys = ['personajes_principales', 'trama', 'ambientacion', 'tecnica_narrativa']
            if all(key in elementos for key in required_keys):
                st.session_state.elements = elementos
                st.success("Elementos generados exitosamente.")
            else:
                st.error("La respuesta JSON no contiene todas las claves necesarias.")
                st.write("### Respuesta JSON:")
                st.json(elementos)
        except json.JSONDecodeError:
            st.error("La respuesta de la API no está en formato JSON válido.")
            st.write("### Respuesta de la API:")
            st.write(resultado)
    else:
        st.error("No se pudo generar los elementos de la novela. Por favor, intenta de nuevo.")

# Función para generar una escena individual
def generar_escena(capitulo_numero, escena_numero, idea=None):
    if not (1 <= escena_numero <= 5):
        st.error("El número de escena debe estar entre 1 y 5.")
        return

    if len(st.session_state.chapters) < capitulo_numero - 1:
        st.error(f"El capítulo {capitulo_numero} aún no ha sido generado.")
        return

    if capitulo_numero == 0:
        st.error("El número de capítulo debe ser al menos 1.")
        return

    if capitulo_numero > len(st.session_state.chapters) + 1:
        st.error(f"No existe el capítulo {capitulo_numero}.")
        return

    if capitulo_numero == 1 and not st.session_state.elements:
        st.error("Primero debes generar los elementos de la novela.")
        return

    if idea:
        prompt = (
            f"Reescribe la **Escena {escena_numero}** del Capítulo {capitulo_numero} de la novela del género **{st.session_state.genre}**. "
            f"Basándote en la siguiente idea: {idea}\n\n"
            "Asegúrate de que los diálogos estén correctamente formateados utilizando la raya (—) y que cada diálogo sea claro y relevante para el desarrollo de la trama.\n"
            "Mantén el estilo narrativo coherente y atractivo."
        )
    else:
        # Si no se proporciona una idea, generar la escena basada en los elementos o el capítulo anterior
        if capitulo_numero == 1:
            prompt = (
                f"Genera la **Escena {escena_numero}** del Capítulo {capitulo_numero} de una novela del género **{st.session_state.genre}**. "
                "La escena debe tener aproximadamente **5000 tokens**. "
                "Incluye diálogos entre los personajes utilizando la raya (—) y mantén un estilo narrativo coherente y atractivo.\n\n"
                f"**Sinopsis:** {st.session_state.synopsis}\n"
                f"**Audiencia:** {st.session_state.audience}\n"
                f"**Personajes principales:** {st.session_state.elements.get('personajes_principales', '')}\n"
                f"**Trama:** {st.session_state.elements.get('trama', '')}\n"
                f"**Ambientación:** {st.session_state.elements.get('ambientacion', '')}\n"
                f"**Técnica narrativa:** {st.session_state.elements.get('tecnica_narrativa', '')}\n\n"
                "Asegúrate de que los diálogos estén correctamente formateados utilizando la raya (—) y que cada diálogo sea claro y relevante para el desarrollo de la trama."
            )
        else:
            ultimo_capitulo = st.session_state.chapters[capitulo_numero - 2]  # capitulo_numero -1 para 0 index
            prompt = (
                f"Basándote en el siguiente capítulo y la idea proporcionada, escribe la **Escena {escena_numero}** del Capítulo {capitulo_numero} de la novela del género **{st.session_state.genre}**. "
                "La escena debe tener aproximadamente **5000 tokens**. "
                "Incluye diálogos entre los personajes utilizando la raya (—) y mantén un estilo narrativo coherente y atractivo.\n\n"
                f"**Último Capítulo:**\n{ultimo_capitulo}\n\n"
                f"**Idea para la escena:** {idea if idea else 'Continuar la trama de manera coherente con el capítulo anterior.'}\n\n"
                "Asegúrate de que los diálogos estén correctamente formateados utilizando la raya (—) y que cada diálogo sea claro y relevante para el desarrollo de la trama."
            )

    with st.spinner(f"Generando Escena {escena_numero} del Capítulo {capitulo_numero}..."):
        resultado = call_openrouter_api(prompt, max_tokens=5000)  # Ajustado a 5000 tokens

    if resultado:
        # Actualizar o crear el capítulo con la nueva escena
        if len(st.session_state.chapters) < capitulo_numero:
            st.session_state.chapters.append("")

        capitulo = st.session_state.chapters[capitulo_numero - 1]

        # Crear el encabezado de la escena
        nueva_escena = f"### Escena {escena_numero}\n{resultado}\n\n"

        # Buscar si la escena ya existe usando regex
        pattern = re.compile(rf"### Escena {escena_numero}[\s\S]*?(?=### Escena \d|$)", re.MULTILINE)
        if pattern.search(capitulo):
            # Reemplazar la escena existente
            st.session_state.chapters[capitulo_numero - 1] = pattern.sub(nueva_escena, capitulo)
            st.success(f"Escena {escena_numero} del Capítulo {capitulo_numero} reescrita exitosamente.")
        else:
            # Añadir la nueva escena
            st.session_state.chapters[capitulo_numero - 1] += nueva_escena
            st.success(f"Escena {escena_numero} del Capítulo {capitulo_numero} generada exitosamente.")
    else:
        st.error(f"No se pudo generar la Escena {escena_numero} del Capítulo {capitulo_numero}. Por favor, intenta de nuevo.")

# Función para editar los elementos de la novela
def editar_elementos():
    st.subheader("📑 Editar Elementos de la Novela")
    
    with st.expander("Editar Género"):
        generos = [
            "Fantasía", "Ciencia Ficción", "Misterio", "Romance",
            "Terror", "Aventura", "Histórica", "Thriller", "Drama", "Comedia"
        ]
        selected_genre = st.selectbox(
            "Selecciona el género de tu novela:",
            generos,
            index=generos.index(st.session_state.genre) if st.session_state.genre in generos else 0,
            key="selectbox_genero_editar"
        )
        if st.session_state.genre != selected_genre:
            st.session_state.genre = selected_genre

    with st.expander("Editar Sinopsis"):
        sinopsis_editada = st.text_area("Sinopsis:", value=st.session_state.synopsis, height=200, key="text_area_sinopsis_editar")
        if sinopsis_editada.strip() != st.session_state.synopsis:
            st.session_state.synopsis = sinopsis_editada.strip()

    with st.expander("Editar Audiencia"):
        audiencia_editada = st.text_area("Audiencia (e.g., edad, intereses):", value=st.session_state.audience, height=100, key="text_area_audiencia_editar")
        if audiencia_editada.strip() != st.session_state.audience:
            st.session_state.audience = audiencia_editada.strip()

    with st.expander("Editar Personajes Principales"):
        personajes_editados = st.text_area("Personajes principales:", value=st.session_state.elements.get('personajes_principales', ''), height=150, key="text_area_personajes_editar")
        st.session_state.elements['personajes_principales'] = personajes_editados.strip()

    with st.expander("Editar Trama"):
        trama_editada = st.text_area("Trama:", value=st.session_state.elements.get('trama', ''), height=150, key="text_area_trama_editar")
        st.session_state.elements['trama'] = trama_editada.strip()

    with st.expander("Editar Ambientación"):
        ambientacion_editada = st.text_area("Ambientación:", value=st.session_state.elements.get('ambientacion', ''), height=150, key="text_area_ambientacion_editar")
        st.session_state.elements['ambientacion'] = ambientacion_editada.strip()

    with st.expander("Editar Técnica Narrativa"):
        tecnica_editada = st.text_area("Técnica narrativa:", value=st.session_state.elements.get('tecnica_narrativa', ''), height=150, key="text_area_tecnica_editar")
        st.session_state.elements['tecnica_narrativa'] = tecnica_editada.strip()

    if st.button("Guardar Cambios", key="guardar_cambios_btn"):
        st.success("Elementos actualizados exitosamente.")

# Función para ingresar la sinopsis
def ingresar_sinopsis():
    st.subheader("📄 Ingresar Sinopsis")
    sinopsis = st.text_area("Escribe una sinopsis para tu novela:", value=st.session_state.synopsis, height=200, key="text_area_sinopsis_ingresar")
    if sinopsis != st.session_state.synopsis:
        st.session_state.synopsis = sinopsis.strip()
        st.success("Sinopsis actualizada exitosamente.")

# Función para definir la audiencia
def definir_audiencia():
    st.subheader("🎯 Definir Audiencia")
    audiencia = st.text_area("Describe la audiencia objetivo para tu novela (por ejemplo, edad, intereses, género, etc.):", value=st.session_state.audience, height=100, key="text_area_audiencia_ingresar")
    if audiencia != st.session_state.audience:
        st.session_state.audience = audiencia.strip()
        st.success("Audiencia actualizada exitosamente.")

# Función para mostrar el estado de la sesión (para depuración)
def mostrar_estado():
    st.sidebar.markdown("## 📊 Estado de la Sesión")
    st.sidebar.write("### Género:")
    st.sidebar.write(st.session_state.genre)
    st.sidebar.write("### Sinopsis:")
    st.sidebar.write(st.session_state.synopsis)
    st.sidebar.write("### Audiencia:")
    st.sidebar.write(st.session_state.audience)
    st.sidebar.write("### Elementos:")
    st.sidebar.write(st.session_state.elements)
    st.sidebar.write("### Capítulos Generados:")
    st.sidebar.write(len(st.session_state.chapters))

# Función para reiniciar el estado de la sesión
def reiniciar_sesion():
    if st.sidebar.button("🔄 Reiniciar Proyecto", key="reset_project_btn"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.success("Proyecto reiniciado exitosamente.")
        st.experimental_rerun()

# Interfaz de la aplicación
st.header("📖 Genera tu Novela")

if not st.session_state.chapters:
    # Paso 0: Seleccionar el Género
    st.subheader("Paso 0: Seleccionar el Género de la Novela")
    generos = [
        "Fantasía", "Ciencia Ficción", "Misterio", "Romance",
        "Terror", "Aventura", "Histórica", "Thriller", "Drama", "Comedia"
    ]
    selected_genre = st.selectbox(
        "Selecciona el género de tu novela:",
        generos,
        index=generos.index(st.session_state.genre) if st.session_state.genre in generos else 0,
        key="selectbox_genero_paso0"
    )
    if st.session_state.genre != selected_genre:
        st.session_state.genre = selected_genre

    # Paso 1: Ingresar la Sinopsis
    ingresar_sinopsis()

    # Paso 2: Definir la Audiencia
    definir_audiencia()

    # Paso 3: Generar los Elementos de la Novela
    st.subheader("Paso 3: Generar Elementos de la Novela")
    if st.button("Generar Elementos", key="generar_elementos_btn"):
        generar_elementos()
    if st.session_state.elements:
        st.markdown("### **Elementos Generados:**")
        st.markdown(f"**Género:** {st.session_state.genre}")
        st.markdown(f"**Sinopsis:** {st.session_state.synopsis}")
        st.markdown(f"**Audiencia:** {st.session_state.audience}")
        st.markdown(f"**Personajes Principales:** {st.session_state.elements.get('personajes_principales', '')}")
        st.markdown(f"**Trama:** {st.session_state.elements.get('trama', '')}")
        st.markdown(f"**Ambientación:** {st.session_state.elements.get('ambientacion', '')}")
        st.markdown(f"**Técnica Narrativa:** {st.session_state.elements.get('tecnica_narrativa', '')}")
        st.markdown("---")
        # Opción para editar los elementos
        editar_elementos()
        # Paso 4: Generar el Primer Capítulo
        st.subheader("Paso 4: Generar el Primer Capítulo")
        if st.button("Generar Primer Capítulo", key="generar_primer_capitulo_btn"):
            # Generar las 5 escenas del primer capítulo
            for escena_numero in range(1, 6):
                generar_escena(capitulo_numero=1, escena_numero=escena_numero)
        if st.session_state.chapters:
            st.markdown("### **Capítulo 1:**")
            st.write(st.session_state.chapters[0])
else:
    # Generar capítulos adicionales
    st.subheader("Generar Nuevos Capítulos")
    st.markdown("### **Capítulo Anterior:**")
    st.write(st.session_state.chapters[-1])
    st.markdown("---")
    # Usamos un formulario para manejar mejor la entrada del usuario
    with st.form(key='idea_form'):
        idea = st.text_input("Ingresa una idea para el siguiente capítulo:", key="input_idea")
        submit_button = st.form_submit_button(label="Generar Siguiente Capítulo")
    if submit_button:
        if idea.strip() == "":
            st.error("La idea para el siguiente capítulo no puede estar vacía.")
        else:
            nuevo_capitulo_numero = len(st.session_state.chapters) + 1
            # Generar las 5 escenas del nuevo capítulo
            for escena_numero in range(1, 6):
                generar_escena(capitulo_numero=nuevo_capitulo_numero, escena_numero=escena_numero, idea=idea)
    if st.session_state.chapters:
        st.markdown(f"### **Capítulo {len(st.session_state.chapters)}:**")
        st.write(st.session_state.chapters[-1])

# Mostrar todos los capítulos generados con opción de reescribir
if st.session_state.chapters:
    st.sidebar.header("🔍 Navegar y Reescribir Capítulos")
    for idx, cap in enumerate(st.session_state.chapters, 1):
        with st.sidebar.expander(f"Capítulo {idx}"):
            st.markdown(cap)  # Usar markdown para mantener el formato de escenas
            # Botón para reescribir el capítulo
            if st.button(f"Reescribir Capítulo {idx}", key=f"reescribir_capitulo_{idx}"):
                # Mostrar un formulario para ingresar la nueva idea
                with st.expander(f"Reescribir Capítulo {idx}", expanded=True):
                    nueva_idea = st.text_input(f"Nueva idea para el Capítulo {idx}:", key=f"nueva_idea_{idx}")
                    if st.button(f"Actualizar Capítulo {idx}", key=f"actualizar_capitulo_{idx}"):
                        if nueva_idea.strip() == "":
                            st.error("La nueva idea no puede estar vacía.")
                        else:
                            # Reescribir cada escena del capítulo
                            for escena_numero in range(1, 6):
                                generar_escena(capitulo_numero=idx, escena_numero=escena_numero, idea=nueva_idea)
                            st.success(f"Capítulo {idx} reescrito exitosamente.")
                            st.experimental_rerun()

# Mostrar el estado de la sesión (opcional, para depuración)
mostrar_estado()

# Opción para reiniciar el proyecto
reiniciar_sesion()
