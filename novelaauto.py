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
        sections = re.split(r'Escena \d+:', chapter_text)
        for section_text in sections[1:]:
            lines = section_text.strip().split('\n', 1)
            if len(lines) >= 2:
                title = lines[0].strip()
                description = lines[1].strip()
                chapter.append({'titulo': title, 'descripcion': description})
        plan.append(chapter)
    return plan

# Título de la aplicación
st.title("Generador de Novelas Juveniles de Aventuras")

# Paso 1: Ingreso del tema
tema = st.text_input("Introduce el tema principal de la novela:")

if tema:
    if 'plan_generado' not in st.session_state:
        st.session_state.plan_generado = False

    if not st.session_state.plan_generado:
        st.write("Generando el plan de la novela...")
        messages = [
            {"role": "user", "content": f"Planea una novela juvenil de aventuras sobre el tema: '{tema}'. Debe tener 10 capítulos y 3 escenas por capítulo. Para cada escena, proporciona un título y una breve descripción de lo que sucede. Organiza la trama y las subtramas de manera coherente a lo largo de las 30 escenas. Formatea el plan claramente indicando 'Capítulo X:' y 'Escena Y:'."}
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
        total_secciones = 10 * 3
        contador = 0

        for capitulo_num, capitulo in enumerate(st.session_state.plan, start=1):
            capitulo_descripciones = []
            for escena_num, escena in enumerate(capitulo, start=1):
                titulo_escena = escena['titulo']
                descripcion_escena = escena['descripcion']
                messages = [
                    {"role": "user", "content": f"Detalle la escena para la Escena {escena_num} del Capítulo {capitulo_num}, titulada '{titulo_escena}'. Basándose en la siguiente descripción: {descripcion_escena}. Asegúrese de que sea coherente con la trama general y evite frases cliché."}
                ]
                respuesta = openrouter_api(messages)
                detalle_escena = respuesta['choices'][0]['message']['content']
                capitulo_descripciones.append({
                    'titulo': titulo_escena,
                    'descripcion': descripcion_escena,
                    'detalle': detalle_escena
                })
                contador += 1
                progress_bar.progress(contador / total_secciones)
            st.session_state.descripciones.append(capitulo_descripciones)
        st.session_state.descripciones_generadas = True

    # Mostrar descripciones y solicitar aprobación
    st.subheader("Descripciones detalladas de las escenas:")
    for capitulo_num, capitulo in enumerate(st.session_state.descripciones, start=1):
        st.write(f"**Capítulo {capitulo_num}**")
        for escena_num, escena in enumerate(capitulo, start=1):
            st.write(f"Escena {escena_num}: {escena['titulo']}")
            st.write(escena['detalle'])
    if 'aprobacion_descripciones' not in st.session_state:
        st.session_state.aprobacion_descripciones = False

    if not st.session_state.aprobacion_descripciones:
        if st.button("Aprobar Descripciones"):
            st.session_state.aprobacion_descripciones = True

# Paso 3: Generar las escenas de la novela
if 'aprobacion_descripciones' in st.session_state and st.session_state.aprobacion_descripciones:
    if 'novela_generada' not in st.session_state:
        st.session_state.novela_generada = False

    if not st.session_state.novela_generada:
        st.write("Generando la novela...")
        progress_bar = st.progress(0)
        novela = ""
        total_secciones = 10 * 3
        contador = 0

        for capitulo_num, capitulo in enumerate(st.session_state.descripciones, start=1):
            novela += f"\n\nCapítulo {capitulo_num}\n"
            for escena_num, escena in enumerate(capitulo, start=1):
                titulo_escena = escena['titulo']
                detalle_escena = escena['detalle']
                messages = [
                    {"role": "user", "content": f"Escribe la Escena {escena_num} del Capítulo {capitulo_num}, titulada '{titulo_escena}'. La escena debe tener aproximadamente 1000 palabras y seguir las características de una novela juvenil de aventuras: lenguaje accesible, tono emocionante, descripciones vívidas y finales de escena que mantengan el interés del lector. Utiliza la siguiente descripción detallada: {detalle_escena}. Usa raya en los diálogos y evita frases cliché."}
                ]
                respuesta = openrouter_api(messages)
                texto_escena = respuesta['choices'][0]['message']['content']
                novela += f"\n\nEscena {escena_num}: {titulo_escena}\n\n{texto_escena}"
                contador += 1
                progress_bar.progress(contador / total_secciones)
        st.session_state.novela = novela
        st.session_state.novela_generada = True

    # Mostrar opción para descargar la novela
    st.subheader("Novela Generada")
    st.write("La novela ha sido generada exitosamente.")
    if st.button("Descargar Novela en Word"):
        doc = Document()
        doc.add_heading("Novela Juvenil de Aventuras", 0)
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
