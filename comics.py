import streamlit as st
import requests
import base64
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

def generar_texto_meme(idea_usuario):
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
                "content": f"Convierte esta idea en un texto de meme divertido: {idea_usuario}"
            }
        ]
    }
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        response_data = response.json()
        texto_meme = response_data["choices"][0]["message"]["content"].strip()
        return texto_meme
    except requests.exceptions.HTTPError as http_err:
        st.error(f"Error HTTP al generar el texto del meme: {http_err} - {response.text}")
    except Exception as e:
        st.error(f"Error al generar el texto del meme: {e}")
    return None

def generar_ilustracion(prompt, width=512, height=512):
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

def crear_meme(imagen, texto):
    # Añade el texto al meme
    ancho, alto = imagen.size
    imagen_editable = imagen.copy()
    draw = ImageDraw.Draw(imagen_editable)
    try:
        font = ImageFont.truetype("arial.ttf", size=int(alto/10))
    except IOError:
        # Si no se encuentra la fuente arial.ttf, usar una fuente predeterminada
        font = ImageFont.load_default()
    text_width, text_height = draw.textsize(texto, font=font)
    x = (ancho - text_width) / 2
    y = alto - text_height - 10
    # Añadir contorno al texto
    outline_range = 2
    for adj in range(-outline_range, outline_range+1):
        draw.text((x+adj, y), texto, font=font, fill="black")
        draw.text((x, y+adj), texto, font=font, fill="black")
        draw.text((x+adj, y+adj), texto, font=font, fill="black")
    # Añadir texto blanco encima
    draw.text((x, y), texto, font=font, fill="white")
    return imagen_editable

def main():
    st.title("Generador de Memes")
    idea_usuario = st.text_input("Introduce tu idea para el meme:")
    if st.button("Generar Meme"):
        if idea_usuario:
            with st.spinner("Generando el texto del meme..."):
                texto_meme = generar_texto_meme(idea_usuario)
            if texto_meme:
                st.write("**Texto del Meme:**")
                st.write(texto_meme)
                with st.spinner("Generando la imagen del meme..."):
                    imagen = generar_ilustracion(idea_usuario)
                if imagen:
                    meme = crear_meme(imagen, texto_meme)
                    st.image(meme, caption="Tu meme generado")
        else:
            st.error("Por favor, introduce una idea para el meme.")

if __name__ == "__main__":
    main()
