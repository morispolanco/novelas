import streamlit as st
import requests
import time
from docx import Document
from io import BytesIO
import nltk
from nltk.tokenize import sent_tokenize

# Descargar recursos de NLTK si no están ya descargados
nltk.download('punkt', quiet=True)

# Configuración de la página
st.set_page_config(
    page_title="📝 Generador de Obras de Ficción",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📝 Generador de Obras de Ficción")
st.write("Esta aplicación genera una obra de ficción basada en el prompt que ingreses, dividida en capítulos evitando la repetición de contenido.")

# Inicializar estado de la sesión
if 'capitulos' not in st.session_state:
    st.session_state.capitulos = []
if 'resumenes' not in st.session_state:
    st.session_state.resumenes = []
if 'informe_evaluacion' not in st.session_state:
    st.session_state.informe_evaluacion = None
if 'novela_regenerada' not in st.session_state:
    st.session_state.novela_regenerada = False
if 'titulo_obra' not in st.session_state:
    st.session_state.titulo_obra = "Obra de Ficción"
if 'proceso_generado' not in st.session_state:
    st.session_state.proceso_generado = False
if 'regenerate' not in st.session_state:
    st.session_state.regenerate = None

# Función para generar un capítulo de la obra
def generar_capitulo(prompt, capitulo_num, resumen_previas):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}"
    }
    # Instrucciones para evitar repeticiones
    instrucciones = (
        "Asegúrate de no repetir información ya mencionada en capítulos anteriores de la obra. "
        "Utiliza un lenguaje creativo y atractivo, desarrollando nuevos eventos, personajes o giros en la trama en cada capítulo."
    )
    if resumen_previas:
        resumen_texto = " Hasta ahora, la obra ha cubierto los siguientes puntos: " + resumen_previas
    else:
        resumen_texto = ""
    mensaje = (
        f"Escribe el capítulo {capitulo_num} de una obra de ficción sobre el siguiente tema: {prompt}. "
        f"El capítulo debe tener aproximadamente 1000 palabras y no debe contener subdivisiones ni subcapítulos.{resumen_texto} {instrucciones}"
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
        contenido = respuesta['choices'][0]['message']['content']
        return contenido
    except requests.exceptions.RequestException as e:
        st.error(f"Error al generar el capítulo {capitulo_num}: {e}")
        return None

# Función para resumir un capítulo utilizando la API de OpenRouter
def resumir_capitulo(capitulo):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}"
    }
    prompt_resumen = (
        "Proporciona un resumen conciso y relevante del siguiente capítulo de una obra de ficción. "
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
        resumen = respuesta['choices'][0]['message']['content']
        # Limpiar el resumen eliminando posibles saltos de línea adicionales
        resumen = ' '.join(resumen.split())
        return resumen
    except requests.exceptions.RequestException as e:
        st.error(f"Error al resumir el capítulo: {e}")
        return None

# Función para crear el documento Word
def crear_documento(capitulo_list, titulo):
    doc = Document()
    doc.add_heading(titulo, 0)
    for idx, capitulo in enumerate(capitulo_list, 1):
        doc.add_heading(f"Capítulo {idx}", level=1)
        doc.add_paragraph(capitulo)
    # Guardar el documento en un buffer
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# Función para evaluar críticamente la novela
def evaluar_novela(novela_completa):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}"
    }
    prompt_evaluacion = (
        "Evalúa críticamente la siguiente obra de ficción. Identifica errores narrativos, inconsistencias en la trama, desarrollo de personajes y otros aspectos que podrían mejorarse. "
        "Proporciona un informe detallado con puntos de mejora y sugerencias para cada aspecto identificado.\n\n"
        f"Obra de Ficción:\n{novela_completa}\n\nInforme de Evaluación:"
    )
    data = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": prompt_evaluacion
            }
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        respuesta = response.json()
        informe = respuesta['choices'][0]['message']['content']
        return informe
    except requests.exceptions.RequestException as e:
        st.error(f"Error al evaluar la novela: {e}")
        return None

