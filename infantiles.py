import streamlit as st
import requests
import json
from docx import Document
from docx.shared import Pt

# Función para generar un cuento utilizando la API de OpenRouter
def generate_story(api_key, age, topic):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": f"Write a short story for a {age}-year-old child about {topic}. Keep it simple and suitable for their age."
            }
        ]
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()
    return response.json().get("choices", [])[0].get("message", {}).get("content", "")

# Configuración de la aplicación de Streamlit
st.title("Story Generator for Kids")

# Obtener la API Key de los secretos de Streamlit
api_key = st.secrets["OPENROUTER_API_KEY"]

# Entrada del usuario
num_stories = st.number_input("Number of stories to generate (max 15)", min_value=1, max_value=15, value=1, step=1)

if st.button("Generate Stories"):
    stories = []
    
    for i in range(num_stories):
        age = st.number_input(f"Age of the child for story {i+1}", min_value=3, max_value=12, value=5, step=1)
        topic = st.text_input(f"Topic or theme for story {i+1}", value="friendship")
        
        with st.spinner(f"Generating story {i+1}..."):
            story = generate_story(api_key, age, topic)
            stories.append(story)
    
    # Crear un documento Word con los cuentos
    doc = Document()
    for idx, story in enumerate(stories):
        doc.add_heading(f"Story {idx+1}", level=1)
        story_paragraph = doc.add_paragraph(story)
        story_paragraph.style = doc.styles['Normal']
        story_paragraph.paragraph_format.space_after = Pt(12)
    
    # Guardar el documento Word
    doc_name = "kids_stories.docx"
    doc.save(doc_name)
    
    # Permitir la descarga del archivo Word
    with open(doc_name, "rb") as file:
        st.download_button(label="Download Stories", data=file, file_name=doc_name, mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

