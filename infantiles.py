import streamlit as st
import requests
import json
from docx import Document
from docx.shared import Inches
import io
import random
import base64
from PIL import Image

# Configuración de la página
st.set_page_config(page_title="Children's Story Generator", page_icon="📚") 

# Obtener las API keys de los secretos de Streamlit
openrouter_api_key = st.secrets["OPENROUTER_API_KEY"]
together_api_key = st.secrets["TOGETHER_API_KEY"]

# Temas posibles para los cuentos
story_themes = [
    "magical forest", "space adventure", "friendly dragon", 
    "underwater kingdom", "talking animals", "fairy garden",
    "time travel", "magical school", "circus adventure",
    "lost treasure", "flying carpet", "enchanted toy",
    "rainbow unicorn", "giant's castle", "magical library",
    "desert oasis", "haunted mansion", "talking robots",
    "enchanted mountain", "wizard's apprentice", "snowy village",
    "hidden island", "pirate treasure hunt", "friendly ghost",
    "ancient ruins", "singing mermaids", "mysterious labyrinth",
    "enchanted bakery", "flying boat", "storybook castle",
    "rainforest mystery", "dinosaur discovery", "night sky adventure",
    "jungle expedition", "enchanted carnival", "moonlight picnic"
]

def generate_illustration(prompt):
    """Genera una ilustración usando la API de Together"""
    headers = {
        "Authorization": f"Bearer {together_api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "black-forest-labs/FLUX.1-pro",
        "prompt": f"children's book illustration, cute, colorful, safe for kids: {prompt}",
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
    else:
        return None

def generate_story(age, theme):
    """Genera un cuento basado en la edad y el tema"""
    
    if age < 6:
        length = "very short (about 100 words)"
    elif age < 9:
        length = "short (about 200 words)"
    else:
        length = "medium length (about 300 words)"
    
    prompt = f"""Write a {length} children's story in English for a {age}-year-old child. 
    Theme: {theme}
    Make it engaging, age-appropriate, and include a moral lesson.

    Strengthen Background Themes:
    Ensure each story has a clear central theme (like bravery, friendship, or empathy) and explore it in depth. Consistency in themes, even if they vary across stories, can give the collection a cohesive identity.

    Develop Memorable Characters:
    Main characters should have distinctive qualities (like bravery, wit, or humility) reflected in their actions and decisions. Add small physical or emotional details to make them more relatable and memorable for readers.
    
    Character Development:
    Dive into the internal conflicts of the characters. Showing their fears, doubts, and small victories makes them more human and relatable. As each character faces a challenge, include moments where they reflect on their insecurities or limitations to enrich their growth.
    
    Consistency in Tone and Age:
    The stories are aimed at 12-year-old readers, but some themes and emotions may be slightly advanced for this age. Simplify certain moral and emotional decisions, or have the characters act and think in age-appropriate ways to maintain authenticity.

    Sensory Details:
    Use sensory descriptions to make the environments and experiences more immersive. Incorporating smells, sounds, and textures creates a richer atmosphere and helps the reader feel more connected to the story world.

    Subtle Morals:
    Present the lessons of each story more implicitly than explicitly. Allow characters and readers to discover the moral through actions and consequences, making the message more effective and less preachy.

    Deepening Character Relationships:
    Character bonds add an emotional layer to the stories. Show interactions that reveal more about their relationships (conflicts, support, friendships) to help the reader feel more emotionally connected to the story.

    Gradual Conflicts and Challenges:
    Ensure characters face obstacles in a natural progression. This not only adds tension but also makes the resolution more satisfying, as the character has overcome various challenges to reach their goal.

    Conflict Variety:
    Vary the types of conflicts (internal, external, natural, supernatural, emotional) to give the collection dynamism and avoid a repetitive pattern. This allows exploration of different types of courage, empathy, and creativity.

    Symbols and Recurring Elements:
    Include symbols or recurring elements (like objects, phrases, or places) with special meaning in each story to unify the collection thematically. This can help readers find connections and meanings across stories.

    World Context and Background:
    In stories with a magical or fantastic world, offer a brief context of the setting or “magical rules” to build a consistent universe. This makes the stories more compelling and immersive for the reader.

    Show, Don’t Tell:
    Rather than directly telling the reader what a character is feeling or learning, try to show it through actions, gestures, and decisions. This narrative technique allows the reader to interpret the character’s emotions and understand the moral on their own."""
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openrouter_api_key}"
    }

    data = {
        "model": "google/gemini-flash-1.5",
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

def create_word_document(stories_with_images):
    """Crea un documento Word con los cuentos e ilustraciones generados"""
    doc = Document()
    doc.add_heading('Children\'s Stories Collection', 0)

    for i, (age, theme, story, image_data) in enumerate(stories_with_images, 1):
        doc.add_heading(f'Story {i}: {theme.title()}', level=1)
        doc.add_paragraph(f'For age: {age} years')
        
        # Guardar la imagen temporalmente y añadirla al documento
        if image_data:
            image_stream = io.BytesIO(image_data)
            doc.add_picture(image_stream, width=Inches(4))
        
        doc.add_paragraph(story)
        doc.add_paragraph('\n')

    return doc

# Interfaz de usuario
st.title("📚 Children's Story Generator with Illustrations")

num_stories = st.number_input(
    "How many stories would you like to generate? (max 15)",
    min_value=1,
    max_value=15,
    value=1
)

age = st.slider("Select child's age", 4, 12, 8)

if st.button("Generate Stories"):
    with st.spinner("Generating your stories and illustrations... Please wait"):
        stories_with_images = []
        selected_themes = random.sample(story_themes, num_stories)
        
        for theme in selected_themes:
            # Generar cuento
            story = generate_story(age, theme)
            
            # Generar ilustración
            illustration = generate_illustration(theme)
            
            stories_with_images.append((age, theme, story, illustration))
            
            # Mostrar en la interfaz
            st.subheader(f"Story: {theme.title()}")
            
            # Mostrar la ilustración
            if illustration:
                image = Image.open(io.BytesIO(illustration))
                st.image(image, caption=f"Illustration for '{theme}'")
            
            st.write(story)
            st.markdown("---")

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
