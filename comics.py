import streamlit as st
import requests
from PIL import Image, ImageDraw, ImageFont
import base64
from io import BytesIO

# Función para generar el texto del meme usando OpenRouter
def generar_texto_meme(idea):
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
                "content": f"Genera un formato de meme basado en la siguiente idea: {idea}. Proporciona el texto para la parte superior y la inferior del meme."
            }
        ]
    }
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        response_data = response.json()
        mensaje = response_data["choices"][0]["message"]["content"].strip()
        
        # Suponiendo que el modelo devuelve el texto en formato:
        # Top: ...
        # Bottom: ...
        top_text = ""
        bottom_text = ""
        for line in mensaje.split('\n'):
            if line.lower().startswith("top:"):
                top_text = line.split(":", 1)[1].strip()
            elif line.lower().startswith("bottom:"):
                bottom_text = line.split(":", 1)[1].strip()
        
        return top_text, bottom_text
    except requests.exceptions.HTTPError as http_err:
        st.error(f"Error HTTP al generar el texto del meme: {http_err} - {response.text}")
    except Exception as e:
        st.error(f"Error al generar el texto del meme: {e}")
    return None, None

# Función para generar la ilustración usando Together API
def generar_ilustracion(prompt, estilo="realistic", width=512, height=512):
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
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        return image
    except requests.exceptions.HTTPError as http_err:
        st.error(f"Error HTTP al generar la imagen: {http_err} - {response.text}")
    except Exception as e:
        st.error(f"Error al generar la imagen: {e}")
    return None

# Función para agregar texto al meme
def agregar_texto_imagen(image, top_text, bottom_text, font_path="arial.ttf", font_size=40):
    draw = ImageDraw.Draw(image)
    width, height = image.size

    # Cargar fuente
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        font = ImageFont.load_default()

    # Función para ajustar el texto al ancho de la imagen
    def ajustar_texto(texto, ancho_max, fuente):
        palabras = texto.split()
        lineas = []
        linea_actual = ""
        for palabra in palabras:
            prueba = f"{linea_actual} {palabra}".strip()
            ancho, _ = draw.textsize(prueba, font=fuente)
            if ancho <= ancho_max:
                linea_actual = prueba
            else:
                lineas.append(linea_actual)
                linea_actual = palabra
        if linea_actual:
            lineas.append(linea_actual)
        return lineas

    # Agregar texto superior
    top_lineas = ajustar_texto(top_text, width - 20, font)
    y = 10
    for linea in top_lineas:
        ancho, alto = draw.textsize(linea, font=font)
        draw.text(((width - ancho) / 2, y), linea, fill="white", font=font, stroke_width=2, stroke_fill="black")
        y += alto

    # Agregar texto inferior
    bottom_lineas = ajustar_texto(bottom_text, width - 20, font)
    y = height - (len(bottom_lineas) * (font_size + 10)) - 10
    for linea in bottom_lineas:
        ancho, alto = draw.textsize(linea, font=font)
        draw.text(((width - ancho) / 2, y), linea, fill="white", font=font, stroke_width=2, stroke_fill="black")
        y += alto

    return image

# Configuración de la aplicación Streamlit
st.set_page_config(page_title="Generador de Memes", page_icon="😂", layout="centered")
st.title("📸 Generador de Memes")
st.write("Introduce una idea y genera un meme personalizado.")

# Entrada de usuario
idea_usuario = st.text_input("Introduce tu idea para el meme:", "")

# Botón para generar el meme
if st.button("Generar Meme") and idea_usuario:
    with st.spinner("Generando el meme..."):
        # Generar el texto del meme
        top_text, bottom_text = generar_texto_meme(idea_usuario)
        
        if top_text and bottom_text:
            st.write("**Texto del Meme:**")
            st.write(f"**Parte Superior:** {top_text}")
            st.write(f"**Parte Inferior:** {bottom_text}")
            
            # Generar la ilustración
            imagen = generar_ilustracion(idea_usuario)
            
            if imagen:
                # Agregar texto a la imagen
                meme = agregar_texto_imagen(imagen, top_text, bottom_text)
                
                # Mostrar el meme
                st.image(meme, caption="¡Aquí está tu meme!", use_column_width=True)
                
                # Opción para descargar el meme
                buffered = BytesIO()
                meme.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                href = f'<a href="data:image/png;base64,{img_str}" download="meme.png">📥 Descargar Meme</a>'
                st.markdown(href, unsafe_allow_html=True)
        else:
            st.error("No se pudo generar el texto del meme. Por favor, intenta de nuevo.")

elif st.button("Generar Meme") and not idea_usuario:
    st.warning("Por favor, introduce una idea para generar el meme.")
