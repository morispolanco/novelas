import streamlit as st
from docx import Document
import requests

# Configuración básica
st.set_page_config(page_title="Análisis de Novelas", layout="wide")
st.title("Análisis Crítico de tu Novela")

def read_docx(file):
    doc = Document(file)
    return "\n".join([paragraph.text for paragraph in doc.paragraphs])

def analyze_novel(text):
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}",
            "Content-Type": "application/json"
        }
        
        analysis_prompt = """Realiza un análisis crítico detallado de esta novela, evaluando:

        1. ESTRUCTURA Y RITMO
        - Coherencia de la estructura narrativa
        - Ritmo y pacing de la historia
        - Balance entre descripción, narración y diálogo
        
        2. PERSONAJES
        - Profundidad y desarrollo
        - Coherencia en sus acciones y motivaciones
        - Arcos de desarrollo
        
        3. TRAMA
        - Consistencia y lógica interna
        - Resolución de conflictos
        - Manejo de subtramas
        
        4. ESTILO Y TÉCNICA
        - Calidad de la prosa
        - Uso del lenguaje
        - Técnicas narrativas empleadas
        
        5. PUNTOS A MEJORAR
        - Identificar áreas específicas que necesitan revisión
        - Sugerir mejoras concretas
        - Señalar posibles inconsistencias
        
        Proporciona ejemplos específicos del texto para ilustrar cada punto."""
        
        data = {
            "model": "openai/gpt-4o-mini",
            "messages": [{"role": "user", "content": f"{analysis_prompt}\n\nNOVELA:\n\n{text}"}],
            "max_tokens": 4000
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=120)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    
    except requests.exceptions.Timeout:
        st.error("⏱️ La solicitud excedió el tiempo límite. Intenta con una sección más corta del texto.")
    except requests.exceptions.HTTPError as http_err:
        st.error(f"❌ Error en la API: {http_err}")
    except Exception as e:
        st.error(f"❌ Error inesperado: {str(e)}")
    return None

# Función para calificar cada aspecto
def rate_aspects():
    structure_rating = st.slider("Calificación para Estructura y Ritmo:", min_value=1, max_value=10, value=5)
    characters_rating = st.slider("Calificación para Personajes:", min_value=1, max_value=10, value=5)
    plot_rating = st.slider("Calificación para Trama:", min_value=1, max_value=10, value=5)
    style_rating = st.slider("Calificación para Estilo y Técnica:", min_value=1, max_value=10, value=5)
    
    # Calcular el promedio
    average_rating = (structure_rating + characters_rating + plot_rating + style_rating) / 4
    return structure_rating, characters_rating, plot_rating, style_rating, average_rating

# Interfaz principal
st.write("""
### 📚 Instrucciones
1. Sube tu novela en formato .docx
2. Haz clic en 'Analizar' para recibir un análisis crítico detallado
3. El análisis evaluará estructura, personajes, trama y estilo
""")

uploaded_file = st.file_uploader("Sube tu novela (formato .docx)", type="docx")

if uploaded_file:
    try:
        # Leer el archivo
        novel_text = read_docx(uploaded_file)
        st.success("✅ Archivo cargado correctamente")
        
        # Mostrar vista previa
        with st.expander("📄 Ver contenido del archivo"):
            st.text_area(
                "Primeras 1000 palabras del texto:",
                novel_text[:1000] + "...",
                height=200
            )
        
        # Botón de análisis
        if st.button("🔍 Analizar Novela"):
            with st.spinner("Analizando el texto... (esto puede tomar unos minutos)"):
                analysis = analyze_novel(novel_text)
                
                if analysis:
                    st.write("## 📝 Análisis Crítico")
                    
                    # Crear tabs para organizar el análisis
                    tab1, tab2 = st.tabs(["📊 Análisis Completo", "📋 Resumen"])
                    
                    with tab1:
                        st.markdown(analysis)
                    
                    with tab2:
                        st.write("""
                        ### Principales aspectos analizados:
                        - ⚡ Estructura y ritmo narrativo
                        - 👥 Desarrollo de personajes
                        - 📈 Coherencia de la trama
                        - ✍️ Estilo y técnica literaria
                        - 🎯 Puntos específicos a mejorar
                        """)
                    
                    # Calificar cada aspecto
                    st.write("### Califica cada aspecto de la novela")
                    structure_rating, characters_rating, plot_rating, style_rating, average_rating = rate_aspects()
                    
                    # Mostrar resultados
                    st.write("### Resultados de Calificación:")
                    st.write(f"⭐ **Calificación para Estructura y Ritmo:** {structure_rating}")
                    st.write(f"⭐ **Calificación para Personajes:** {characters_rating}")
                    st.write(f"⭐ **Calificación para Trama:** {plot_rating}")
                    st.write(f"⭐ **Calificación para Estilo y Técnica:** {style_rating}")
                    st.write(f"⭐ **Calificación global asignada:** {average_rating:.2f}")

    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")
