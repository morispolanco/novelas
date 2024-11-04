# app.py

import streamlit as st
import requests
import base64
from PIL import Image
from io import BytesIO
import re
import os

# Importar bibliotecas para manejar archivos
import PyPDF2
from docx import Document

# Función para dividir la novela en capítulos
def dividir_en_capitulos(texto):
    # Suponiendo que los capítulos están marcados con "Capítulo" o "Chapter"
    capitulos = re.split(r'(Capítulo\s+\d+|Chapter\s+\d+)', texto, flags=re.IGNORECASE)
    capitulos_limpios = []
    for i in range(1, len(capitulos), 2):
        titulo = capitulos[i].strip()
        contenido = capitulos[i+1].strip() if i+1 < len(capitulos) else ""
        capitulos_limpios.append({'titulo': titulo, 'contenido': contenido})
    return capitulos_limpios

# Función para resumir un capítulo usando OpenRouter
def resumir_capitulo(capitulo):
    api_key = st.secrets["OPENROUTER_API_KEY"]
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": f"Resume el siguiente capítulo de una novela asegurando coherencia en los personajes y el ambiente:\n\n{capitulo}"
            }
        ]
    }
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    if response.status_code == 200:
        resumen = response.json()['choices'][0]['message']['content']
        return resumen
    else:
        st.error(f"Error al resumir el capítulo: {response.status_code} - {response.text}")
        return None

# Función para generar una ilustración usando Together API
def generar_ilustracion(prompt, estilo, width=512, height=512):
    api_key = st.secrets["TOGETHER_API_KEY"]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "black-forest-labs/FLUX.1-pro",
        "prompt": prompt,
        "width": width,
        "height": height,
        "steps": 28,
        "n": 1,
        "response_format": "b64_json"
    }
    try:
        response = requests.post("https://api.together.xyz/v1/images/generations", headers=headers, json=data)
        response.raise_for_status()
        response_data = response.json()
        # Decodificar la imagen de base64
        b64_image = response_data["data"][0]["b64_json"]
        image_bytes = base64.b64decode(b64_image)
        image = Image.open(BytesIO(image_bytes))
        return image
    except requests.exceptions.HTTPError as http_err:
        st.error(f"Error HTTP al generar la imagen: {http_err} - {response.text}")
    except Exception as e:
        st.error(f"Error al generar la imagen: {e}")
    return None

# Lista de estilos artísticos soportados
supported_styles = [
    "Realismo",
    "Impresionismo",
    "Expresionismo",
    "Surrealismo",
    "Arte Abstracto",
    "Arte Digital",
    "Estilo Manga",
    "Estilo de Cómic",
    "Arte Minimalista",
    "Arte Pop",
    "Cyberpunk",
    "Arte Gótico",
    "Steampunk",
    "Arte Deco",
    "Arte Futurista",
    "Arte Fantástico",
    "Arte Sci-Fi",
    "Arte Barroco",
    "Arte Moderno"
]

# Título de la aplicación
st.title("Convertidor de Novela en Historia Ilustrada")

# Instrucciones
st.markdown("""
Sube tu novela en formato `.txt`, `.docx` o `.pdf`, selecciona un estilo artístico para las ilustraciones y la aplicación resumirá cada capítulo y generará ilustraciones coherentes para cada uno.
""")

# Subida de archivo
uploaded_file = st.file_uploader("Sube tu novela", type=["txt", "pdf", "docx"])

# Selección de estilo artístico
estilo_seleccionado = st.selectbox("Selecciona un estilo artístico para las ilustraciones", supported_styles)

# Botón para procesar
if st.button("Procesar Novela"):
    if uploaded_file is not None:
        # Leer el contenido del archivo
        contenido = ""
        if uploaded_file.type == "text/plain":
            try:
                contenido = uploaded_file.read().decode("utf-8")
            except Exception as e:
                st.error(f"Error al leer el archivo de texto: {e}")
        elif uploaded_file.type == "application/pdf":
            try:
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                for page in pdf_reader.pages:
                    texto_pagina = page.extract_text()
                    if texto_pagina:
                        contenido += texto_pagina + "\n"
            except Exception as e:
                st.error(f"Error al leer el PDF: {e}")
        elif uploaded_file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
            try:
                doc = Document(uploaded_file)
                for para in doc.paragraphs:
                    contenido += para.text + "\n"
            except Exception as e:
                st.error(f"Error al leer el archivo de Word: {e}")
        else:
            st.error("Formato de archivo no soportado.")
        
        if contenido:
            st.success("Archivo leído correctamente. Procesando...")
            # Dividir en capítulos
            capitulos = dividir_en_capitulos(contenido)
            st.info(f"Se encontraron {len(capitulos)} capítulos.")
            
            if len(capitulos) == 0:
                st.error("No se encontraron capítulos en el documento. Asegúrate de que los capítulos estén marcados con 'Capítulo' o 'Chapter' seguido de un número.")
            else:
                # Crear listas para almacenar resúmenes e ilustraciones
                resúmenes = []
                ilustraciones = []
                
                for idx, cap in enumerate(capitulos, 1):
                    st.write(f"### {cap['titulo']}")
                    
                    # Resumir capítulo
                    with st.spinner(f"Resumiendo el capítulo {idx}..."):
                        resumen = resumir_capitulo(cap['contenido'])
                        if resumen:
                            resúmenes.append(resumen)
                            st.write("**Resumen:**")
                            st.write(resumen)
                    
                    # Generar ilustración
                    with st.spinner(f"Generando ilustración para el capítulo {idx}..."):
                        prompt = f"{resumen}. Estilo artístico: {estilo_seleccionado}."
                        imagen = generar_ilustracion(prompt, estilo_seleccionado)
                        if imagen:
                            ilustraciones.append(imagen)
                            st.image(imagen, caption=f"Ilustración Capítulo {idx} - {estilo_seleccionado}", use_column_width=True)
                    
                    st.markdown("---")
                
                st.success("Procesamiento completado.")
    else:
        st.error("Por favor, sube un archivo para comenzar.")
