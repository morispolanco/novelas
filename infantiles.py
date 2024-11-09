import streamlit as st
import requests
import json
from docx import Document
from docx.shared import Inches
from io import BytesIO
import random
from PIL import Image
import base64

# Configuración de la página
st.set_page_config(
    page_title="Generador de Cuentos Infantiles con Ilustraciones",
    layout="centered",
    initial_sidebar_state="auto",
)

# Título de la aplicación
st.title("📚 Generador de Cuentos Infantiles con Ilustraciones")

# Descripción
st.markdown("""
Genera cuentos personalizados en español para niños, adaptados a diferentes grupos de edad. 
Especifica el número de cuentos (hasta 15), y deja que la aplicación cree historias atractivas con temas variados, longitudes apropiadas y hermosas ilustraciones.
""")

# Barra lateral para la entrada del usuario
st.sidebar.header("Parámetros de Entrada")

# Entrada para el número de cuentos
num_stories = st.sidebar.number_input(
    "Número de Cuentos",
    min_value=1,
    max_value=15,
    value=1,
    step=1
)

# Grupos de edad para elegir
age_groups = ["3-5 años", "6-8 años", "9-12 años"]
selected_age_group = st.sidebar.selectbox(
    "Selecciona el Grupo de Edad para los Cuentos",
    age_groups
)

