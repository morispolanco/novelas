import streamlit as st
import requests
import json
import time

# Configuración de la página
st.set_page_config(
    page_title="Generador de Novelas de Suspenso Político",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Título de la aplicación
st.title("Generador de Novelas de Suspenso Político")
st.write("""
Esta aplicación genera una novela de 12 capítulos y 3 escenas por capítulo en el género de thriller político. 
Ingrese un tema y deje que la inteligencia artificial cree una narrativa coherente y emocionante.
""")

# Función para llamar a la API de Together
def call_together_api(prompt):
    api_url = "https://api.together.xyz/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {st.secrets['TOGETHER_API_KEY']}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "Qwen/Qwen2.5-7B-Instruct-Turbo",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2500,
        "temperature": 0.7,
        "top_p": 0.7,
        "top_k": 50,
        "repetition_penalty": 1,
        "stop": ["[\"<|eot_id|>\"]"],
        "stream": False
    }
    response = requests.post(api_url, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        return response.json().get("choices")[0].get("message").get("content")
    else:
        st.error(f"Error en la API: {response.status_code} - {response.text}")
        return None

# Función para generar la estructura inicial de la novela
def generar_estructura(theme):
    prompt = f"""
    Basado en el tema proporcionado, genera lo siguiente para una novela de suspenso político:
    - Título
    - Trama
    - Personajes (incluyendo nombres, descripciones, motivaciones)
    - Ambientación
    - Técnicas literarias a utilizar

    Tema: {theme}

    Asegúrate de que todo sea coherente y adecuado para un thriller político.
    """
    estructura = call_together_api(prompt)
    return estructura

# Función para generar cada escena
def generar_escena(capitulo, escena, trama, personajes, ambientacion, tecnica):
    prompt = f"""
    Escribe la Escena {escena} del Capítulo {capitulo} de una novela de suspenso político con las siguientes características:

    Trama: {trama}
    Personajes: {personajes}
    Ambientación: {ambientacion}
    Técnicas literarias: {tecnica}

    La escena debe tener al menos 2000 palabras, mantener la consistencia y coherencia, evitar clichés y frases hechas. 
    Debe incluir descripciones vívidas, diálogos agudos y dinámicos, y contribuir al desarrollo de la trama y los personajes.
    """
    escena_texto = call_together_api(prompt)
    return escena_texto

# Función para generar la novela completa
def generar_novela(theme):
    with st.spinner("Generando la estructura de la novela..."):
        estructura = generar_estructura(theme)
        if not estructura:
            st.error("No se pudo generar la estructura de la novela.")
            return None

    st.subheader("Estructura de la Novela")
    st.text(estructura)

    # Aquí se podría parsear la estructura para extraer título, trama, etc.
    # Para simplificar, asumiremos que la estructura viene en un formato reconocible.

    # Por ejemplo, supongamos que la estructura está en formato de lista:
    # Título: ...
    # Trama: ...
    # Personajes: ...
    # Ambientación: ...
    # Técnicas literarias: ...

    # Dividir la estructura en líneas
    lineas = estructura.split('\n')
    titulo = ""
    trama = ""
    personajes = ""
    ambientacion = ""
    tecnica = ""

    for linea in lineas:
        if linea.lower().startswith("título"):
            titulo = linea.split(":", 1)[1].strip()
        elif linea.lower().startswith("trama"):
            trama = linea.split(":", 1)[1].strip()
        elif linea.lower().startswith("personajes"):
            personajes = linea.split(":", 1)[1].strip()
        elif linea.lower().startswith("ambientación"):
            ambientacion = linea.split(":", 1)[1].strip()
        elif linea.lower().startswith("técnicas literarias"):
            tecnica = linea.split(":", 1)[1].strip()

    st.subheader("Título")
    st.write(titulo)

    st.subheader("Trama")
    st.write(trama)

    st.subheader("Personajes")
    st.write(personajes)

    st.subheader("Ambientación")
    st.write(ambientacion)

    st.subheader("Técnicas Literarias")
    st.write(tecnica)

    novela = f"**{titulo}**\n\n"

    for cap in range(1, 13):
        novela += f"## Capítulo {cap}\n\n"
        for esc in range(1, 4):
            with st.spinner(f"Generando Capítulo {cap}, Escena {esc}..."):
                escena = generar_escena(cap, esc, trama, personajes, ambientacion, tecnica)
                if not escena:
                    st.error(f"No se pudo generar la Escena {esc} del Capítulo {cap}.")
                    return None
            novela += f"### Escena {esc}\n\n{escena}\n\n"
            # Para evitar exceder los límites de la API, podríamos agregar un pequeño retraso
            time.sleep(1)

    return novela

# Interfaz de usuario
theme = st.text_input("Ingrese el tema para su thriller político:", "")

if st.button("Generar Novela"):
    if not theme:
        st.error("Por favor, ingrese un tema.")
    else:
        novela_completa = generar_novela(theme)
        if novela_completa:
            st.success("Novela generada con éxito.")
            st.download_button(
                label="Descargar Novela",
                data=novela_completa,
                file_name=f"novela_thriller_politico_{int(time.time())}.txt",
                mime="text/plain"
            )
            st.text_area("Novela Generada:", novela_completa, height=600)
