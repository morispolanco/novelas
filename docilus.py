import streamlit as st
from docx import Document
import requests
import json
import base64
from PIL import Image
from io import BytesIO
from typing import List

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

# Función para obtener momentos clave de una fábula
def get_key_moments(fable: str, api_key: str) -> List[str]:
    url = "https://api.together.xyz/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    messages = [
        {
            "role": "system",
            "content": "Extrae los momentos clave de la siguiente fábula. Devuelve una lista enumerada de momentos importantes."
        },
        {
            "role": "user",
            "content": fable
        }
    ]
    
    payload = {
        "model": "Qwen/Qwen2.5-7B-Instruct-Turbo",
        "messages": messages,
        "max_tokens": 1500,
        "temperature": 0.7,
        "top_p": 0.7,
        "top_k": 50,
        "repetition_penalty": 1,
        "stop": ["<|eot_id|>"],
        "stream": False
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code != 200:
        st.error(f"Error al extraer momentos clave: {response.text}")
        return []
    
    data = response.json()
    key_moments_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    # Procesar el texto para obtener una lista de momentos
    key_moments = []
    for line in key_moments_text.split('\n'):
        line = line.strip()
        if line and (line[0].isdigit() and line[1] == '.'):
            moment = line.split('.', 1)[1].strip()
            key_moments.append(moment)
    
    return key_moments

# Función para generar una imagen usando la API de Together
def generate_image(prompt: str, api_key: str) -> Image.Image:
    url = "https://api.together.xyz/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Añadir detalles al prompt para asegurar el estilo deseado
    full_prompt = f"Dibujo a lápiz en blanco y negro de: {prompt}"
    
    payload = {
        "model": "black-forest-labs/FLUX.1.1-pro",
        "prompt": full_prompt,
        "width": 512,
        "height": 512,
        "steps": 50,  # Aumentar pasos para mejor calidad
        "n": 1,
        "response_format": "b64_json"
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code != 200:
        st.error(f"Error al generar la imagen: {response.text}")
        return None
    
    data = response.json()
    image_data = data.get("data", [])[0].get("b64_json", "")
    
    if not image_data:
        st.error("No se recibió imagen en la respuesta.")
        return None
    
    # Decodificar la imagen de base64
    image_bytes = base64.b64decode(image_data)
    image = Image.open(BytesIO(image_bytes))
    
    return image

# Interfaz de Streamlit
st.title("Generador de Ilustraciones a Lápiz para Fábulas")
uploaded_file = st.file_uploader("Selecciona un archivo Word", type=["docx"])

# Verificar si la clave API está disponible
if "TOGETHER_API_KEY" not in st.secrets:
    st.error("Falta la clave API de Together. Por favor, agrega `TOGETHER_API_KEY` en los secretos de Streamlit.")
else:
    together_api_key = st.secrets["TOGETHER_API_KEY"]
    
    if uploaded_file:
        if st.button("Enviar"):
            chapters = extract_chapters(uploaded_file)
            st.success(f"Se han extraído {len(chapters)} capítulos.")
            
            for chapter in chapters:
                st.markdown("### Capítulo")
                st.write(chapter)
                
                key_moments = get_key_moments(chapter, together_api_key)
                
                if key_moments:
                    st.success(f"Se han extraído {len(key_moments)} momentos clave.")
                    
                    st.markdown("### Ilustraciones Generadas")
                    
                    for idx, moment in enumerate(key_moments, 1):
                        st.markdown(f"**Momento {idx}:** {moment}")
                        with st.spinner(f"Generando imagen para el momento {idx}..."):
                            image = generate_image(moment, together_api_key)
                        
                        if image:
                            st.image(image, use_column_width=True)
                else:
                    st.error("No se pudieron extraer momentos clave de la fábula.")