# Botón para generar cuentos
if st.sidebar.button("Generar Cuentos"):
    with st.spinner("Generando cuentos e ilustraciones..."):
        # Función para generar un solo cuento
        def generate_story(theme, age_group):
            api_url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}"
            }

            # Definir el prompt basado en el grupo de edad
            if age_group == "3-5 años":
                prompt = f"Escribe un cuento corto y sencillo en español para niños de {age_group}. El tema es {theme}. Mantén la historia atractiva y fácil de entender."
            elif age_group == "6-8 años":
                prompt = f"Escribe un cuento infantil adecuado en español para niños de {age_group}. El tema es {theme}. Asegúrate de que la historia tenga una trama clara y sea apropiada para este grupo de edad."
            else:  # 9-12 años
                prompt = f"Escribe un cuento infantil atractivo en español para niños de {age_group}. El tema es {theme}. La historia debe tener una trama más compleja y un vocabulario apropiado para este grupo de edad."

            data = {
                "model": "openai/gpt-4o-mini",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }

            try:
                response = requests.post(api_url, headers=headers, data=json.dumps(data))
                response.raise_for_status()
                result = response.json()
                story = result['choices'][0]['message']['content'].strip()
                return story
            except requests.exceptions.HTTPError as http_err:
                st.error(f"Ocurrió un error HTTP: {http_err}")
            except Exception as err:
                st.error(f"Ocurrió un error: {err}")
            return "Lo siento, ocurrió un error al generar el cuento."

        # Función para generar una ilustración usando Together.xyz
        def generate_image(prompt_description):
            together_api_key = st.secrets.get('TOGETHER_API_KEY')
            if not together_api_key:
                st.error("La clave API de Together.xyz no está configurada en los secretos de Streamlit.")
                return None

            api_url = "https://api.together.xyz/v1/images/generations"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {together_api_key}"
            }

            data = {
                "model": "black-forest-labs/FLUX.1.1-pro",
                "prompt": prompt_description,
                "width": 512,
                "height": 512,
                "steps": 1,
                "n": 1,
                "response_format": "b64_json"
            }

            try:
                response = requests.post(api_url, headers=headers, data=json.dumps(data))
                response.raise_for_status()
                result = response.json()
                b64_image = result['data'][0]['b64_json']
                image_bytes = base64.b64decode(b64_image)
                image = Image.open(BytesIO(image_bytes))
                return image
            except requests.exceptions.HTTPError as http_err:
                st.error(f"Ocurrió un error HTTP al generar la imagen: {http_err}")
            except Exception as err:
                st.error(f"Ocurrió un error al generar la imagen: {err}")
            return None

        # Lista predefinida de 50 temas
        themes = [
            "aventura en el bosque",
            "un viaje mágico",
            "amistad y trabajo en equipo",
            "superar miedos",
            "un día en la playa",
            "exploración espacial",
            "misterio submarino",
            "viaje en el tiempo",
            "una búsqueda heroica",
            "aprender a compartir",
            "el castillo encantado",
            "una historia de detectives",
            "compañeros robots",
            "tierra de fantasía",
            "reino animal",
            "el dragón amigable",
            "la princesa valiente",
            "el robot perdido",
            "la isla secreta",
            "un monstruo en el armario",
            "la fábrica de chocolate",
            "el tren mágico",
            "los juguetes que cobran vida",
            "una aventura en el desierto",
            "el bosque de los sueños",
            "el misterioso castillo",
            "el héroe inesperado",
            "la escuela de magia",
            "el cohete a la luna",
            "el puente arcoíris",
            "el viaje al fondo del mar",
            "la casa de los árboles",
            "el robot y el niño",
            "la feria encantada",
            "el tesoro escondido",
            "la carrera de globos",
            "el bosque de las hadas",
            "el caballo volador",
            "la carrera espacial",
            "el jardín secreto",
            "la tormenta de estrellas",
            "el mago y el aprendiz",
            "la ciudad perdida",
            "el misterio del lago",
            "la aventura en la montaña",
            "el libro de los deseos",
            "la isla de los dinosaurios",
            "el viaje al centro de la tierra",
            "el circo de los sueños"
        ]

        # Seleccionar temas para el número de cuentos
        selected_themes = random.sample(themes, num_stories) if num_stories <= len(themes) else random.choices(themes, k=num_stories)

        # Generar todos los cuentos y sus ilustraciones
        stories = []
        for i in range(num_stories):
            theme = selected_themes[i]
            story = generate_story(theme, selected_age_group)
            if story.startswith("Lo siento"):
                image = None
            else:
                # Crear una descripción para la ilustración basada en el tema
                image_prompt = f"Una ilustración colorida y atractiva para un cuento infantil sobre {theme}."
                image = generate_image(image_prompt)
            stories.append({
                "title": f"Cuento {i+1}: {theme.title()}",
                "content": story,
                "image": image
            })

        # Crear un documento de Word
        doc = Document()
        doc.add_heading("Cuentos Infantiles con Ilustraciones", 0)

        for story in stories:
            doc.add_heading(story["title"], level=1)
            doc.add_paragraph(story["content"])
            if story["image"]:
                # Guardar la imagen en un flujo de bytes
                img_byte_arr = BytesIO()
                story["image"].save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()
                
                # Agregar la imagen al documento
                doc.add_picture(BytesIO(img_byte_arr), width=Inches(4))  # Ajuste del ancho a 4 pulgadas para mejor adaptación
                doc.add_paragraph("")  # Espacio adicional después de la imagen

        # Guardar el documento en un flujo de BytesIO
        doc_io = BytesIO()
        doc.save(doc_io)
        doc_io.seek(0)

        # Proporcionar el botón de descarga
        st.success("¡Cuentos e ilustraciones generados con éxito!")
        st.download_button(
            label="📄 Descargar Cuentos como Documento de Word",
            data=doc_io,
            file_name="Cuentos_Infantiles_Con_Ilustraciones.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        # Opcional: mostrar los cuentos e ilustraciones en la aplicación
        with st.expander("Ver Cuentos e Ilustraciones Generados"):
            for story in stories:
                st.markdown(f"### {story['title']}")
                st.write(story["content"])
                if story["image"]:
                    st.image(story["image"], caption="Ilustración del cuento", use_column_width=True)
                else:
                    st.write("No se pudo generar una ilustración para este cuento.")

# Pie de página
st.markdown("---")
st.markdown("© 2024 Generador de Cuentos Infantiles. Desarrollado con OpenRouter, Together.xyz y Streamlit.")
