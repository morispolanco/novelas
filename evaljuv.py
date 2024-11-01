import streamlit as st
from docx import Document
from docx.shared import Pt
import requests
import os
import io

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
def call_openrouter_api(messages, model="openai/gpt-4"):
    api_url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}"
    }
    data = {
        "model": model,
        "messages": messages,
        "stream": False,
        "temperature": 0.7,
        "max_tokens": 2048
    }
    response = requests.post(api_url, headers=headers, json=data)
    if response.status_code == 200:
        try:
            return response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            st.error("Error al procesar la respuesta de la API.")
            return None
    else:
        st.error(f"Error en la API: {response.status_code} - {response.text}")
        return None

# Función para dividir la novela en capítulos
def split_into_chapters(text):
    import re
    # Busca patrones comunes para capítulos
    chapters = re.split(r'(Capítulo\s+\d+|CAPÍTULO\s+\d+|Capítulo\s+[IVXLCDM]+|CAPÍTULO\s+[IVXLCDM]+)', text)
    if len(chapters) > 1:
        # Reconstruir los capítulos incluyendo el título
        it = iter(chapters)
        chapters = [a + b for a, b in zip(it, it)]
    else:
        # Si no se encuentran patrones, dividir cada cierto número de palabras
        words = text.split()
        n = 1000  # Número de palabras por segmento
        chapters = [' '.join(words[i:i + n]) for i in range(0, len(words), n)]
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
                    "Por favor, realiza una evaluación crítica literaria de la siguiente novela en busca de errores, "
                    "inconsistencias, descripciones muy largas, repeticiones, clichés, etc. Proporciona un análisis detallado."
                    "\n\nTexto de la novela:\n" + novel_text)
                }
            ]
            analysis = call_openrouter_api(messages)
        
        if analysis:
            st.subheader("Análisis Crítico")
            st.write(analysis)
            
            # Preguntar si desea regenerar la novela
            regenerate = st.radio("¿Quieres regenerar la novela basada en este análisis?", ("No", "Sí"))
            
            if regenerate == "Sí":
                with st.spinner("Dividiendo la novela en capítulos..."):
                    chapters = split_into_chapters(novel_text)
                
                regenerated_novel = ""
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                total_chapters = len(chapters)
                
                for idx, chapter in enumerate(chapters, start=1):
                    status_text.text(f"Regenerando Capítulo {idx} de {total_chapters}...")
                    
                    # Limitar el tamaño del mensaje para evitar exceder el límite de tokens
                    prompt = (
                        "Basado en el siguiente análisis, regenera este capítulo mejorando los aspectos mencionados. "
                        "Conserva el estilo original y la intención del autor.\n\n"
                        "Análisis:\n" + analysis + "\n\nCapítulo a regenerar:\n" + chapter
                    )
                    
                    messages = [{"role": "user", "content": prompt}]
                    
                    regenerated_chapter = call_openrouter_api(messages)
                    
                    if regenerated_chapter:
                        regenerated_novel += f"{regenerated_chapter}\n\n"
                    else:
                        regenerated_novel += f"[Error al regenerar el Capítulo {idx}]\n\n"
                    
                    # Actualizar la barra de progreso
                    progress_bar.progress(idx / total_chapters)
                
                status_text.text("Regeneración completada.")
                st.success("La novela ha sido regenerada exitosamente.")
                
                # Crear un documento Word con la novela regenerada
                doc = Document()
                for para in regenerated_novel.split('\n\n'):
                    p = doc.add_paragraph(para)
                    p.style.font.size = Pt(12)
                
                # Guardar el documento en memoria
                buffer = io.BytesIO()
                doc.save(buffer)
                buffer.seek(0)
                
                # Botón para descargar el documento Word
                st.download_button(
                    label="Descargar Novela Regenerada",
                    data=buffer,
                    file_name="novela_regenerada.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
