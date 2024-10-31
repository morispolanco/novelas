import streamlit as st
import requests
import json
from io import BytesIO
from docx import Document
import re

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

# Función para parsear el plan de la novela
def parse_plan(plan_text):
    plan = []
    chapters = re.split(r'Capítulo \d+:', plan_text)
    for chapter_text in chapters[1:]:
        chapter = []
        sections = re.split(r'Sección \d+:', chapter_text)
        for section_text in sections[1:]:
            lines = section_text.strip().split('\n', 1)
            if len(lines) >= 2:
                title = lines[0].strip()
                description = lines[1].strip()
                chapter.append({'titulo': title, 'descripcion': description})
        plan.append(chapter)
    return plan

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
            {"role": "user", "content": f"Planea una novela thriller política sobre el tema: '{tema}'. Debe tener 12 capítulos y 5 secciones por capítulo. Para cada sección, proporciona un título y una breve descripción de lo que sucede. Organiza la trama y las subtramas de manera coherente a lo largo de las 60 secciones. Formatea el plan claramente indicando 'Capítulo X:' y 'Sección Y:'."}
        ]
        respuesta = openrouter_api(messages)
        plan_texto = respuesta['choices'][0]['message']['content']
        st.session_state.plan_texto = plan_texto

        # Procesar el plan para almacenarlo en una estructura de datos
        st.session_state.plan = parse_plan(plan_texto)

        st.session_state.plan_generado = True

    # Mostrar el plan y solicitar aprobación
    st.subheader("Plan de la novela:")
    st.write(st.session_state.plan_texto)
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
        st.write("Generando descripciones detalladas de las escenas...")
        st.session_state.descripciones = []
        progress_bar = st.progress(0)
        total_secciones = 12 * 5
        contador = 0

        for capitulo_num, capitulo in enumerate(st.session_state.plan, start=1):
            capitulo_descripciones = []
            for seccion_num, seccion in enumerate(capitulo, start=1):
                titulo_seccion = seccion['titulo']
                descripcion_seccion = seccion['descripcion']
                messages = [
                    {"role": "user", "content": f"Detalle la escena para la Sección {seccion_num} del Capítulo {capitulo_num}, titulada '{titulo_seccion}'. Basándose en la siguiente descripción: {descripcion_seccion}. Asegúrese de que sea coherente con la trama general y evite frases cliché."}
                ]
                respuesta = openrouter_api(messages)
                detalle_seccion = respuesta['choices'][0]['message']['content']
                capitulo_descripciones.append({
                    'titulo': titulo_seccion,
                    'descripcion': descripcion_seccion,
                    'detalle': detalle_seccion
                })
                contador += 1
                progress_bar.progress(contador / total_secciones)
            st.session_state.descripciones.append(capitulo_descripciones)
        st.session_state.descripciones_generadas = True

    # Mostrar descripciones y solicitar aprobación
    st.subheader("Descripciones detalladas de las escenas:")
    for capitulo_num, capitulo in enumerate(st.session_state.descripciones, start=1):
        st.write(f"**Capítulo {capitulo_num}**")
        for seccion_num, seccion in enumerate(capitulo, start=1):
            st.write(f"Sección {seccion_num}: {seccion['titulo']}")
            st.write(seccion['detalle'])
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
        total_secciones = 12 * 5
        contador = 0

        for capitulo_num, capitulo in enumerate(st.session_state.descripciones, start=1):
            novela += f"\n\nCapítulo {capitulo_num}\n"
            for seccion_num, seccion in enumerate(capitulo, start=1):
                titulo_seccion = seccion['titulo']
                detalle_seccion = seccion['detalle']
                messages = [
                    {"role": "user", "content": f"Escribe la Sección {seccion_num} del Capítulo {capitulo_num}, titulada '{titulo_seccion}'. La escena debe tener aproximadamente 1000 palabras y seguir las características de un thriller político: mucha acción, ritmo rápido, descripciones vívidas y finales de escena con ganchos. Utiliza la siguiente descripción detallada: {detalle_seccion}. Usa raya en los diálogos y evita frases cliché."}
                ]
                respuesta = openrouter_api(messages)
                texto_seccion = respuesta['choices'][0]['message']['content']
                novela += f"\n\nSección {seccion_num}: {titulo_seccion}\n\n{texto_seccion}"
                contador += 1
                progress_bar.progress(contador / total_secciones)
        st.session_state.novela = novela
        st.session_state.novela_generada = True

    # Mostrar opción para descargar la novela
    st.subheader("Novela Generada")
    st.write("La novela ha sido generada exitosamente.")
    if st.button("Descargar Novela en Word"):
        doc = Document()
        doc.add_heading("Novela Thriller Política", 0)
        for line in st.session_state.novela.split('\n'):
            if line.strip() != '':
                doc.add_paragraph(line)
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        st.download_button(
            label="Descargar Documento",
            data=buffer,
            file_name="novela.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
