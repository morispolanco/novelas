import streamlit as st
import requests
import json
from docx import Document
import io
import random

# Configuración de la página
st.set_page_config(page_title="Children's Story Generator", page_icon="📚")

# Obtener la API key de los secretos de Streamlit
api_key = st.secrets["OPENROUTER_API_KEY"]

# Temas posibles para los cuentos
story_themes = [
    "magical forest", "space adventure", "friendly dragon", 
    "underwater kingdom", "talking animals", "fairy garden",
    "time travel", "magical school", "circus adventure",
    "lost treasure", "flying carpet", "enchanted toy",
    "rainbow unicorn", "giant's castle", "magical library"
]

def generate_story(age, theme):
    """Genera un cuento basado en la edad y el tema"""
    
    # Ajustar la longitud según la edad
    if age < 6:
        length = "very short (about 100 words)"
    elif age < 9:
        length = "short (about 200 words)"
    else:
        length = "medium length (about 300 words)"
    
    prompt = f"""Write a {length} children's story in English for a {age}-year-old child. 
    Theme: {theme}
    Make it engaging, age-appropriate, and include a moral lesson.
    Use simple language for younger children and more complex vocabulary for older ones."""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    data = {
        "model": "openai/gpt-4-mini",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=data
    )

    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        return f"Error generating story: {response.status_code}"

def create_word_document(stories):
    """Crea un documento Word con los cuentos generados"""
    doc = Document()
    doc.add_heading('Children\'s Stories Collection', 0)

    for i, (age, theme, story) in enumerate(stories, 1):
        doc.add_heading(f'Story {i}: {theme.title()}', level=1)
        doc.add_paragraph(f'For age: {age} years')
        doc.add_paragraph(story)
        doc.add_paragraph('\n')

    return doc

# Interfaz de usuario
st.title("📚 Children's Story Generator")

# Input para el número de cuentos
num_stories = st.number_input(
    "How many stories would you like to generate? (max 15)",
    min_value=1,
    max_value=15,
    value=1
)

# Input para la edad
age = st.slider("Select child's age", 4, 12, 8)

if st.button("Generate Stories"):
    with st.spinner("Generating your stories... Please wait"):
        stories = []
        # Seleccionar temas aleatorios sin repetición
        selected_themes = random.sample(story_themes, num_stories)
        
        for theme in selected_themes:
            story = generate_story(age, theme)
            stories.append((age, theme, story))
            
            # Mostrar cada cuento en la interfaz
            st.subheader(f"Story: {theme.title()}")
            st.write(story)
            st.markdown("---")

        # Crear documento Word
        doc = create_word_document(stories)
        
        # Guardar el documento en memoria
        bio = io.BytesIO()
        doc.save(bio)
        
        # Botón de descarga
        st.download_button(
            label="Download Stories as Word Document",
            data=bio.getvalue(),
            file_name="children_stories.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

st.markdown("""
---
### About this app
This app generates age-appropriate children's stories using AI. 
Each story is uniquely crafted considering the child's age and includes:
- Age-appropriate vocabulary
- Engaging storylines
- Positive messages
- Educational value
""")
