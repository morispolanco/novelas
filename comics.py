import streamlit as st
import requests
import base64
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

def generar_texto_meme(idea_usuario):
    # [Función igual que antes]
    pass

def generar_ilustracion(prompt, width=512, height=512):
    # [Función igual que antes]
    pass

def crear_meme(imagen, texto, color, tamaño):
    """
    Añade el texto generado al meme utilizando la fuente predeterminada de Pillow.
    """
    ancho, alto = imagen.size
    imagen_editable = imagen.copy()
    draw = ImageDraw.Draw(imagen_editable)

    # Cargar la fuente predeterminada con el tamaño seleccionado
    font = ImageFont.load_default()
    
    try:
        font = ImageFont.truetype("arial.ttf", size=tamaño)
    except:
        st.warning("No se pudo cargar 'arial.ttf'. Usando fuente predeterminada.")
        font = ImageFont.load_default()

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
    st.title("🖼️ Generador de Memes Personalizados")

    st.markdown("""
    **Instrucciones:**
    1. Introduce una idea o descripción para tu meme.
    2. Personaliza el color y tamaño del texto.
    3. Haz clic en "Generar Meme".
    4. Espera mientras se genera el texto y la imagen.
    5. Disfruta de tu meme personalizado.
    """)

    # Entrada de la idea del usuario
    idea_usuario = st.text_input("Introduce tu idea para el meme:")

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
                        st.error("No se pudo crear el meme final.")
                else:
                    st.error("No se pudo generar la imagen del meme.")
            else:
                st.error("No se pudo generar el texto del meme.")

if __name__ == "__main__":
    main()
