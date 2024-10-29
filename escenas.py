import streamlit as st
import requests
from docx import Document
from io import BytesIO

# Configuración de la API Key
OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Función para generar el contenido de cada escena
def generar_escena(tema, capitulo, escena):
    prompt = f"Escribe una escena de una novela original de cuarenta mil palabras sobre el tema '{tema}'. \
Capítulo {capitulo}, Escena {escena}. Incluye descripciones detalladas, diálogos con raya en cada intervención de los personajes, \
y desarrolla las motivaciones de los personajes. Mantén un ritmo trepidante."

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}"
    }
    data = {
        "model": "openai/gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }

    response = requests.post(API_URL, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        st.error("Error al generar la escena. Por favor, intenta de nuevo.")
        return None

# Función para generar toda la novela con barra de progreso
def generar_novela(tema):
    document = Document()
    progreso_total = 10 * 4  # 10 capítulos, 4 escenas por capítulo
    progreso_actual = 0

    # Agregar barra de progreso en Streamlit
    barra_progreso = st.progress(0)
    for capitulo in range(1, 11):
        document.add_paragraph(f"Capítulo {capitulo}", style="Heading 1")
        for escena in range(1, 5):
            escena_texto = generar_escena(tema, capitulo, escena)
            if escena_texto:
                document.add_paragraph(escena_texto)
                progreso_actual += 1
                barra_progreso.progress(progreso_actual / progreso_total)
            else:
                st.error(f"No se pudo generar la Escena {escena} del Capítulo {capitulo}.")
                break

    # Guardar el documento en un archivo Word
    buffer = BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer

# Interfaz de la aplicación
st.title("Generador de Novelas en Streamlit")
st.write("Introduce el tema de la novela para generar una historia original dividida en diez capítulos y exportar el resultado en un archivo Word.")

# Entrada del usuario para el tema de la novela
tema = st.text_input("Tema de la novela", help="Introduce el tema principal para la novela.")

# Botón para iniciar la generación de la novela
if st.button("Generar Novela"):
    if tema:
        st.info("Generando novela... puede tardar unos minutos.")
        buffer = generar_novela(tema)
        st.success("¡Novela generada exitosamente!")
        st.download_button(
            label="Descargar Novela en Word",
            data=buffer,
            file_name="novela_generada.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    else:
        st.warning("Por favor, introduce un tema para la novela.")
