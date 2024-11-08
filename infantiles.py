import streamlit as st
import requests
import json
from docx import Document
from docx.shared import Inches
import io
import random
from PIL import Image
import base64
import re
from collections import Counter

# Configuración de la página
st.set_page_config(page_title="Children's Story Generator", page_icon="📚", layout="wide")

# Obtener las API keys de los secretos de Streamlit
openrouter_api_key = st.secrets["OPENROUTER_API_KEY"]
together_api_key = st.secrets["TOGETHER_API_KEY"]

# Temas posibles para los cuentos con descripciones únicas
story_themes = [
    {"theme": "magical forest", "description": "enchanted woods with mystical creatures"},
    {"theme": "space adventure", "description": "journey through distant galaxies"},
    {"theme": "friendly dragon", "description": "tale of an unusual dragon companion"},
    {"theme": "underwater kingdom", "description": "mysterious realm beneath the waves"},
    {"theme": "talking animals", "description": "wise creatures sharing life lessons"},
    {"theme": "fairy garden", "description": "tiny magical beings and their secret world"},
    {"theme": "time travel", "description": "adventures across different eras"},
    {"theme": "magical school", "description": "learning extraordinary abilities"},
    {"theme": "circus adventure", "description": "spectacular performances and friendship"},
    {"theme": "lost treasure", "description": "quest for ancient artifacts"},
    {"theme": "flying carpet", "description": "magical journey through the skies"},
    {"theme": "enchanted toy", "description": "ordinary toy with extraordinary powers"},
    {"theme": "rainbow unicorn", "description": "magical creature bringing joy"},
    {"theme": "giant's castle", "description": "adventure in a colossal dwelling"},
    {"theme": "magical library", "description": "books that come to life"}
]

def check_repetition(text):
    """Verifica repeticiones de frases y palabras"""
    # Dividir en oraciones
    sentences = re.split(r'[.!?]+', text)
    
    # Verificar repeticiones de frases
    sentence_counter = Counter(sentences)
    repeated_sentences = [s for s, count in sentence_counter.items() if count > 1]
    
    # Verificar palabras repetidas consecutivamente
    words = text.lower().split()
    repeated_words = []
    for i in range(len(words)-1):
        if words[i] == words[i+1] and words[i] not in ['the', 'a', 'an']:
            repeated_words.append(words[i])
    
    return repeated_sentences, repeated_words

def grammar_check(text):
    """Solicita una revisión gramatical del texto"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openrouter_api_key}"
    }

    prompt = f"""Please check and correct any grammar or spelling errors in the following text, 
    maintaining the same style and tone for children:
    {text}"""

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
    return text

def generate_unique_story(age, theme_info, previous_stories=[]):
    """Genera un cuento único verificando que no haya repeticiones con historias anteriores"""
    if age < 6:
        length = "very short (about 100 words)"
        complexity = "simple vocabulary and short sentences"
    elif age < 9:
        length = "short (about 200 words)"
        complexity = "basic vocabulary with some challenging words"
    else:
        length = "medium length (about 300 words)"
        complexity = "more complex vocabulary and varied sentence structures"
    
    prompt = f"""Write a {length} children's story in English for a {age}-year-old child.
    Theme: {theme_info['theme']} ({theme_info['description']})
    Requirements:
    - Use {complexity}
    - Include a unique moral lesson
    - Avoid common storytelling clichés
    - Create distinctive characters
    - Use varied sentence structures
    - Include creative descriptions
    - Make sure the story has a clear beginning, middle, and end
    - Avoid phrases or plot elements from these previous stories: {', '.join(previous_stories)}
    - End with a clear moral lesson"""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openrouter_api_key}"
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
        story = response.json()['choices'][0]['message']['content']
        
        # Verificar repeticiones
        repeated_sentences, repeated_words = check_repetition(story)
        if repeated_sentences or repeated_words:
            return generate_unique_story(age, theme_info, previous_stories)
        
        # Verificar gramática
        story = grammar_check(story)
        return story
    else:
        return f"Error generating story: {response.status_code}"

def generate_unique_illustration(theme_info):
    """Genera una ilustración única para cada historia"""
    headers = {
        "Authorization": f"Bearer {together_api_key}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""children's book illustration, {theme_info['description']}, 
    cute, colorful, safe for kids, professional illustration style, 
    clear composition, engaging details, appropriate lighting, 
    whimsical, magical atmosphere, high quality children's book art"""
    
    data = {
        "model": "black-forest-labs/FLUX.1-pro",
        "prompt": prompt,
        "width": 512,
        "height": 512,
        "steps": 28,
        "n": 1,
        "response_format": "b64_json"
    }

    response = requests.post(
        "https://api.together.xyz/v1/images/generations",
        headers=headers,
        json=data
    )

    if response.status_code == 200:
        image_data = response.json()['data'][0]['b64_json']
        return base64.b64decode(image_data)
    return None

