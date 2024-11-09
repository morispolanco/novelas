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
import time

# Configuración de la página
st.set_page_config(
    page_title="AI Children's Story Generator",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS personalizado
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        height: 3em;
        background-color: #ff6b6b;
        color: white;
    }
    .story-container {
        border: 1px solid #e0e0e0;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .story-title {
        color: #ff6b6b;
        font-size: 1.5rem;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Obtener las API keys de los secretos de Streamlit
openrouter_api_key = st.secrets["OPENROUTER_API_KEY"]
together_api_key = st.secrets["TOGETHER_API_KEY"]

# Temas posibles para los cuentos con descripciones únicas
story_themes = [
    {
        "theme": "magical forest",
        "description": "enchanted woods with mystical creatures",
        "elements": ["ancient trees", "glowing mushrooms", "talking animals"]
    },
    {
        "theme": "space adventure",
        "description": "journey through distant galaxies",
        "elements": ["starships", "alien friends", "mysterious planets"]
    },
    {
        "theme": "friendly dragon",
        "description": "tale of an unusual dragon companion",
        "elements": ["gentle giant", "magical powers", "unlikely friendship"]
    },
    {
        "theme": "underwater kingdom",
        "description": "mysterious realm beneath the waves",
        "elements": ["merpeople", "coral castles", "sea creatures"]
    },
    {
        "theme": "time travel",
        "description": "adventures across different eras",
        "elements": ["time machine", "historical figures", "future worlds"]
    },
    {
        "theme": "magical school",
        "description": "learning extraordinary abilities",
        "elements": ["spells", "magical creatures", "special lessons"]
    },
    {
        "theme": "flying carpet",
        "description": "magical journey through the skies",
        "elements": ["ancient magic", "cloud cities", "aerial adventures"]
    },
    {
        "theme": "enchanted toy",
        "description": "ordinary toy with extraordinary powers",
        "elements": ["living toys", "magical transformation", "friendship"]
    },
    {
        "theme": "rainbow unicorn",
        "description": "magical creature bringing joy",
        "elements": ["color magic", "healing powers", "spreading happiness"]
    },
    {
        "theme": "giant's castle",
        "description": "adventure in a colossal dwelling",
        "elements": ["huge furniture", "magical objects", "friendly giant"]
    },
    {
        "theme": "magical library",
        "description": "books that come to life",
        "elements": ["living stories", "book characters", "magical knowledge"]
    }
]

def check_repetition(text):
    """Verifica repeticiones de frases y palabras"""
    # Dividir en oraciones
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
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

def analyze_text_complexity(text, age):
    """Analiza la complejidad del texto para la edad objetivo"""
    words = text.split()
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    avg_word_length = sum(len(word) for word in words) / len(words)
    avg_sentence_length = len(words) / len(sentences)
    
    # Criterios por edad
    if age < 6:
        return (avg_word_length <= 4.5 and avg_sentence_length <= 8)
    elif age < 9:
        return (avg_word_length <= 5.0 and avg_sentence_length <= 12)
    else:
        return (avg_word_length <= 5.5 and avg_sentence_length <= 15)
def generate_unique_story(age, theme_info, previous_stories=[]):
    """Genera un cuento único con una estructura narrativa mejorada"""
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
    Story elements to include: {', '.join(theme_info['elements'])}

    Essential Story Requirements:
    1. Narrative Structure:
       - Maintain consistent {random.choice(['past', 'present'])} tense throughout
       - Create smooth transitions between scenes
       - Ensure a clear beginning, middle, and end
       - Develop key conflicts with appropriate depth
       - Include dialogue that advances the story

    2. Character Development:
       - Show emotional growth through actions and reactions
       - Create distinctive personality traits
       - Include relatable challenges
       - Show character transformation

    3. Language and Style:
       - Use {complexity}
       - Employ varied synonyms to avoid repetition
       - Include sensory details
       - Create vivid but concise descriptions
       - Use age-appropriate metaphors

    4. Thematic Elements:
       - Weave moral lessons naturally into the story
       - Allow readers to discover the message through experiences
       - Create meaningful conflict resolution
       - Include subtle learning opportunities

    5. Age-Specific Considerations:
    {
        "4-6": "- Use simple cause and effect\n- Include clear emotional situations\n- Repeat key phrases sparingly\n- Focus on single, clear messages",
        "7-9": "- Add subtle humor\n- Include problem-solving elements\n- Develop friendship themes\n- Explore basic emotions",
        "10-12": "- Include complex emotional scenarios\n- Add layers to character motivations\n- Explore deeper themes\n- Include more sophisticated humor"
    }[f"{'4-6' if age < 6 else '7-9' if age < 9 else '10-12'}"]

    Avoid:
    - Direct moralization
    - Excessive description
    - Complex vocabulary for young ages
    - Plot elements from: {', '.join(previous_stories)}
    - Common storytelling clichés
    """

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openrouter_api_key}"
    }

    data = {
        "model": "google/gemini-flash-1.5-8b",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )

        if response.status_code == 200:
            story = response.json()['choices'][0]['message']['content']
            
            # Verificaciones de calidad
            repeated_sentences, repeated_words = check_repetition(story)
            if repeated_sentences or repeated_words:
                return generate_unique_story(age, theme_info, previous_stories)
            
            if not analyze_text_complexity(story, age):
                return generate_unique_story(age, theme_info, previous_stories)
            
            return story
        else:
            raise Exception(f"API Error: {response.status_code}")
            
    except Exception as e:
        st.error(f"Error generating story: {str(e)}")
        return None

def generate_illustration(theme_info):
    """Genera una ilustración única para cada historia"""
    headers = {
        "Authorization": f"Bearer {together_api_key}",
        "Content-Type": "application/json"
    }
    
    elements_description = ", ".join(theme_info['elements'])
    prompt = f"""children's book illustration, {theme_info['description']}, 
    including {elements_description}, cute, colorful, safe for kids, 
    professional illustration style, clear composition, engaging details, 
    appropriate lighting, whimsical style, magical atmosphere"""
    
    data = {
        "model": "black-forest-labs/FLUX.1-pro",
        "prompt": prompt,
        "width": 512,
        "height": 512,
        "steps": 28,
        "n": 1,
        "response_format": "b64_json"
    }

    try:
        response = requests.post(
            "https://api.together.xyz/v1/images/generations",
            headers=headers,
            json=data,
            timeout=30
        )

        if response.status_code == 200:
            image_data = response.json()['data'][0]['b64_json']
            return base64.b64decode(image_data)
        else:
            raise Exception(f"API Error: {response.status_code}")
            
    except Exception as e:
        st.error(f"Error generating illustration: {str(e)}")
        return None
def create_word_document(stories_with_images):
    """Crea un documento Word con los cuentos e ilustraciones"""
    doc = Document()
    doc.add_heading('Magical Stories Collection', 0)

    for i, (age, theme_info, story, image_data) in enumerate(stories_with_images, 1):
        # Añadir título y metadata
        doc.add_heading(f'Story {i}: {theme_info["theme"].title()}', level=1)
        doc.add_paragraph(f'For ages: {age} years')
        doc.add_paragraph(f'Theme: {theme_info["description"]}')
        
        # Añadir ilustración
        if image_data:
            image_stream = io.BytesIO(image_data)
            doc.add_picture(image_stream, width=Inches(4))
        
        # Añadir historia
        doc.add_paragraph(story)
        doc.add_paragraph('\n')

    return doc

# Interfaz de usuario
st.title("🌟 Magical Stories Generator")
st.markdown("""
Create unique, beautifully illustrated stories for children of all ages.
Each story is carefully crafted with age-appropriate content and accompanied by custom artwork.
""")

# Sidebar para controles
with st.sidebar:
    st.header("Story Settings")
    num_stories = st.number_input(
        "Number of stories to generate",
        min_value=1,
        max_value=15,
        value=1,
        help="Choose how many stories you want to create (maximum 15)"
    )
    
    age = st.slider(
        "Child's age",
        min_value=4,
        max_value=12,
        value=8,
        help="Select the age to adjust story complexity and content"
    )
    
    st.markdown("""
    ### Age Guidelines
    - Ages 4-6: Very short stories with simple language
    - Ages 7-9: Short stories with basic vocabulary
    - Ages 10-12: Longer stories with more complex themes
    """)

# Generación de historias
if st.button("✨ Generate Magical Stories", type="primary"):
    with st.spinner("Creating your magical stories... 🌟"):
        stories_with_images = []
        previous_stories = []
        selected_themes = random.sample(story_themes, num_stories)
        
        progress_bar = st.progress(0)
        
        for idx, theme_info in enumerate(selected_themes):
            # Actualizar progreso
            progress = (idx + 1) / (num_stories * 2)  # Dividido por 2 para contar historia e ilustración
            progress_bar.progress(progress)
            
            # Generar historia
            story = generate_unique_story(age, theme_info, previous_stories)
            previous_stories.append(theme_info['theme'])
            
            # Actualizar progreso para ilustración
            progress = (idx + 1.5) / (num_stories * 2)
            progress_bar.progress(progress)
            
            # Generar ilustración
            illustration = generate_illustration(theme_info)
            
            if story:
                stories_with_images.append((age, theme_info, story, illustration))
                
                # Mostrar en la interfaz
                with st.container():
                    st.markdown(f"### 📖 {theme_info['theme'].title()}")
                    
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        if illustration:
                            image = Image.open(io.BytesIO(illustration))
                            st.image(image, caption=f"Illustration for '{theme_info['theme']}'")
                    
                    with col2:
                        st.markdown(f"**Theme**: {theme_info['description']}")
                        st.write(story)
                    
                    st.markdown("---")

        if stories_with_images:
            # Crear documento Word
            doc = create_word_document(stories_with_images)
            bio = io.BytesIO()
            doc.save(bio)
            
            st.download_button(
                label="📥 Download Your Magical Stories Collection",
                data=bio.getvalue(),
                file_name="magical_stories_collection.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

# Información adicional
st.markdown("""
---
### About the Magical Stories Generator
This AI-powered tool creates:
- Age-appropriate stories with meaningful messages
- Custom illustrations for each story
- Educational and engaging narratives
- Safe and positive content for children

Each story is unique and crafted to:
- Develop imagination and creativity
- Encourage reading and learning
- Promote positive values
- Create magical moments for young readers

Made with ❤️ for young minds
""")
