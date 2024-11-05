import streamlit as st
import requests
import base64
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os

def generar_texto_meme(idea_usuario):
    """
    Genera el texto del meme utilizando la API de OpenRouter.
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
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        return image
    except requests.exceptions.HTTPError as http_err:
        st.error(f"Error HTTP al generar la imagen: {http_err} - {response.text}")
    except Exception as e:
        st.error(f"Error al generar la imagen: {e}")
    return None

def cargar_fuentes_arial():
    """
    Carga las fuentes Arial disponibles desde la carpeta 'fonts'.
    Asegúrate de tener las variantes 'arial.ttf', 'arialbd.ttf' y 'ariali.ttf' en la carpeta.
    """
    fuentes = {
        "Normal": "arial.ttf",
        "Negrita": "arialbd.ttf",
        "Cursiva": "ariali.ttf",
    }
    fuentes_disponibles = {}
    for nombre, archivo in fuentes.items():
        ruta_fuente = os.path.join("fonts", archivo)
        if os.path.exists(ruta_fuente):
            fuentes_disponibles[nombre] = ruta_fuente
        else:
            st.warning(f"Fuente '{archivo}' no encontrada. Asegúrate de tener el archivo '{archivo}' en la carpeta 'fonts'.")
    return fuentes_disponibles

def crear_meme(imagen, texto, estilo, color, tamaño):
    """
    Añade el texto generado al meme utilizando la fuente Arial y el estilo seleccionado.

    Args:
        imagen (PIL.Image): Imagen base para el meme.
        texto (str): Texto a añadir en el meme.
        estilo (str): Estilo del texto ('Normal', 'Negrita', 'Cursiva').
        color (str): Color del texto en formato hexadecimal.
        tamaño (int): Tamaño de la fuente.

    Returns:
        PIL.Image: Imagen con el texto añadido.
    """
    ancho, alto = imagen.size
    imagen_editable = imagen.copy()
    draw = ImageDraw.Draw(imagen_editable)

    # Cargar la fuente Arial con el estilo seleccionado
    fuentes_disponibles = cargar_fuentes_arial()
    ruta_fuente = fuentes_disponibles.get(estilo, None)

    try:
        if ruta_fuente:
            font = ImageFont.truetype(ruta_fuente, size=tamaño)
        else:
            # Si no se encuentra la fuente específica, usar la fuente predeterminada
            font = ImageFont.load_default()
            st.warning("Usando fuente predeterminada.")
    except IOError:
        # Fallback si no se puede cargar la fuente específica
        font = ImageFont.load_default()
        st.warning("No se pudo cargar la fuente seleccionada. Usando fuente predeterminada.")

    # Función para dibujar texto con contorno
    def dibujar_texto(texto, posicion_y):
        if texto.strip() == "":
            return
        # Obtener el tamaño del texto
        try:
            text_bbox = draw.textbbox((0, 0), texto, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
        except AttributeError:
            # Para versiones antiguas de Pillow
            text_width, text_height = draw.textsize(texto, font=font)

        x = (ancho - text_width) / 2
        y = posicion_y

        # Añadir contorno al texto para mayor legibilidad
        outline_range = 2
        for adj in range(-outline_range, outline_range + 1):
            if adj != 0:
                draw.text((x + adj, y), texto, font=font, fill="black")
                draw.text((x, y + adj), texto, font=font, fill="black")
                draw.text((x + adj, y + adj), texto, font=font, fill="black")

        # Añadir el texto principal en el color seleccionado
        draw.text((x, y), texto, font=font, fill=color)

    # Dibujar el texto en el centro de la imagen
    try:
        text_bbox = draw.textbbox((0, 0), texto, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
    except AttributeError:
        # Para versiones antiguas de Pillow
        text_width, text_height = draw.textsize(texto, font=font)

    x = (ancho - text_width) / 2
    y = (alto - text_height) / 2

    dibujar_texto(texto, y)

    return imagen_editable

def main():
    st.set_page_config(page_title="Generador de Memes", page_icon="😄", layout="centered")
    st.title("🖼️ Generador de Memes Personalizados con Arial")

    st.markdown("""
    **Instrucciones:**
    1. Introduce una idea o descripción para tu meme.
    2. Personaliza el estilo, color y tamaño del texto.
    3. Haz clic en "Generar Meme".
    4. Espera mientras se genera el texto y la imagen.
    5. Disfruta de tu meme personalizado.
    """)

    # Entrada de la idea del usuario
    idea_usuario = st.text_input("Introduce tu idea para el meme:")

    # Selección de estilo
    st.markdown("### Personalización del Texto")
    estilos_disponibles = ["Normal", "Negrita", "Cursiva"]
    estilo_seleccionado = st.selectbox("Selecciona un estilo de texto:", options=estilos_disponibles, index=0)

    # Selección de color
    color_texto = st.color_picker("Selecciona el color del texto:", "#FFFFFF")

    # Selección de tamaño
    tamaño_texto = st.slider("Selecciona el tamaño del texto:", min_value=10, max_value=100, value=40)

    if st.button("Generar Meme"):
        if idea_usuario.strip() == "":
            st.error("Por favor, introduce una idea para el meme.")
        else:
            with st.spinner("Generando el texto del meme..."):
                texto_meme = generar_texto_meme(idea_usuario)
            
            if texto_meme:
                st.success("Texto del meme generado exitosamente:")
                st.write(f"**{texto_meme}**")
                
                with st.spinner("Generando la imagen del meme..."):
                    imagen = generar_ilustracion(idea_usuario)
                
                if imagen:
                    with st.spinner("Creando el meme final..."):
                        meme = crear_meme(
                            imagen,
                            texto=texto_meme,
                            estilo=estilo_seleccionado,
                            color=color_texto,
                            tamaño=tamaño_texto
                        )
                    
                    if meme:
                        st.image(meme, caption="🎉 Tu meme generado", use_column_width=True)
                        # Opcional: ofrecer descarga del meme
                        buffered = BytesIO()
                        meme.save(buffered, format="PNG")
                        img_str = base64.b64encode(buffered.getvalue()).decode()
                        href = f'<a href="data:file/png;base64,{img_str}" download="meme.png">📥 Descargar Meme</a>'
                        st.markdown(href, unsafe_allow_html=True)
                else:
                    st.error("No se pudo generar la imagen del meme.")
            else:
                st.error("No se pudo generar el texto del meme.")

if __name__ == "__main__":
    main()