def create_word_document(stories_with_images):
    """Crea un documento Word con los cuentos e ilustraciones generados"""
    doc = Document()
    doc.add_heading('Children\'s Stories Collection', 0)

    for i, (age, theme, story, image_data) in enumerate(stories_with_images, 1):
        doc.add_heading(f'Story {i}: {theme.title()}', level=1)
        doc.add_paragraph(f'For age: {age} years')
        
        if image_data:
            image_stream = io.BytesIO(image_data)
            doc.add_picture(image_stream, width=Inches(4))
        
        doc.add_paragraph(story)
        doc.add_paragraph('\n')

    return doc

# Interfaz de usuario
st.title("📚 AI Children's Story Generator with Illustrations")
st.markdown("""
Create unique, age-appropriate stories with custom illustrations for children.
Each story is carefully crafted to match the child's age and includes beautiful artwork.
""")

# Sidebar para controles
with st.sidebar:
    st.header("Story Settings")
    num_stories = st.number_input(
        "Number of stories (max 15)",
        min_value=1,
        max_value=15,
        value=1
    )
    
    age = st.slider(
        "Child's age",
        min_value=4,
        max_value=12,
        value=8,
        help="Select the age of the child to adjust story complexity"
    )
    
    st.markdown("""
    ### Story Length Guide
    - Ages 4-6: Very short stories (~100 words)
    - Ages 7-9: Short stories (~200 words)
    - Ages 10-12: Medium stories (~300 words)
    """)

# Main content
if st.button("Generate Stories", type="primary"):
    with st.spinner("Creating your magical stories and illustrations... 🌟"):
        stories_with_images = []
        previous_stories = []
        selected_themes = random.sample(story_themes, num_stories)
        
        progress_bar = st.progress(0)
        
        for idx, theme_info in enumerate(selected_themes):
            # Actualizar barra de progreso
            progress = (idx + 1) / num_stories
            progress_bar.progress(progress)
            
            # Generar contenido
            story = generate_unique_story(age, theme_info, previous_stories)
            previous_stories.append(theme_info['theme'])
            illustration = generate_unique_illustration(theme_info)
            
            stories_with_images.append((age, theme_info['theme'], story, illustration))
            
            # Mostrar en la interfaz
            with st.container():
                st.subheader(f"📖 {theme_info['theme'].title()}")
                
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    if illustration:
                        image = Image.open(io.BytesIO(illustration))
                        st.image(image, caption=f"Illustration for '{theme_info['theme']}'")
                
                with col2:
                    st.write(story)
                
                st.markdown("---")

        # Crear y ofrecer descarga del documento
        doc = create_word_document(stories_with_images)
        bio = io.BytesIO()
        doc.save(bio)
        
        st.download_button(
            label="📥 Download Stories with Illustrations",
            data=bio.getvalue(),
            file_name="magical_stories_collection.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

# Información adicional
st.markdown("""
---
### About this Story Generator
This AI-powered tool creates:
- Age-appropriate vocabulary and content
- Unique storylines with moral lessons
- Custom illustrations for each story
- Educational and engaging narratives
- Safe and positive content for children

Made with ❤️ for young readers
""")


        # Crear documento Word
        doc = create_word_document(stories_with_images)
        
        # Guardar el documento en memoria
        bio = io.BytesIO()
        doc.save(bio)
        
        # Botón de descarga
        st.download_button(
            label="Download Stories with Illustrations as Word Document",
            data=bio.getvalue(),
            file_name="children_stories_illustrated.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

st.markdown("""
---
### About this app
This app generates age-appropriate children's stories with custom illustrations using AI. 
Each story includes:
- Age-appropriate vocabulary
- Engaging storylines
- Positive messages
- Educational value
- Custom illustration
""")
