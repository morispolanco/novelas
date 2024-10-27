import streamlit as st
import time
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from io import BytesIO
import re
import random
import matplotlib.pyplot as plt
from together import Together

# Nuevas importaciones necesarias para agregar la tabla de contenidos
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# Inicializar el cliente de Together
client = Together()

# Configuración de la página
st.set_page_config(
    page_title="Generador de Novelas de Suspenso Político",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Título de la aplicación
st.title("Generador de Novelas de Suspenso Político")
st.write("""
Esta aplicación genera una novela en el género de thriller político.
Ingrese un tema y personalice el número de capítulos y escenas para crear una narrativa coherente y emocionante.
""")

# Barra lateral para opciones de usuario
st.sidebar.header("Configuración de la Novela")
num_capitulos = st.sidebar.slider("Número de capítulos", min_value=15, max_value=20, value=18)
num_escenas = st.sidebar.slider("Número de escenas por capítulo", min_value=4, max_value=6, value=5)
porcentaje_trama_principal = st.sidebar.slider("Porcentaje de palabras para la trama principal (%)", min_value=60, max_value=80, value=70)
porcentaje_subtramas = 100 - porcentaje_trama_principal
st.sidebar.write(f"Porcentaje de palabras para subtramas: {porcentaje_subtramas}%")

# Inicializar el estado de la aplicación
if 'etapa' not in st.session_state:
    st.session_state.etapa = "inicio"  # etapas: inicio, aprobacion, generacion, completado

if 'novela_completa' not in st.session_state:
    st.session_state.novela_completa = ""
if 'novela_doc' not in st.session_state:
    st.session_state.novela_doc = Document()

# Función para llamar a la API de Together y generar escenas
def call_together_api(prompt, max_tokens=1200, temperature=0.7, top_p=0.9, top_k=50, repetition_penalty=1.2):
    response = client.chat.completions.create(
        model="Qwen/Qwen2.5-7B-Instruct-Turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
        repetition_penalty=repetition_penalty,
        stop=["<|im_end|>"],
        stream=True
    )

    # Generación de respuesta en tiempo real
    respuesta_completa = ""
    output_text = st.empty()  # Espacio para mostrar la respuesta en tiempo real

    # Procesar cada token transmitido
    for token in response:
        if hasattr(token, 'choices'):
            content = token.choices[0].delta.content
            respuesta_completa += content
            output_text.write(respuesta_completa)  # Actualizar en Streamlit

    return respuesta_completa

# Función para generar cada escena y agregarla al documento de Word
def generar_escena(capitulo, escena, trama, subtramas, personajes, ambientacion, tecnica, palabras_trama, palabras_subtramas):
    prompt = f"""
Escribe la Escena {escena} del Capítulo {capitulo} de una novela de suspenso político de alta calidad con las siguientes características:

- **Trama Principal**: {trama}
- **Subtramas**: {subtramas}
- **Personajes**: {personajes}
- **Ambientación**: {ambientacion}
- **Técnicas Literarias**: {tecnica}

Asegúrate de mantener la coherencia y la cohesión en toda la escena, contribuyendo significativamente al desarrollo general de la novela.
"""
    # Llamar a la API para generar la escena
    escena_texto = call_together_api(prompt, max_tokens=1200, temperature=0.7, top_p=0.9, top_k=50, repetition_penalty=1.2)
    
    # Agregar la escena generada al contenido de la novela y al documento de Word
    st.session_state.novela_completa += f"### Escena {escena} (Capítulo {capitulo})\n\n{escena_texto}\n\n"

    # Añadir capítulo y escena al documento de Word
    st.session_state.novela_doc.add_heading(f"Capítulo {capitulo}", level=1)
    st.session_state.novela_doc.add_heading(f"Escena {escena}", level=2)
    for paragraph in escena_texto.split('\n'):
        st.session_state.novela_doc.add_paragraph(paragraph.strip())

    return escena_texto

# Función para generar la novela completa
def generar_novela_completa(num_capitulos, num_escenas, trama, subtramas, personajes, ambientacion, tecnica):
    for cap in range(1, num_capitulos + 1):
        for esc in range(1, num_escenas + 1):
            palabras_trama = 600  # Número estimado de palabras para la trama principal por escena
            palabras_subtramas = 200  # Número estimado de palabras para subtramas por escena

            with st.spinner(f"Generando Escena {esc} del Capítulo {cap}..."):
                escena_texto = generar_escena(cap, esc, trama, subtramas, personajes, ambientacion, tecnica, palabras_trama, palabras_subtramas)
                time.sleep(1)  # Retraso para evitar exceder los límites de la API

# Función para exportar la novela a Word
def exportar_a_word():
    buffer = BytesIO()
    st.session_state.novela_doc.save(buffer)
    buffer.seek(0)
    return buffer

# Interfaz de usuario principal
if st.session_state.etapa == "inicio":
    st.header("Configuración Inicial")
    theme = st.text_input("Ingrese el tema para su thriller político:", "")
    if st.button("Generar Elementos Iniciales"):
        if theme:
            # Llamar a la API para generar la estructura inicial (simplificado)
            st.session_state.trama = f"Trama principal basada en el tema: {theme}"
            st.session_state.subtramas = "Varias subtramas que complementan la historia principal."
            st.session_state.personajes = "Personajes complejos y bien desarrollados."
            st.session_state.ambientacion = "Ambientación acorde a la trama de suspenso político."
            st.session_state.tecnica = "Uso de técnicas literarias avanzadas."

            # Cambiar la etapa para empezar a generar la novela
            st.session_state.etapa = "generacion"
        else:
            st.error("Por favor, ingrese un tema.")

if st.session_state.etapa == "generacion":
    if st.button("Generar Novela Completa"):
        generar_novela_completa(num_capitulos, num_escenas, st.session_state.trama, st.session_state.subtramas, st.session_state.personajes, st.session_state.ambientacion, st.session_state.tecnica)
        st.session_state.etapa = "completado"

if st.session_state.etapa == "completado":
    st.success("Novela generada con éxito.")
    st.download_button(
        label="Descargar Novela en Word",
        data=exportar_a_word(),
        file_name="novela_thriller_politico.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    st.text_area("Novela Generada:", st.session_state.novela_completa, height=600)
