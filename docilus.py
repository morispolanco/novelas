import streamlit as st
from docx import Document
import requests
import json
import base64
from PIL import Image
from io import BytesIO
from typing import List, Optional
from datetime import datetime

# Función para extraer texto de un documento Word
def extract_chapters(docx_file) -> List[str]:
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

# Función para generar un prompt adecuado para niños de 10 años
def generate_prompt(chapter: str) -> str:
    # Aquí podrías implementar una función de resumen más avanzada si es necesario.
    paragraphs = chapter.strip().split('\n')
    if paragraphs:
        summary = paragraphs[0]
    else:
        summary = chapter
    prompt = f"Ilustración para niños de 10 años que represente: {summary}"
    return prompt

# Función para generar una imagen usando la API de Together
def generate_image(prompt: str, api_key: str) -> Optional[Image.Image]:
    url = "https://api.together.xyz/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Preparar el prompt detallado
    full_prompt = f"Dibujo a lápiz en blanco y negro adecuado para niños de 10 años de edad: {prompt}"
    
    # Obtener la fecha y hora actual en formato ISO para 'update_at'
    update_at = datetime.utcnow().isoformat() + "Z"
    
    payload = {
        "model": "black-forest-labs/FLUX.1-pro",
        "prompt": full_prompt,
        "width": 512,      # Ancho de la imagen en píxeles
        "height": 512,     # Alto de la imagen en píxeles
        "steps": 28,       # Número de pasos para la generación
        "n": 1,            # Número de imágenes a generar
        "response_format": "b64_json",
        "update_at": update_at
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        st.error(f"Error al generar la imagen: {e}")
        return None
    
    data = response.json()
    image_data = data.get("data", [])[0].get("b64_json", "")
    
    if not image_data:
        st.error("No se recibió imagen en la respuesta.")
        return None
    
    try:
        # Decodificar la imagen de base64
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        
        # Verificar dimensiones de la imagen
        if image.size != (512, 512):
            st.warning(f"La imagen generada tiene un tamaño de {image.size}, redimensionando a 512x512.")
            image = image.resize((512, 512))
        
        return image
    except Exception as e:
        st.error(f"Error al procesar la imagen: {e}")
        return None

# Interfaz de Streamlit
def main():
    st.set_page_config(page_title="Generador de Ilustraciones para Fábulas")
    st.title("Generador de Ilustraciones para Fábulas")
    
    uploaded_file = st.file_uploader("Selecciona un archivo Word", type=["docx"])
    
    # Verificar si la clave API está disponible
    if "TOGETHER_API_KEY" not in st.secrets:
        st.error("Falta la clave API de Together. Por favor, agrega `TOGETHER_API_KEY` en los secretos de Streamlit.")
        st.stop()
    
    together_api_key = st.secrets["TOGETHER_API_KEY"]
    
    if uploaded_file:
        if st.button("Generar Ilustraciones"):
            with st.spinner("Extrayendo capítulos del documento..."):
                chapters = extract_chapters(uploaded_file)
            
            st.success(f"Se han extraído {len(chapters)} capítulo(s).")
            
            for idx, chapter in enumerate(chapters, 1):
                st.markdown(f"## Capítulo {idx}")
                st.write(chapter)
                
                prompt = generate_prompt(chapter)
                
                st.markdown(f"### Ilustración del Capítulo {idx}:")
                with st.spinner(f"Generando imagen para el Capítulo {idx}..."):
                    image = generate_image(prompt, together_api_key)
                
                if image:
                    st.image(image, caption=f"Ilustración del Capítulo {idx}", use_column_width=True)
                else:
                    st.error(f"No se pudo generar la imagen para el Capítulo {idx}.")

if __name__ == "__main__":
    main()
