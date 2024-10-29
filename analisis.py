import streamlit as st
import requests
import json
from docx import Document
from docx.shared import Pt
from io import BytesIO

# Configuración de la página
st.set_page_config(
    page_title="Analizador de Novelas",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Título de la aplicación
st.title("📚 Analizador de Novelas Escena por Escena")

# Instrucciones
st.markdown("""
Esta aplicación permite subir una novela en formato de texto (.txt), analizar cada escena en busca de errores y posibles mejoras, y generar un informe completo en un documento de Word.

**Pasos a seguir:**
1. Sube tu novela en formato de texto.
2. Haz clic en "Iniciar Análisis".
3. Espera mientras se analiza cada escena.
4. Descarga el informe generado.
""")

# Función para dividir el texto en escenas
def dividir_en_escenas(texto):
    """
    Divide el texto en escenas basándose en delimitadores comunes como 'Escena', 'Scene', etc.
    Puedes ajustar los delimitadores según la estructura de tu novela.
    """
    import re
    # Suponiendo que cada escena comienza con 'Escena' o 'Scene' seguido de un número
    escenas = re.split(r'(?:Escena|Scene)\s+\d+', texto, flags=re.IGNORECASE)
    # El primer elemento puede ser vacío o una introducción, lo omitimos
    escenas = [escena.strip() for escena in escenas if escena.strip()]
    return escenas

# Función para analizar una escena utilizando OpenRouter API
def analizar_escena(escena, api_key):
    """
    Envía una escena a la API de OpenRouter para su análisis.
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": f"Analiza la siguiente escena en busca de errores y sugiere mejoras:\n\n{escena}"
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()
        # Asumiendo que la respuesta está en 'choices' y 'message' según la estructura de OpenAI
        analisis = result['choices'][0]['message']['content']
        return analisis
    except requests.exceptions.RequestException as e:
        st.error(f"Error en la API: {e}")
        return "Error en el análisis de esta escena."

# Función para generar el informe en Word
def generar_informe(analisis_por_escena):
    """
    Genera un documento de Word con el análisis de todas las escenas.
    """
    document = Document()
    document.add_heading('Informe de Análisis de Novela', 0)

    for idx, analisis in enumerate(analisis_por_escena, 1):
        document.add_heading(f'Escena {idx}', level=1)
        p = document.add_paragraph(analisis)
        p.style.font.size = Pt(12)

    # Guardar el documento en un buffer
    buffer = BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer

# Interfaz de usuario
uploaded_file = st.file_uploader("Sube tu novela en formato .txt", type=["txt"])

if uploaded_file is not None:
    # Leer el contenido del archivo
    try:
        contenido = uploaded_file.read().decode('utf-8')
    except UnicodeDecodeError:
        st.error("El archivo debe estar en formato de texto UTF-8.")
        st.stop()

    # Mostrar una vista previa
    st.subheader("Vista Previa del Contenido")
    st.text_area("Contenido de la Novela", contenido, height=300)

    # Botón para iniciar el análisis
    if st.button("Iniciar Análisis"):
        with st.spinner("Dividiendo la novela en escenas..."):
            escenas = dividir_en_escenas(contenido)
            num_escenas = len(escenas)
            if num_escenas == 0:
                st.error("No se encontraron escenas en el texto. Asegúrate de que las escenas estén correctamente delimitadas.")
                st.stop()

        st.success(f"Se han encontrado {num_escenas} escenas. Iniciando el análisis...")

        # Barra de progreso
        progress_bar = st.progress(0)
        progreso_text = st.empty()

        # Obtener la clave de la API desde los secretos
        api_key = st.secrets["OPENROUTER_API_KEY"]

        analisis_resultados = []

        for idx, escena in enumerate(escenas, 1):
            analisis = analizar_escena(escena, api_key)
            analisis_resultados.append(analisis)
            # Actualizar la barra de progreso
            progress = idx / num_escenas
            progress_bar.progress(progress)
            progreso_text.text(f"Analizando escena {idx} de {num_escenas}...")

        progreso_text.text("Análisis completado.")
        progress_bar.empty()

        # Generar el informe
        with st.spinner("Generando el informe en Word..."):
            informe = generar_informe(analisis_resultados)

        st.success("El informe ha sido generado exitosamente.")

        # Botón para descargar el informe
        st.download_button(
            label="Descargar Informe en Word",
            data=informe,
            file_name="Informe_Analisis_Novela.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
