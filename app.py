import streamlit as st
import requests
import re

# Configuración de la página
st.set_page_config(page_title="Asistente para Escribir Novelas", layout="wide")

# Título de la aplicación
st.title("📚 Asistente para Escribir tu Novela Capítulo por Capítulo")

# Función para llamar a la API de Together
def call_together_api(messages):
    api_url = "https://api.together.xyz/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {st.secrets['TOGETHER_API_KEY']}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "messages": messages,
        "max_tokens": 4000,  # Ajustado a un valor razonable
        "temperature": 0.7,
        "top_p": 0.7,
        "top_k": 50,
        "repetition_penalty": 1,
        "stop": ["<|eot_id|>"],
        "stream": False
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        # Asegurarse de que la respuesta tiene el formato esperado
        return data['choices'][0]['message']['content'].strip()
    except requests.exceptions.RequestException as e:
        st.error(f"Error en la llamada a la API: {e}")
        return None
    except (KeyError, IndexError) as e:
        st.error(f"Formato inesperado de la respuesta de la API: {e}")
        return None

# Inicialización del estado de la sesión
if 'elements' not in st.session_state:
    st.session_state.elements = {}
if 'chapters' not in st.session_state:
    st.session_state.chapters = []
if 'genre' not in st.session_state:
    st.session_state.genre = None

# Función para generar los elementos fundamentales
def generar_elementos():
    if not st.session_state.genre:
        st.error("Por favor, selecciona un género antes de generar los elementos.")
        return
    prompt = (
        f"Necesito que me ayudes a crear una novela del género **{st.session_state.genre}**. "
        "Por favor, genera los siguientes elementos:\n"
        "1. **Personajes principales:** Describe al menos tres personajes principales con sus características.\n"
        "2. **Trama:** Esboza la trama principal de la novela.\n"
        "3. **Ambientación:** Describe el mundo o entorno donde se desarrolla la historia.\n"
        "4. **Técnica narrativa:** Indica el punto de vista y el estilo narrativo que se utilizará.\n"
    )
    messages = [
        {"role": "system", "content": "Eres un asistente creativo que ayuda a escribir novelas."},
        {"role": "user", "content": prompt}
    ]
    with st.spinner("Generando elementos de la novela..."):
        resultado = call_together_api(messages)
    if resultado:
        # Parsear el resultado asumiendo que está en formato Markdown
        try:
            elementos = {}
            # Utilizamos expresiones regulares para extraer las secciones
            personajes_match = re.search(r"\*\*Personajes principales:\*\*\s*(.*)", resultado, re.DOTALL)
            trama_match = re.search(r"\*\*Trama:\*\*\s*(.*)", resultado, re.DOTALL)
            ambientacion_match = re.search(r"\*\*Ambientación:\*\*\s*(.*)", resultado, re.DOTALL)
            tecnica_match = re.search(r"\*\*Técnica narrativa:\*\*\s*(.*)", resultado, re.DOTALL)

            if personajes_match:
                elementos['personajes'] = personajes_match.group(1).strip()
            if trama_match:
                elementos['trama'] = trama_match.group(1).strip()
            if ambientacion_match:
                elementos['ambientacion'] = ambientacion_match.group(1).strip()
            if tecnica_match:
                elementos['tecnica_narrativa'] = tecnica_match.group(1).strip()

            if elementos:
                st.session_state.elements = elementos
                st.success("Elementos generados exitosamente.")
            else:
                st.error("No se pudieron extraer los elementos de la respuesta de la API.")
        except Exception as e:
            st.error(f"Error al procesar los elementos: {e}")

# Función para generar un capítulo
def generar_capitulo(idea=None):
    if not st.session_state.chapters:
        # Generar el primer capítulo basado en los elementos
        if not st.session_state.elements:
            st.error("Primero debes generar los elementos de la novela.")
            return
        prompt = (
            f"Usa los siguientes elementos para escribir el primer capítulo de una novela del género **{st.session_state.genre}**. "
            "El capítulo debe ser tres veces más largo de lo habitual, incluir diálogos entre los personajes utilizando la raya (—) y mantener un estilo narrativo coherente y atractivo.\n\n"
            f"**Personajes principales:** {st.session_state.elements.get('personajes', '')}\n"
            f"**Trama:** {st.session_state.elements.get('trama', '')}\n"
            f"**Ambientación:** {st.session_state.elements.get('ambientacion', '')}\n"
            f"**Técnica narrativa:** {st.session_state.elements.get('tecnica_narrativa', '')}\n"
            "Escribe un capítulo detallado y atractivo siguiendo las indicaciones anteriores."
        )
    else:
        # Generar capítulos subsecuentes basados en el anterior y la idea del usuario
        if not idea:
            st.error("Por favor, proporciona una idea para el siguiente capítulo.")
            return
        ultimo_capitulo = st.session_state.chapters[-1]
        prompt = (
            f"Basándote en el siguiente capítulo y la idea proporcionada, escribe el siguiente capítulo de la novela del género **{st.session_state.genre}**. "
            "El capítulo debe ser tres veces más largo de lo habitual, incluir diálogos entre los personajes utilizando la raya (—) y mantener un estilo narrativo coherente y atractivo.\n\n"
            f"**Último Capítulo:**\n{ultimo_capitulo}\n\n"
            f"**Idea para el siguiente capítulo:** {idea}\n\n"
            "Escribe el siguiente capítulo de manera coherente y creativa siguiendo las indicaciones anteriores."
        )
    messages = [
        {"role": "system", "content": "Eres un escritor creativo que ayuda a desarrollar novelas."},
        {"role": "user", "content": prompt}
    ]
    with st.spinner("Generando capítulo..."):
        resultado = call_together_api(messages)
    if resultado:
        st.session_state.chapters.append(resultado)
        st.success("Capítulo generado exitosamente.")

