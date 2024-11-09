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
    "rainbow unicorn", "giant's castle", "magical library"
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
    Use simple language for younger children and more complex vocabulary for older ones.
    prompt = f"""Write a {length} childrens story in English for a {age}-year-old child. 
Theme: {theme}
Make it engaging, age-appropriate, and include a moral lesson.

Strengthen Background Themes:
Ensure each story has a clear central theme (like bravery, friendship, or empathy) and explore it in depth. Consistency in themes, even if they vary across stories, can give the collection a cohesive identity.

Develop Memorable Characters:
Main characters should have distinctive qualities (like bravery, wit, or humility) reflected in their actions and decisions. Add small physical or emotional details to make them more relatable and memorable for readers.

Add Sensory Details:
Use sensory descriptions (smell, touch, sound) to immerse readers in the story's environment. These details enrich the narrative and help readers feel as if they're exploring these worlds alongside the characters.

Incorporate Clear Conflicts or Challenges:
Each story should have a central conflict or challenge the protagonist must overcome. This creates tension and keeps readers engaged. Additionally, when characters resolve problems or face dilemmas, the stories become more dynamic.

Show Growth and Learning:
Ensure that characters grow or learn something meaningful in each story. The lessons or inner changes should be natural and reflected in the narrative without feeling forced, making the learning something the reader can feel and understand.

Create a Connection with the Reader:
Use situations or emotions children can relate to, like curiosity, fear of the unknown, or the search for acceptance. This helps them feel part of the story and better understand the message.

Add Humor and Light Touches:
While the stories should contain a lesson, add humor in the dialogues or character interactions. This not only makes the reading more entertaining but also balances the story, especially if the message is deep.

Use Rhythm and Variety in Narrative:
Play with rhythm, alternating calm moments with peaks of excitement or tension. Additionally, vary language and narrative style in each story to give a fresh feel, even though they share a general tone.

Create Memorable Introductions and Conclusions:
The opening lines should capture the readers attention, and the conclusions should leave a sense of satisfaction or reflection. This makes the story more impactful and memorable.

Convey Positive Values Without Being Didactic:
Instead of making the moral explicit, allow positive values to emerge naturally from the characters decisions and actions. This avoids making the stories feel preachy and gives the message a more powerful and subtle resonance."""
"""

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
