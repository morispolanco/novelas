import streamlit as st
import requests
import json
from docx import Document
from io import BytesIO
import random

# Configuración de la página
st.set_page_config(
    page_title="Generador de Cuentos Infantiles",
    layout="centered",
    initial_sidebar_state="auto",
)

# Título de la aplicación
st.title("📚 Generador de Cuentos Infantiles")

# Descripción
st.markdown("""
Genera cuentos personalizados en español para niños, adaptados a diferentes grupos de edad. 
Especifica el número de cuentos (hasta 15), y deja que la aplicación cree historias atractivas con temas variados y longitudes apropiadas.
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
    with st.spinner("Generando cuentos..."):
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

        # Generar todos los cuentos
        stories = []
        for i in range(num_stories):
            theme = selected_themes[i]
            story = generate_story(theme, selected_age_group)
            stories.append({
                "title": f"Cuento {i+1}: {theme.title()}",
                "content": story
            })

        # Crear un documento de Word
        doc = Document()
        doc.add_heading("Cuentos Infantiles", 0)

        for story in stories:
            doc.add_heading(story["title"], level=1)
            doc.add_paragraph(story["content"])

        # Guardar el documento en un flujo de BytesIO
        doc_io = BytesIO()
        doc.save(doc_io)
        doc_io.seek(0)

        # Proporcionar el botón de descarga
        st.success("¡Cuentos generados con éxito!")
        st.download_button(
            label="📄 Descargar Cuentos como Documento de Word",
            data=doc_io,
            file_name="Cuentos_Infantiles.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        # Opcional: mostrar los cuentos en la aplicación
        with st.expander("Ver Cuentos Generados"):
            for story in stories:
                st.markdown(f"### {story['title']}")
                st.write(story['content'])

# Pie de página
st.markdown("---")
st.markdown("© 2024 Generador de Cuentos Infantiles. Desarrollado con OpenRouter y Streamlit.")
