import streamlit as st
from docx import Document
import requests
import os
import io
import re

# Configuración de la página
st.set_page_config(page_title="Evaluación Crítica de Novelas", layout="wide")

# Título de la aplicación
st.title("Evaluación Crítica de tu Novela")

# Función para leer el contenido de un archivo .docx
def read_docx(file):
    doc = Document(file)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

# Función para llamar a la API de OpenRouter
def call_openrouter_api(messages, model="gpt-4"):
    api_url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}"
    }
    data = {
        "model": model,
        "messages": messages
    }
    try:
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.HTTPError as http_err:
        st.error(f"Error en la API: {response.status_code} - {response.text}")
    except Exception as err:
        st.error(f"Ocurrió un error: {err}")
    return None

# Función para dividir el texto en capítulos
def split_into_chapters(text):
    # Utiliza expresiones regulares para encontrar capítulos (ejemplo: "Capítulo 1", "Chapter 1", etc.)
    pattern = r'(Capítulo\s+\d+|Chapter\s+\d+)', re.IGNORECASE
    splits = re.split(pattern, text)
    chapters = []
    current_chapter = ""
    for i in range(len(splits)):
        if re.match(pattern, splits[i], re.IGNORECASE):
            if current_chapter:
                chapters.append(current_chapter.strip())
            current_chapter = splits[i]
        else:
            current_chapter += " " + splits[i]
    if current_chapter:
        chapters.append(current_chapter.strip())
    return chapters

# Sección para subir el archivo .docx
uploaded_file = st.file_uploader("Sube tu novela en formato .docx", type=["docx"])

if uploaded_file is not None:
    with st.spinner("Leyendo el archivo..."):
        novel_text = read_docx(uploaded_file)
    
    st.success("Archivo cargado exitosamente.")
    
    # Mostrar un resumen breve del contenido
    st.subheader("Contenido de la Novela")
    st.text_area("Vista previa:", value=novel_text[:1000] + '...', height=200)
    
    # Botón para iniciar el análisis
    if st.button("Iniciar Evaluación Crítica"):
        with st.spinner("Realizando evaluación crítica..."):
            messages = [
                {"role": "user", "content": (
                    "Realiza una evaluación crítica literaria de la siguiente novela en busca de errores, inconsistencias, "
                    "descripciones muy largas, repeticiones, clichés, etc. Proporciona un análisis detallado."
                    "\n\n" + novel_text)
                }
            ]
            analysis = call_openrouter_api(messages)
        
        if analysis:
            st.subheader("Análisis Crítico")
            st.write(analysis)
            
            # Preguntar si desea regenerar la novela
            regenerate = st.radio("¿Quieres regenerar la novela basada en este análisis?", ("No", "Sí"))
            
            if regenerate == "Sí":
                # Dividir la novela en capítulos
                chapters = split_into_chapters(novel_text)
                
                if not chapters:
                    st.error("No se pudieron detectar capítulos en la novela. Asegúrate de que estén correctamente formateados.")
                else:
                    regenerated_novel = ""
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    total_chapters = len(chapters)
                    
                    for idx, chapter in enumerate(chapters, start=1):
                        status_text.text(f"Regenerando Capítulo {idx} de {total_chapters}...")
                        
                        # Solicitar a la API la regeneración del capítulo
                        regen_messages = [
                            {"role": "user", "content": (
                                "Basado en el siguiente análisis, regenera este capítulo mejorando los aspectos mencionados: "
                                "\n\n" + analysis + "\n\nCapítulo a regenerar:\n" + chapter)
                            }
                        ]
                        regenerated_chapter = call_openrouter_api(regen_messages)
                        
                        if regenerated_chapter:
                            regenerated_novel += f"{regenerated_chapter}\n\n"
                        else:
                            regenerated_novel += f"Capítulo {idx}\n[Error al regenerar este capítulo]\n\n"
                        
                        # Actualizar la barra de progreso
                        progress_bar.progress(idx / total_chapters)
                    
                    status_text.text("Regeneración completada.")
                    st.success("La novela ha sido regenerada exitosamente.")
                    
                    # Mostrar la novela regenerada (puede ser muy larga, así que se puede ofrecer descargarla)
                    st.subheader("Novela Regenerada")
                    
                    # Convertir el texto regenerado a un archivo .docx
                    def create_docx(text):
                        doc = Document()
                        for line in text.split('\n'):
                            doc.add_paragraph(line)
                        buf = io.BytesIO()
                        doc.save(buf)
                        buf.seek(0)
                        return buf

                    regenerated_docx = create_docx(regenerated_novel)
                    
                    st.download_button(
                        label="Descargar Novela Regenerada",
                        data=regenerated_docx,
                        file_name="novela_regenerada.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                    
                    # Opcional: Mostrar una vista previa limitada
                    st.text_area("Vista Previa de la Novela Regenerada:", value=regenerated_novel[:2000] + '...', height=300)
