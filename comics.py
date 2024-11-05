import streamlit as st
import requests
import base64
from PIL import Image
from io import BytesIO

# Configuración de la página
st.set_page_config(
    page_title="Generador de Cómics",
    page_icon="🖼️",
    layout="centered",
    initial_sidebar_state="auto",
)

# Título de la aplicación
st.title("🖼️ Generador de Cómics con Inteligencia Artificial")

# Función para generar descripciones de escenas usando OpenRouter
def generar_descripciones(idea, num_scenes=3):
    api_key = st.secrets["OPENROUTER_API_KEY"]
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    prompt = (
        f"Genera {num_scenes} descripciones detalladas para escenas de un cómic basadas en la siguiente idea:\n\n{idea}\n\n"
        "Cada descripción debe incluir el escenario, los personajes involucrados y la acción principal."
    )
    data = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "user", "content": prompt}
        ],
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        response_data = response.json()
        descripciones = response_data["choices"][0]["message"]["content"].strip().split("\n")
        # Filtrar y limpiar las descripciones
        descripciones = [desc.strip("- ").strip() for desc in descripciones if desc.strip()]
        if len(descripciones) < num_scenes:
            st.warning("Se generaron menos escenas de las solicitadas.")
        return descripciones[:num_scenes]
    except requests.exceptions.HTTPError as http_err:
        st.error(f"Error HTTP al generar descripciones: {http_err} - {response.text}")
    except Exception as e:
        st.error(f"Error al generar descripciones: {e}")
    return []

# Función para generar ilustraciones usando Together API
def generar_ilustracion(prompt, estilo="cómic", width=512, height=512):
    api_key = st.secrets["TOGETHER_API_KEY"]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "black-forest-labs/FLUX.1-pro",
        "prompt": prompt,
        "width": width,
        "height": height,
        "steps": 28,
        "n": 1,
        "response_format": "b64_json",
    }
    try:
        response = requests.post("https://api.together.xyz/v1/images/generations", headers=headers, json=data)
        response.raise_for_status()
        response_data = response.json()
        # Decodificar la imagen de base64
        b64_image = response_data["data"][0]["b64_json"]
        image_bytes = base64.b64decode(b64_image)
        image = Image.open(BytesIO(image_bytes))
        return image
    except requests.exceptions.HTTPError as http_err:
        st.error(f"Error HTTP al generar la imagen: {http_err} - {response.text}")
    except Exception as e:
        st.error(f"Error al generar la imagen: {e}")
    return None

# Interfaz de usuario para ingresar la idea
st.header("Ingresa la Idea para tu Cómic")
idea = st.text_area("Describe la idea de tu cómic aquí:", height=150)

# Botón para generar el cómic
if st.button("Generar Cómic"):
    if not idea.strip():
        st.warning("Por favor, ingresa una idea para generar el cómic.")
    else:
        with st.spinner("Generando descripciones de las escenas..."):
            descripciones = generar_descripciones(idea)
        
        if descripciones:
            st.success("Descripciones generadas exitosamente.")
            for idx, desc in enumerate(descripciones, start=1):
                st.subheader(f"Escena {idx}")
                st.write(desc)
                with st.spinner(f"Generando ilustración para la Escena {idx}..."):
                    imagen = generar_ilustracion(desc)
                if imagen:
                    st.image(imagen, caption=f"Ilustración de la Escena {idx}", use_column_width=True)
                else:
                    st.error(f"No se pudo generar la ilustración para la Escena {idx}.")
                st.markdown("---")
