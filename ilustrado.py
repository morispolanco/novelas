import streamlit as st
import requests
import base64
from PIL import Image
from io import BytesIO
import re
import os
import zipfile

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

# Función para generar un resumen de un párrafo usando OpenRouter
def generar_resumen(capitulo):
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
                "content": f"Genera un resumen de un párrafo para el siguiente capítulo de una novela, asegurando coherencia en los personajes y el ambiente:\n\n{capitulo}"
            }
        ]
    }
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    if response.status_code == 200:
        resumen = response.json()['choices'][0]['message']['content'].strip()
        return resumen
    else:
        st.error(f"Error al generar el resumen: {response.status_code} - {response.text}")
        return None

# Función para generar una ilustración usando Together API
def generar_ilustracion(prompt, width=512, height=512):
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

# Función para crear un archivo ZIP con resúmenes e ilustraciones
def crear_zip(capitulos, resúmenes, ilustraciones):
    # Crear un objeto BytesIO para el ZIP
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for idx, cap in enumerate(capitulos, 1):
            # Nombre de los archivos
            resumen_nombre = f"Capitulo_{idx}_Resumen.txt"
            # Guardar cada ilustración con un nombre único
            ilustracion_nombre_1 = f"Capitulo_{idx}_Ilustracion_1.png"
            ilustracion_nombre_2 = f"Capitulo_{idx}_Ilustracion_2.png"
            
            # Agregar resumen al ZIP
            zip_file.writestr(resumen_nombre, resúmenes[idx-1])
            
            # Agregar ilustraciones al ZIP
            if ilustraciones[idx-1][0]:
                img_byte_arr_1 = BytesIO()
                ilustraciones[idx-1][0].save(img_byte_arr_1, format='PNG')
                img_byte_arr_1.seek(0)
                zip_file.writestr(ilustracion_nombre_1, img_byte_arr_1.read())
            
            if ilustraciones[idx-1][1]:
                img_byte_arr_2 = BytesIO()
                ilustraciones[idx-1][1].save(img_byte_arr_2, format='PNG')
                img_byte_arr_2.seek(0)
                zip_file.writestr(ilustracion_nombre_2, img_byte_arr_2.read())
    
    zip_buffer.seek(0)
    return zip_buffer

# Título de la aplicación
st.title("Convertidor de Novela en Historia Ilustrada")

# Instrucciones
st.markdown("""
Sube tu novela en formato `.txt`, `.docx` o `.pdf`, y la aplicación generará un resumen de un párrafo para cada capítulo y dos ilustraciones coherentes en estilo 'Arte Digital'. Al final, podrás descargar un archivo ZIP que contiene todos los resúmenes e ilustraciones generados.
""")

# Subida de archivo
uploaded_file = st.file_uploader("Sube tu novela", type=["txt", "pdf", "docx"])

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
                    
                    # Generar resumen
                    with st.spinner(f"Generando resumen para el capítulo {idx}..."):
                        resumen = generar_resumen(cap['contenido'])
                        if resumen:
                            resúmenes.append(resumen)
                            st.write("**Resumen de un párrafo:**")
                            st.write(resumen)
                    
                    # Generar dos ilustraciones
                    ilustraciones_capitulo = []
                    for i in range(2):
                        with st.spinner(f"Generando ilustración {i+1} para el capítulo {idx}..."):
                            prompt = f"{resumen}. Estilo artístico: Arte Digital."
                            imagen = generar_ilustracion(prompt)
                            if imagen:
                                ilustraciones_capitulo.append(imagen)
                                st.image(imagen, caption=f"Ilustración {i+1} Capítulo {idx} - Arte Digital", use_column_width=True)
                    
                    ilustraciones.append(ilustraciones_capitulo)
                    st.markdown("---")
                
                st.success("Procesamiento completado.")
                
                # Crear el archivo ZIP
                with st.spinner("Creando archivo ZIP con resúmenes e ilustraciones..."):
                    zip_file = crear_zip(capitulos, resúmenes, ilustraciones)
                
                # Proporcionar botón para descargar
                st.download_button(
                    label="Descargar Resúmenes e Ilustraciones en ZIP",
                    data=zip_file,
                    file_name='resumenes_ilustraciones.zip',
                    mime='application/zip'
                )
    else:
        st.error("Por favor, sube un archivo para comenzar.")