# Función para editar los elementos de la novela
def editar_elementos():
    st.subheader("📑 Editar Elementos de la Novela")
    with st.expander("Editar Personajes Principales"):
        elementos_editados = st.text_area("Personajes principales:", value=st.session_state.elements.get('personajes', ''), height=150)
        st.session_state.elements['personajes'] = elementos_editados.strip()

    with st.expander("Editar Trama"):
        trama_editada = st.text_area("Trama:", value=st.session_state.elements.get('trama', ''), height=150)
        st.session_state.elements['trama'] = trama_editada.strip()

    with st.expander("Editar Ambientación"):
        ambientacion_editada = st.text_area("Ambientación:", value=st.session_state.elements.get('ambientacion', ''), height=150)
        st.session_state.elements['ambientacion'] = ambientacion_editada.strip()

    with st.expander("Editar Técnica Narrativa"):
        tecnica_editada = st.text_area("Técnica narrativa:", value=st.session_state.elements.get('tecnica_narrativa', ''), height=150)
        st.session_state.elements['tecnica_narrativa'] = tecnica_editada.strip()

    if st.button("Guardar Cambios", key="guardar_cambios_btn"):
        st.success("Elementos actualizados exitosamente.")

# Interfaz de la aplicación
st.header("📖 Genera tu Novela")

if not st.session_state.chapters:
    # Paso 0: Seleccionar el Género
    st.subheader("Paso 0: Seleccionar el Género de la Novela")
    generos = [
        "Fantasía", "Ciencia Ficción", "Misterio", "Romance",
        "Terror", "Aventura", "Histórica", "Thriller", "Drama", "Comedia"
    ]
    # Utilizamos una variable temporal para evitar sobrescribir en cada interacción
    selected_genre = st.selectbox("Selecciona el género de tu novela:", generos, index=generos.index(st.session_state.genre) if st.session_state.genre in generos else 0)
    if st.session_state.genre != selected_genre:
        st.session_state.genre = selected_genre

    # Paso 1: Generar los Elementos de la Novela
    st.subheader("Paso 1: Generar Elementos de la Novela")
    if st.button("Generar Elementos", key="generar_elementos_btn"):
        generar_elementos()
    if st.session_state.elements:
        st.markdown("### **Elementos Generados:**")
        st.markdown(f"**Género:** {st.session_state.genre}")
        st.markdown(f"**Personajes Principales:** {st.session_state.elements.get('personajes', '')}")
        st.markdown(f"**Trama:** {st.session_state.elements.get('trama', '')}")
        st.markdown(f"**Ambientación:** {st.session_state.elements.get('ambientacion', '')}")
        st.markdown(f"**Técnica Narrativa:** {st.session_state.elements.get('tecnica_narrativa', '')}")
        st.markdown("---")
        # Opción para editar los elementos
        editar_elementos()
        # Paso 2: Generar el Primer Capítulo
        st.subheader("Paso 2: Generar el Primer Capítulo")
        if st.button("Generar Primer Capítulo", key="generar_primer_capitulo_btn"):
            generar_capitulo()
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
        idea = st.text_input("Ingresa una idea para el siguiente capítulo:")
        submit_button = st.form_submit_button(label="Generar Siguiente Capítulo")
    if submit_button:
        generar_capitulo(idea=idea)
    if st.session_state.chapters:
        st.markdown(f"### **Capítulo {len(st.session_state.chapters)}:**")
        st.write(st.session_state.chapters[-1])

# Mostrar todos los capítulos generados
if st.session_state.chapters:
    st.sidebar.header("🔍 Navegar por los Capítulos")
    for idx, cap in enumerate(st.session_state.chapters, 1):
        with st.sidebar.expander(f"Capítulo {idx}"):
            st.write(cap)
