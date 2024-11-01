import streamlit as st
from docx import Document
import requests
import io

# Configuración básica
st.set_page_config(page_title="Evaluación de Novelas", layout="wide")
st.title("Evaluación y Regeneración de Novela")

def read_docx(file):
    doc = Document(file)
    return "\n".join([paragraph.text for paragraph in doc.paragraphs])

def create_docx(text):
    doc = Document()
    for line in text.split('\n'):
        if line.strip():
            doc.add_paragraph(line)
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def call_api(text, is_analysis=True):
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}",
            "Content-Type": "application/json"
        }
        
        if is_analysis:
            prompt = "Analiza esta novela y proporciona una crítica constructiva detallada:"
        else:
            prompt = """Reescribe esta novela mejorando su calidad literaria. 
            Mantén la misma historia pero mejora:
            1. La narrativa y el ritmo
            2. Las descripciones
            3. Los diálogos
            4. El desarrollo de personajes
            
            Devuelve la novela completa reescrita:"""
        
        data = {
            "model": "openai/gpt-4-turbo",
            "messages": [{"role": "user", "content": f"{prompt}\n\n{text}"}],
            "max_tokens": 4000
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=120)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    
    except Exception as e:
        st.error(f"Error en la API: {str(e)}")
        return None

# Interfaz principal
uploaded_file = st.file_uploader("Sube tu novela (formato .docx)", type="docx")

if uploaded_file:
    try:
        # Leer el archivo
        novel_text = read_docx(uploaded_file)
        st.success("✅ Archivo cargado correctamente")
        
        # Mostrar vista previa
        with st.expander("Ver contenido original"):
            st.text_area("Texto original:", novel_text[:1000] + "...", height=200)
        
        # Columnas para análisis y regeneración
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📝 Analizar Novela"):
                with st.spinner("Analizando..."):
                    analysis = call_api(novel_text, is_analysis=True)
                    if analysis:
                        st.write("### Análisis")
                        st.write(analysis)
        
        with col2:
            if st.button("🔄 Regenerar Novela"):
                with st.spinner("Regenerando... (esto puede tomar varios minutos)"):
                    regenerated = call_api(novel_text, is_analysis=False)
                    if regenerated:
                        st.success("✨ ¡Regeneración completada!")
                        
                        # Crear documento regenerado
                        doc_buffer = create_docx(regenerated)
                        
                        # Botón de descarga
                        st.download_button(
                            "⬇️ Descargar Novela Regenerada",
                            doc_buffer,
                            "novela_regenerada.docx",
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                        
                        # Mostrar vista previa
                        with st.expander("Ver novela regenerada"):
                            st.text_area("Texto regenerado:", regenerated[:1000] + "...", height=200)
    
    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")
