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
    La idea se convertirá primero a un formato de meme estándar, y luego se generarán variantes.
    La generación de texto se realiza mediante la API de OpenRouter y las imágenes con la API de Together.
""")

def convertir_a_formato_meme(idea):
    """
    Convierte la idea ingresada por el usuario a un formato de meme estándar.
    """
    api_key = st.secrets["OPENROUTER_API_KEY"]
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    prompt = f"Convierte la siguiente idea en un formato de meme con 'Top Text' y 'Bottom Text': {idea}"
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
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        response_data = response.json()
        mensaje = response_data.get("choices", [])[0].get("message", {}).get("content", "")
        # Extraer Top Text y Bottom Text
        top_text = ""
        bottom_text = ""
        if "Top Text:" in mensaje and "Bottom Text:" in mensaje:
            top_text = mensaje.split("Top Text:")[1].split("Bottom Text:")[0].strip()
            bottom_text = mensaje.split("Bottom Text:")[1].strip()
        return {"top_text": top_text, "bottom_text": bottom_text}
    except requests.exceptions.HTTPError as http_err:
        st.error(f"Error HTTP al convertir a formato de meme: {http_err} - {response.text}")
    except Exception as e:
        st.error(f"Error al convertir a formato de meme: {e}")
    return {"top_text": "", "bottom_text": ""}

def generar_variantes_meme(formato_meme, num_variantes=3):
    """
    Genera variantes del formato de meme utilizando la API de OpenRouter.
    """
    api_key = st.secrets["OPENROUTER_API_KEY"]
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    # Crear un prompt basado en el formato de meme existente
    prompt = f"Genera {num_variantes} variantes de este formato de meme:\nTop Text: {formato_meme['top_text']}\nBottom Text: {formato_meme['bottom_text']}"
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
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        response_data = response.json()
        mensaje = response_data.get("choices", [])[0].get("message", {}).get("content", "")
        variantes = []
        for line in mensaje.split('\n'):
            if "Top Text:" in line and "Bottom Text:" in line:
                top = line.split("Top Text:")[1].split("Bottom Text:")[0].strip()
                bottom = line.split("Bottom Text:")[1].strip()
                variantes.append({"top_text": top, "bottom_text": bottom})
            elif "Top Text:" in line:
                top = line.split("Top Text:")[1].strip()
                # Asumir que la siguiente línea es Bottom Text
                index = mensaje.split('\n').index(line)
                if index + 1 < len(mensaje.split('\n')):
                    next_line = mensaje.split('\n')[index + 1]
                    if "Bottom Text:" in next_line:
                        bottom = next_line.split("Bottom Text:")[1].strip()
                        variantes.append({"top_text": top, "bottom_text": bottom})
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
            with st.spinner("Convirtiendo la idea al formato de meme..."):
                formato_meme = convertir_a_formato_meme(idea)
            
            if formato_meme['top_text'] and formato_meme['bottom_text']:
                st.success("Formato de meme generado exitosamente.")
                st.markdown(f"**Top Text:** {formato_meme['top_text']}")
                st.markdown(f"**Bottom Text:** {formato_meme['bottom_text']}")
                st.markdown("---")
                
                with st.spinner("Generando variantes del meme..."):
                    variantes = generar_variantes_meme(formato_meme)
                
                if variantes:
                    st.success("Variantes generadas exitosamente.")
                    for idx, variante in enumerate(variantes, 1):
                        st.markdown(f"### Variante {idx}")
                        st.markdown(f"**Top Text:** {variante['top_text']}")
                        st.markdown(f"**Bottom Text:** {variante['bottom_text']}")
                        # Crear un prompt para la ilustración combinando ambos textos
                        prompt_imagen = f"{variante['top_text']} - {variante['bottom_text']}"
                        with st.spinner(f"Generando ilustración para variante {idx}..."):
                            imagen = generar_ilustracion(prompt_imagen)
                        if imagen:
                            st.image(imagen, use_column_width=True)
                        st.markdown("---")
                else:
                    st.error("No se pudieron generar variantes del meme.")
            else:
                st.error("No se pudo convertir la idea al formato de meme. Intenta con otra idea.")

if __name__ == "__main__":
    main()
