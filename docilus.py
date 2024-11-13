import streamlit as st
from docx import Document
import requests
import base64
import os
from io import BytesIO

# Configuración de la página
st.title("Generador de Ilustraciones para Capítulos")
st.write("Sube un archivo Word y genera ilustraciones en estilo lápiz para cada capítulo.")

# Cargar las API keys desde los secretos
OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]
TOGETHER_API_KEY = st.secrets["TOGETHER_API_KEY"]

# Función para extraer texto de un documento Word
def extract_chapters(docx_file):
    doc = Document(docx_file)
    chapters = []
    current_chapter = ""
    for para in doc.paragraphs:
        if para.style.name.startswith('Heading'):
            if current_chapter:
                chapters.append(current_chapter)
            current_chapter = para.text + "\n"
        else:
            current_chapter += para.text + "\n"
    if current_chapter:
        chapters.append(current_chapter)
    return chapters

# Función para obtener el momento clave usando Open Router
def get_key_moment(chapter_text):
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENROUTER_API_KEY}"
        },
        json={
            "model": "openai/gpt-4o-mini",
            "messages": [{"role": "user", "content": chapter_text}]
        }
    )
    return response.json().get("choices", [{}])[0].get("message", {}).get("content", "")

# Función para generar la ilustración usando Together
def generate_illustration(prompt):
    # Modificar el prompt para solicitar un estilo de lápiz
    pencil_style_prompt = f"{prompt}, estilo lápiz, en blanco y negro"
    
    response = requests.post(
        "https://api.together.xyz/v1/images/generations",
        headers={
            "Authorization": f"Bearer {TOGETHER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "black-forest-labs/FLUX.1.1-pro",
            "prompt": pencil_style_prompt,
            "width": 512,
            "height": 512,
            "steps": 1,
            "n": 1,
            "response_format": "b64_json"
        }
    )
    return response.json().get("data", [{}])[0].get("b64_json", "")

# Función para crear un nuevo documento Word
def create_document(chapters_with_images):
    doc = Document()
    for chapter, image in chapters_with_images:
        doc.add_heading(chapter.split('\n')[0], level=1)
        doc.add_paragraph(chapter)
        if image:
            img_data = base64.b64decode(image)
            image_stream = BytesIO(img_data)
            doc.add_picture(image_stream)
    return doc

# Cargar archivo Word
uploaded_file = st.file_uploader("Selecciona un archivo Word", type=["docx"])

if uploaded_file:
    if st.button("Enviar"):
        chapters = extract_chapters(uploaded_file)
        chapters_with_images = []
        
        for chapter in chapters:
            key_moment = get_key_moment(chapter)
            if key_moment:
                image = generate_illustration(key_moment)
                chapters_with_images.append((chapter, image))
        
        # Crear y descargar el nuevo documento Word
        new_doc = create_document(chapters_with_images)
        docx_file_path = "documento_generado.docx"
        new_doc.save(docx_file_path)
        
        with open(docx_file_path, "rb") as f:
            st.download_button("Descargar Documento Word", f, file_name=docx_file_path, mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
