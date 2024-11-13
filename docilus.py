import streamlit as st
import requests
from docx import Document
from docx.shared import Inches
from PIL import Image
import io
import base64
import time

# Configurar la página
st.set_page_config(
    page_title="Generador de Ilustraciones para Fábulas",
    layout="wide"
)

# Título de la aplicación
st.title("Generador de Ilustraciones para Fábulas")

# Subir archivo Word
uploaded_file = st.file_uploader("Sube un archivo Word (.docx)", type=["docx"])

if uploaded_file is not None:
    if st.button("Procesar Documento"):
        with st.spinner("Procesando..."):
            try:
                # Leer el documento subido
                doc = Document(uploaded_file)
                new_doc = Document()
                capitulos = []
                capitulo_actual = {"titulo": "", "contenido": ""}

                for para in doc.paragraphs:
                    if para.style.name.startswith('Heading'):
                        if capitulo_actual["titulo"]:
                            capitulos.append(capitulo_actual)
                        capitulo_actual = {"titulo": para.text, "contenido": ""}
                    else:
                        capitulo_actual["contenido"] += para.text + "\n"
                if capitulo_actual["titulo"]:
                    capitulos.append(capitulo_actual)

                total = len(capitulos)
                progreso = st.progress(0)

                for idx, capitulo in enumerate(capitulos, 1):
                    titulo = capitulo["titulo"]
                    contenido = capitulo["contenido"].strip()

                    # Generar momento clave usando OpenRouter API
                    openrouter_response = requests.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {st.secrets['api']['OPENROUTER_API_KEY']}"
                        },
                        json={
                            "model": "openai/gpt-4o-mini",
                            "messages": [
                                {
                                    "role": "user",
                                    "content": f"Extrae un momento clave del siguiente capítulo:\n\n{contenido}"
                                }
                            ]
                        }
                    )

                    if openrouter_response.status_code == 200:
                        momento = openrouter_response.json()['choices'][0]['message']['content'].strip()
                    else:
                        momento = "No se pudo extraer el momento clave."

                    # Generar ilustración usando Together API
                    together_response = requests.post(
                        "https://api.together.xyz/v1/images/generations",
                        headers={
                            "Authorization": f"Bearer {st.secrets['api']['TOGETHER_API_KEY']}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "black-forest-labs/FLUX.1.1-pro",
                            "prompt": f"Dibujo a lápiz en blanco y negro basado en el siguiente momento clave: {momento}",
                            "width": 512,
                            "height": 512,
                            "steps": 1,
                            "n": 1,
                            "response_format": "b64_json"
                        }
                    )

                    if together_response.status_code == 200:
                        imagen_b64 = together_response.json()['data'][0]['b64_json']
                        imagen_bytes = base64.b64decode(imagen_b64)
                        imagen = Image.open(io.BytesIO(imagen_bytes))
                        img_buffer = io.BytesIO()
                        imagen.save(img_buffer, format='PNG')
                        img_buffer.seek(0)
                    else:
                        img_buffer = None

                    # Añadir capítulo al nuevo documento
                    new_doc.add_heading(titulo, level=1)
                    if img_buffer:
                        new_doc.add_picture(img_buffer, width=Inches(6))
                    new_doc.add_paragraph(contenido)

                    # Actualizar la barra de progreso
                    progreso.progress(idx / total)
                    time.sleep(0.5)  # Opcional: simular tiempo de procesamiento

                # Guardar el nuevo documento en un buffer
                buffer = io.BytesIO()
                new_doc.save(buffer)
                buffer.seek(0)

                # Mostrar botón para descargar el nuevo documento
                st.success("Documento generado exitosamente.")
                st.download_button(
                    label="Descargar Documento",
                    data=buffer,
                    file_name="Fábulas_Illustradas.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

            except Exception as e:
                st.error(f"Ocurrió un error: {e}")
