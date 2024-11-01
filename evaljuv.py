import streamlit as st
from docx import Document
import requests
import io
import re

# Configuración de la página
st.set_page_config(page_title="Evaluación Crítica de Novelas", layout="wide")

# Título de la aplicación
st.title("Evaluación Crítica de tu Novela")

# Función para leer el contenido de un archivo .docx
def read_docx(file):
    try:
        doc = Document(file)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)
    except Exception as e:
        st.error(f"Error al leer el archivo .docx: {e}")
        return None

# Función para llamar a la API de OpenRouter con manejo de errores mejorado
def call_openrouter_api(messages, model="openai/gpt-4o-mini"):
    api_url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}"
    }
    data = {
        "model": model,
        "messages": messages,
        "max_tokens": 4000  # Aumentamos el límite de tokens
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.Timeout:
        st.error("La solicitud a la API excedió el tiempo de espera. Por favor, intenta de nuevo.")
    except requests.exceptions.HTTPError as http_err:
        st.error(f"Error HTTP: {http_err}")
        if response.status_code == 429:
            st.warning("Se ha alcanzado el límite de la API. Por favor, espera unos minutos.")
    except Exception as e:
        st.error(f"Error: {str(e)}")
    return None

# Función para dividir el texto en capítulos con mejor manejo de patrones
def split_into_chapters(text):
    # Patrón más flexible para detectar capítulos
    patterns = [
        r'(?i)capítulo\s+(?:\d+|[IVXLC]+)',
        r'(?i)chapter\s+(?:\d+|[IVXLC]+)',
        r'(?i)parte\s+(?:\d+|[IVXLC]+)'
    ]
    
    # Combinar patrones
    combined_pattern = '|'.join(f'({p})' for p in patterns)
    
    # Dividir el texto
    chapters = []
    current_text = ''
    lines = text.split('\n')
    
    for line in lines:
        if any(re.match(pattern, line.strip(), re.IGNORECASE) for pattern in patterns):
            if current_text:
                chapters.append(current_text.strip())
            current_text = line
        else:
            current_text += '\n' + line
    
    if current_text:
        chapters.append(current_text.strip())
    
    return chapters if chapters else [text]

# Función para regenerar un capítulo con manejo de contexto
def regenerate_chapter(chapter, analysis, chapter_num, total_chapters):
    prompt = f"""Por favor, reescribe el siguiente capítulo ({chapter_num} de {total_chapters}) 
    teniendo en cuenta este análisis crítico: {analysis}
    
    Mantén la esencia y los eventos principales del capítulo, pero mejora:
    1. La claridad y concisión de la narración
    2. Las descripciones excesivamente largas
    3. Las inconsistencias señaladas
    4. Los clichés identificados
    
    Capítulo original:
    {chapter}
    """
    
    messages = [{"role": "user", "content": prompt}]
    return call_openrouter_api(messages)

# Función para crear un archivo .docx
def create_docx(text):
    try:
        doc = Document()
        for line in text.split('\n'):
            if line.strip():  # Solo agregar líneas no vacías
                doc.add_paragraph(line)
        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        return buf
    except Exception as e:
        st.error(f"Error al crear el archivo .docx: {e}")
        return None

# Interfaz principal
uploaded_file = st.file_uploader("Sube tu novela en formato .docx", type=["docx"])

if uploaded_file is not None:
    with st.spinner("Leyendo el archivo..."):
        novel_text = read_docx(uploaded_file)
    
    if novel_text:
        st.success("Archivo cargado exitosamente.")
        
        # Vista previa del contenido
        with st.expander("Ver contenido de la novela"):
            preview_length = 1000
            preview_text = novel_text[:preview_length] + '...' if len(novel_text) > preview_length else novel_text
            st.text_area("Vista previa:", value=preview_text, height=200)
        
        # Botón para iniciar el análisis
        if st.button("Iniciar Evaluación Crítica"):
            with st.spinner("Realizando evaluación crítica..."):
                analysis_prompt = """Realiza una evaluación crítica literaria detallada de la siguiente novela. 
                Analiza específicamente:
                1. Estructura narrativa y ritmo
                2. Desarrollo de personajes
                3. Consistencia en la trama
                4. Uso del lenguaje y estilo
                5. Descripciones y diálogos
                
                Proporciona ejemplos específicos de áreas que necesitan mejora.
                
                Novela:
                """
                
                messages = [{"role": "user", "content": analysis_prompt + novel_text}]
                analysis = call_openrouter_api(messages)
            
            if analysis:
                st.subheader("Análisis Crítico")
                st.write(analysis)
                
                # Opción para regenerar
                if st.button("Regenerar Novela"):
                    chapters = split_into_chapters(novel_text)
                    total_chapters = len(chapters)
                    
                    st.write(f"Procesando {total_chapters} capítulos...")
                    
                    # Contenedor para la barra de progreso
                    progress_container = st.empty()
                    progress_bar = progress_container.progress(0)
                    
                    regenerated_novel = []
                    
                    for idx, chapter in enumerate(chapters, 1):
                        progress_text = st.empty()
                        progress_text.text(f"Regenerando capítulo {idx}/{total_chapters}")
                        
                        regenerated_chapter = regenerate_chapter(
                            chapter, analysis, idx, total_chapters
                        )
                        
                        if regenerated_chapter:
                            regenerated_novel.append(regenerated_chapter)
                            progress_bar.progress(idx/total_chapters)
                        else:
                            st.error(f"Error al regenerar el capítulo {idx}")
                            break
                    
                    if len(regenerated_novel) == total_chapters:
                        final_text = "\n\n".join(regenerated_novel)
                        regenerated_docx = create_docx(final_text)
                        
                        if regenerated_docx:
                            st.success("¡Regeneración completada!")
                            st.download_button(
                                "Descargar Novela Regenerada",
                                regenerated_docx,
                                "novela_regenerada.docx",
                                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            )
                            
                            with st.expander("Ver vista previa de la novela regenerada"):
                                preview = final_text[:2000] + "..." if len(final_text) > 2000 else final_text
                                st.text_area("Vista previa:", value=preview, height=300)
