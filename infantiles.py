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

    1. Character Development:
       - Dive into the internal conflicts of the characters. Show their fears, doubts, and small victories to make them more human and relatable. As each character faces a challenge, include moments where they reflect on their insecurities or limitations to enrich their growth.

    2. Consistency in Tone and Age:
       - The stories are aimed at 12-year-old readers, but some themes and emotions may be slightly advanced for this age. Simplify certain moral and emotional decisions, or have the characters act and think in age-appropriate ways to maintain authenticity.

    3. Sensory Details:
       - Use sensory descriptions to make the environments and experiences more immersive. Incorporate smells, sounds, and textures to create a richer atmosphere and help readers feel more connected to the story world.

    4. Subtle Morals:
       - Present the lessons of each story more implicitly rather than explicitly. Allow characters and readers to discover the moral through actions and consequences, making the message more effective and less preachy.

    5. Deepening Character Relationships:
       - Character bonds add an emotional layer to the stories. Show interactions that reveal more about their relationships (conflicts, support, friendships) to help readers feel more emotionally connected to the story.

    6. Gradual Conflicts and Challenges:
       - Ensure that characters face obstacles in a natural progression. This adds tension and makes the resolution more satisfying, as the character overcomes various challenges to achieve their goal.

    7. Conflict Variety:
       - Vary the types of conflicts (internal, external, natural, supernatural, emotional) to give the collection dynamism and avoid a repetitive pattern. This allows for exploration of different types of courage, empathy, and creativity.

    8. Symbols and Recurring Elements:
       - Include symbols or recurring elements (like objects, phrases, or places) that hold special meaning in each story. This unifies the collection thematically, helping readers find connections and meanings across stories.

    9. World Context and Background:
       - In stories with a magical or fantastic world, offer a brief context of the setting or “magical rules” to build a consistent universe. This enhances the story’s appeal and immersion.

    10. Show, Don’t Tell:
       - Instead of directly telling the reader what a character feels or learns, show it through actions, gestures, and decisions. This narrative technique allows readers to interpret the character’s emotions and extract the moral themselves.

    11. Strengthen Background Themes:
       - Ensure each story has a clear central theme (like bravery, friendship, or empathy) and explore it in depth. Consistent themes across the collection give it a cohesive identity.

    12. Develop Memorable Characters:
       - Main characters should have distinctive qualities (like bravery, wit, or humility) that are reflected in their actions and decisions. Add small physical or emotional details to make them more human and easy to remember for readers.

    13. Add Sensory Details:
       - Use sensory descriptions (smell, touch, sound) to immerse readers in the setting of each story. These details enrich the narrative and help readers feel like they’re exploring these worlds with the characters.

    14. Incorporate Clear Conflicts or Challenges:
       - Each story should have a central conflict or challenge for the protagonist to overcome. This creates tension and keeps readers engaged. Additionally, resolving problems or facing dilemmas makes the stories more dynamic.

    15. Show Growth and Learning:
       - Ensure characters grow or learn something meaningful in each story. Lessons or inner changes should feel natural and be reflected in the narrative without feeling forced, making the learning something readers can feel and understand.

    16. Create a Connection with the Reader:
       - Use situations or emotions children can relate to, like curiosity, fear of the unknown, or the search for acceptance. This helps them feel part of the story and better understand the message.

    17. Add Humor and Light Touches:
       - While the stories should contain a lesson, add humor in dialogues or character interactions. This not only makes the reading more entertaining but also balances the story, especially if the message is deep.

    18. Use Rhythm and Variety in Narrative:
       - Play with the rhythm, alternating calm moments with peaks of excitement or tension. Additionally, vary language and narration style in each story for freshness, even with a consistent general tone.

    19. Create Memorable Introductions and Conclusions:
       - The opening lines should capture the reader's attention, and the conclusions should leave a sense of satisfaction or reflection. This makes the story more impactful and memorable.

    20. Convey Positive Values Without Being Moralizing:
       - Instead of making the moral explicit, allow positive values to emerge naturally from characters' decisions and actions. This avoids making stories feel preachy and gives the message a powerful, subtle resonance.
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
