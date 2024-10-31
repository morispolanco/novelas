import streamlit as st
import requests
import json
from io import BytesIO
from docx import Document

# Función para llamar a la API de OpenRouter
def openrouter_api(messages):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}"
    }
    data = {
        "model": "openai/gpt-4o-mini",
        "messages": messages
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.json()

# Título de la aplicación
st.title("Generador de Novelas Thriller Políticas")

# Paso 1: Ingreso del tema
tema = st.text_input("Introduce el tema principal de la novela:")

if tema:
    if 'plan_generado' not in st.session_state:
        st.session_state.plan_generado = False

    if not st.session_state.plan_generado:
        st.write("Generando el plan de la novela...")
        messages = [
            {"role": "user", "content": f"Planea una novela thriller política sobre el tema: '{tema}'. Debe tener 12 capítulos y 5 secciones por capítulo. Distribuye la trama y las subtramas en estas secciones y proporciona una descripción detallada de cada una."}
        ]
        respuesta = openrouter_api(messages)
        plan = respuesta['choices'][0]['message']['content']
        st.session_state.plan = plan
        st.session_state.plan_generado = True

    # Mostrar el plan y solicitar aprobación
    st.subheader("Plan de la novela:")
    st.write(st.session_state.plan)
    if 'aprobacion_plan' not in st.session_state:
        st.session_state.aprobacion_plan = False

    if not st.session_state.aprobacion_plan:
        if st.button("Aprobar Plan"):
            st.session_state.aprobacion_plan = True

# Paso 2: Generar descripciones de escenas
if 'aprobacion_plan' in st.session_state and st.session_state.aprobacion_plan:
    if 'descripciones_generadas' not in st.session_state:
        st.session_state.descripciones_generadas = False

    if not st.session_state.descripciones_generadas:
        st.write("Generando descripciones de las escenas...")
        messages = [
            {"role": "user", "content": f"Con base en el plan proporcionado, describe detalladamente qué pasa en cada una de las 60 secciones para asegurar coherencia y consistencia en la trama. No te extiendas demasiado en las descripciones y evita frases cliché."}
        ]
        respuesta = openrouter_api(messages)
        descripciones = respuesta['choices'][0]['message']['content']
        st.session_state.descripciones = descripciones
        st.session_state.descripciones_generadas = True

    # Mostrar descripciones y solicitar aprobación
    st.subheader("Descripciones de las escenas:")
    st.write(st.session_state.descripciones)
    if 'aprobacion_descripciones' not in st.session_state:
        st.session_state.aprobacion_descripciones = False

    if not st.session_state.aprobacion_descripciones:
        if st.button("Aprobar Descripciones"):
            st.session_state.aprobacion_descripciones = True

# Paso 3: Generar las secciones de la novela
if 'aprobacion_descripciones' in st.session_state and st.session_state.aprobacion_descripciones:
    if 'novela_generada' not in st.session_state:
        st.session_state.novela_generada = False

    if not st.session_state.novela_generada:
        st.write("Generando la novela...")
        progress_bar = st.progress(0)
        novela = ""
        for i in range(1, 61):
            messages = [
                {"role": "user", "content": f"Escribe la sección {i} de la novela. Esta sección debe tener aproximadamente 1000 palabras y seguir las características de un thriller político: mucha acción, ritmo rápido, descripciones vívidas y finales de escena con ganchos. Utiliza raya en los diálogos y evita frases cliché."}
            ]
            respuesta = openrouter_api(messages)
            seccion = respuesta['choices'][0]['message']['content']
            novela += f"\n\nSección {i}:\n{seccion}"
            progress_bar.progress(i / 60)
        st.session_state.novela = novela
        st.session_state.novela_generada = True

    # Mostrar opción para descargar la novela
    st.subheader("Novela Generada")
    st.write("La novela ha sido generada exitosamente.")
    if st.button("Descargar Novela en Word"):
        doc = Document()
        doc.add_heading("Novela Thriller Política", 0)
        doc.add_paragraph(st.session_state.novela)
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        st.download_button(
            label="Descargar Documento",
            data=buffer,
            file_name="novela.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
