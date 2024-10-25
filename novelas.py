import streamlit as st
import requests
from io import BytesIO
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import json
import random

# =====================
# Configuración Inicial
# =====================

OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-4o-mini"

# =====================
# Funciones Auxiliares
# =====================

def generar_contenido(prompt, max_tokens=3000, temperature=0.7, repetition_penalty=1.2, frequency_penalty=0.5):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}"
    }
    data = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "repetition_penalty": repetition_penalty,
        "frequency_penalty": frequency_penalty
    }
    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=120)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"Error: {e}")
        return ""

def exportar_a_docx(contenido_novela):
    doc = Document()
    try:
        sections = doc.sections
        for section in sections:
            section.page_width = Inches(5)
            section.page_height = Inches(8)
            section.top_margin = Inches(0.7)
            section.bottom_margin = Inches(0.5)
            section.left_margin = Inches(0.7)
            section.right_margin = Inches(0.5)

        style_normal = doc.styles['Normal']
        font_normal = style_normal.font
        font_normal.name = 'Alegreya'
        font_normal.size = Pt(12)
        style_normal.element.rPr.rFonts.set(qn('w:eastAsia'), 'Alegreya')

        for linea in contenido_novela.split('\n'):
            linea = linea.strip()
            if not linea:
                continue

            if linea.startswith("Capítulo"):
                p = doc.add_heading(linea, level=2)
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                p.paragraph_format.line_spacing = 1.15
                p.paragraph_format.space_after = Pt(120)
            else:
                p = doc.add_paragraph(linea, style='Normal')
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                p.paragraph_format.line_spacing = 1.15
                p.paragraph_format.space_after = Pt(9)

        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"Error al formatear el documento DOCX: {e}")
        return None

# =====================
# Cacheo de Funciones
# =====================

@st.cache_data(show_spinner=False, ttl=3600)
def generar_contenido_cache(prompt, max_tokens=3000, temperature=0.7, repetition_penalty=1.2, frequency_penalty=0.5):
    return generar_contenido(prompt, max_tokens, temperature, repetition_penalty, frequency_penalty)

# =====================
# Implementación de Mejoras
# =====================

def generar_resumen_capitulo(capitulo_num, contenido_escenas):
    prompt_resumen = (
        f"Genera un resumen coherente para el capítulo {capitulo_num} basado en las siguientes escenas:\n\n"
        f"{contenido_escenas}\n\n"
        f"El resumen debe capturar los eventos clave, decisiones de los personajes y las transiciones importantes en la trama."
    )
    return generar_contenido_cache(prompt_resumen, max_tokens=500)

def actualizar_detalles_personajes(capitulo_num, contenido_escenas):
    for personaje in st.session_state.personajes:
        prompt_actualizacion = (
            f"Basado en los eventos del capítulo {capitulo_num}, describe cómo han cambiado las decisiones, "
            f"emociones y eventos clave del personaje **{personaje['nombre']}**.\n\n"
            f"Escenas:\n{contenido_escenas}"
        )
        detalles_actualizados = generar_contenido_cache(prompt_actualizacion, max_tokens=200)
        if detalles_actualizados:
            personaje['decisiones'].append(detalles_actualizados.get('decisiones', 'Sin cambios'))
            personaje['emociones'].append(detalles_actualizados.get('emociones', 'Sin cambios'))
            personaje['eventos'].append(detalles_actualizados.get('eventos', 'Sin cambios'))

def generar_escenas_batch(capitulo_num, titulo_capitulo, personajes, resumen_anterior, num_escenas):
    escenas_prompts = []
    for escena_num in range(1, num_escenas + 1):
        inicio = obtener_inicio_escena()
        escenas_prompts.append(
            f"{inicio} la escena {escena_num} del {titulo_capitulo}. Asegúrate de que la trama se conecte con las decisiones "
            f"y emociones de los personajes y que siga los eventos previos y futuros.\n\n"
            f"Resumen del capítulo anterior:\n{resumen_anterior}\n\n"
            f"Personajes:\n{json.dumps(personajes, ensure_ascii=False)}\n\n"
        )
    prompt = "\n".join(escenas_prompts)
    return generar_contenido_cache(prompt, max_tokens=3000)

def evaluar_coherencia_escena(escena_texto, personajes):
    prompt_evaluacion = (
        f"Evalúa la coherencia de la siguiente escena asegurándote de que los nombres de personajes, eventos y decisiones sean consistentes. "
        f"Si hay incoherencias, sugiere correcciones:\n\n{escena_texto}\n\n"
        f"Personajes:\n{json.dumps(personajes, ensure_ascii=False)}"
    )
    return generar_contenido_cache(prompt_evaluacion, max_tokens=500)

def ajustar_prompt_por_genero(prompt, genero):
    if genero == "Ciencia Ficción":
        prompt += "\nAsegúrate de incluir descripciones tecnológicas y un enfoque futurista."
    elif genero == "Romance":
        prompt += "\nEnfócate en las emociones y las relaciones de los personajes principales."
    elif genero == "Fantasía Oscura":
        prompt += "\nUsa un tono oscuro y enfócate en los conflictos internos y dilemas éticos."
    return prompt

# =====================
# Interfaz de Usuario
# =====================

st.set_page_config(page_title="Generador de Novelas", layout="wide")

# Barra lateral
st.sidebar.title("Opciones de Generación de la Novela")
genero = st.sidebar.selectbox("Selecciona el género de la novela", ["Thriller", "Ciencia Ficción", "Romance", "Fantasía Oscura"])
num_capitulos = st.sidebar.slider("Número de Capítulos", min_value=5, max_value=20, value=12)
num_escenas = st.sidebar.slider("Número de Escenas por Capítulo", min_value=3, max_value=10, value=5)

st.title("Generador de Novelas")

# Solicitar el tema de la novela
tema = st.text_input("Introduce el tema de la novela:")

if st.button("Enviar"):
    if tema:
        st.session_state.tema = tema
        st.session_state.personajes = []
        st.session_state.eventos = []
        st.session_state.resumen_capitulos = []
        st.session_state.novela_generada = False

        # Generar y cachear contenido inicial
        prompt_intro = f"Crea un esquema para una novela de {genero.lower()} basada en el tema: '{tema}'..."
        contenido_inicial = generar_contenido_cache(prompt_intro)
        st.write(contenido_inicial)
    else:
        st.error("El tema no puede estar vacío.")

# Paso para exportar la novela en DOCX
if 'novela_generada' in st.session_state and st.session_state.novela_generada:
    buffer_docx = exportar_a_docx(st.session_state.contenido_final)
    if buffer_docx:
        st.download_button(
            label="Descargar Novela en DOCX",
            data=buffer_docx,
            file_name="novela.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ) 
