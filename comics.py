import streamlit as st
import requests
import base64
from PIL import Image
from io import BytesIO

# Configuración de la página
st.set_page_config(
    page_title="Generador de Memes",
    page_icon="😂",
    layout="centered",
    initial_sidebar_state="auto",
)

# Título de la aplicación
st.title("🖼️ Generador de Memes Personalizados")

# Descripción
st.write("""
    Ingresa una idea para tu meme y generaás tres variantes con ilustraciones únicas.
    La generación de texto se realiza mediante la API de OpenRouter y las imágenes con la API de Together.
""")

def generar_variantes_idea(idea, num_variantes=3):
    """
    Genera variantes de la idea utilizando la API de OpenRouter.
    """
    api_key = st.secrets["OPENROUTER_API_KEY"]
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": f"Genera {num_variantes} ideas para memes basadas en: {idea}"
            }
        ]
    }
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        response_data = response.json()
        mensajes = response_data.get("choices", [])[0].get("message", {}).get("content", "")
        # Suponiendo que las variantes están separadas por saltos de línea
        variantes = [var.strip() for var in mensajes.split('\n') if var.strip()]
        return variantes[:num_variantes]
    except requests.exceptions.HTTPError as http_err:
        st.error(f"Error HTTP al generar variantes: {http_err} - {response.text}")
    except Exception as e:
        st.error(f"Error al generar variantes: {e}")
    return []

def generar_ilustracion(prompt, width=512, height=512):
    """
    Genera una ilustración basada en el prompt utilizando la API de Together.
    """
    api_key = st.secrets["TOGETHER_API_KEY"]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "black-forest-labs/FLUX.1-pro",
        "prompt": prompt,
        "width": width,
        "height": height,
        "steps": 28,
        "n": 1,
        "response_format": "b64_json"
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

def main():
    # Entrada del usuario
    idea = st.text_input("Ingresa la idea para tu meme:", "")

    if st.button("Generar Memes"):
        if not idea.strip():
            st.warning("Por favor, ingresa una idea para generar memes.")
        else:
            with st.spinner("Generando variantes del meme..."):
                variantes = generar_variantes_idea(idea)
            
            if variantes:
                st.success("Variantes generadas exitosamente.")
                for idx, variante in enumerate(variantes, 1):
                    st.markdown(f"### Variante {idx}")
                    st.write(variante)
                    with st.spinner(f"Generando ilustración para variante {idx}..."):
                        imagen = generar_ilustracion(variante)
                    if imagen:
                        st.image(imagen, use_column_width=True)
                    st.markdown("---")
            else:
                st.error("No se pudieron generar variantes del meme.")

if __name__ == "__main__":
    main()