# Función para regenerar la novela basada en el informe de evaluación
def regenerar_novela(prompt, informe_evaluacion, num_capitulos):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}"
    }
    # Instrucciones para regenerar la novela con mejoras
    mensaje = (
        f"Reescribe la obra de ficción basada en el siguiente tema: {prompt}. "
        f"Aplica las siguientes mejoras y sugerencias para corregir errores y enriquecer la trama y los personajes:\n\n{informe_evaluacion}\n\n"
        f"La obra debe estar dividida en {num_capitulos} capítulos, cada uno de aproximadamente 1000 palabras, manteniendo coherencia y creatividad."
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
        novela_regenerada = respuesta['choices'][0]['message']['content']
        return novela_regenerada
    except requests.exceptions.RequestException as e:
        st.error(f"Error al regenerar la novela: {e}")
        return None

# Interfaz de usuario para generar la obra
def generar_obra():
    if not st.session_state.proceso_generado:
        with st.form(key='form_obra'):
            prompt = st.text_area("Ingresa el tema o idea para la obra de ficción:", height=200)
            num_capitulos = st.slider("Número de capítulos:", min_value=5, max_value=20, value=10)
            submit_button = st.form_submit_button(label='Generar Obra')
            
        if submit_button:
            if not prompt.strip():
                st.error("Por favor, ingresa un tema o idea válida para la obra de ficción.")
            else:
                st.success("Iniciando la generación de la obra de ficción...")
                st.session_state.capitulos = []
                st.session_state.resumenes = []
                st.session_state.informe_evaluacion = None
                st.session_state.novela_regenerada = False
                st.session_state.titulo_obra = st.session_state.titulo_obra or "Obra de Ficción"
                st.session_state.proceso_generado = True
                st.session_state.prompt = prompt  # Guardar el prompt en el estado
                st.session_state.num_capitulos = num_capitulos  # Guardar el número de capítulos
                progreso = st.progress(0)
                for i in range(1, num_capitulos + 1):
                    st.write(f"Generando **Capítulo {i}**...")
                    # Crear un resumen de capítulos previos para evitar repeticiones
                    if st.session_state.resumenes:
                        resumen_previas = ' '.join(st.session_state.resumenes)
                    else:
                        resumen_previas = ''
                    capitulo = generar_capitulo(prompt, i, resumen_previas)
                    if capitulo:
                        st.session_state.capitulos.append(capitulo)
                        # Resumir el capítulo generado
                        resumen = resumir_capitulo(capitulo)
                        if resumen:
                            st.session_state.resumenes.append(resumen)
                        else:
                            st.warning(f"No se pudo generar un resumen para el Capítulo {i}.")
                    else:
                        st.error("La generación de la obra se ha detenido debido a un error.")
                        break
                    progreso.progress(i / num_capitulos)
                    time.sleep(5)  # Pausa de 5 segundos entre capítulos
                progreso.empty()
                if len(st.session_state.capitulos) == num_capitulos:
                    st.success("Obra de ficción generada exitosamente.")
                    st.session_state.titulo_obra = st.text_input("Título de la obra:", value=st.session_state.titulo_obra)
                    documento = crear_documento(st.session_state.capitulos, st.session_state.titulo_obra)
                    st.download_button(
                        label="Descargar Obra en Word",
                        data=documento,
                        file_name="obra_de_ficcion.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )

# Función para mostrar la evaluación y opciones de regeneración
def mostrar_evaluacion():
    if st.session_state.proceso_generado and not st.session_state.novela_regenerada:
        st.markdown("---")
        st.header("Evaluación Crítica de la Novela")
        if st.session_state.informe_evaluacion is None:
            evaluar_button = st.button("Evaluar la novela")
            if evaluar_button:
                with st.spinner("Evaluando la novela..."):
                    novela_completa = "\n\n".join(st.session_state.capitulos)
                    informe = evaluar_novela(novela_completa)
                    if informe:
                        st.session_state.informe_evaluacion = informe
                        st.experimental_rerun()
        else:
            st.subheader("Informe de Evaluación")
            st.write(st.session_state.informe_evaluacion)
            st.markdown("---")
            # Preguntar si desea regenerar la novela
            st.write("¿Deseas regenerar la novela basada en el informe de evaluación?")
            regenerate = st.radio(
                "",
                ("No", "Sí"),
                key='regenerate_option'
            )
            if regenerate == "Sí":
                st.session_state.regenerate = True
            else:
                st.session_state.regenerate = False

            if st.session_state.regenerate:
                regenerar_button = st.button("Regenerar la novela")
                if regenerar_button:
                    with st.spinner("Regenerando la novela con base en el informe..."):
                        novela_regen = regenerar_novela(
                            st.session_state.prompt,
                            st.session_state.informe_evaluacion,
                            st.session_state.num_capitulos
                        )
                        if novela_regen:
                            # Dividir la novela regenerada en capítulos
                            capitulos_regen = novela_regen.split("Capítulo ")
                            capitulos_regen = [cap.strip() for cap in capitulos_regen if cap.strip()]
                            # Re-formatear capítulos para que cada uno comience con "Capítulo X"
                            capitulos_regen = ["Capítulo " + cap for cap in capitulos_regen]
                            st.session_state.capitulos = capitulos_regen
                            st.session_state.resumenes = []  # Resetear resúmenes
                            st.session_state.informe_evaluacion = None  # Resetear informe
                            st.session_state.novela_regenerada = True
                            st.success("Novela regenerada exitosamente.")
                            st.experimental_rerun()

# Mostrar la novela regenerada si aplica
def mostrar_novela_regenerada():
    if st.session_state.novela_regenerada:
        st.markdown("---")
        st.header("📖 Novela Regenerada")
        # Mostrar los capítulos regenerados
        for idx, capitulo in enumerate(st.session_state.capitulos, 1):
            st.subheader(f"Capítulo {idx}")
            st.write(capitulo)
        # Ofrecer descarga de la novela regenerada
        titulo_obra_regen = st.text_input("Título de la obra (Regenerada):", value=f"{st.session_state.titulo_obra} (Regenerada)")
        if titulo_obra_regen:
            st.session_state.titulo_obra = titulo_obra_regen  # Actualizar título
        st.download_button(
            label="Descargar Novela Regenerada en Word",
            data=crear_documento(st.session_state.capitulos, st.session_state.titulo_obra),
            file_name="novela_regenerada.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

# Mostrar los capítulos generados inicialmente
def mostrar_novela():
    if st.session_state.capitulos and not st.session_state.novela_regenerada:
        st.markdown("---")
        st.header("📖 Novela Generada")
        # Mostrar los capítulos generados
        for idx, capitulo in enumerate(st.session_state.capitulos, 1):
            st.subheader(f"Capítulo {idx}")
            st.write(capitulo)

# Lógica principal de la aplicación
def main():
    generar_obra()
    mostrar_novela()
    mostrar_evaluacion()
    mostrar_novela_regenerada()

if __name__ == "__main__":
    main()
