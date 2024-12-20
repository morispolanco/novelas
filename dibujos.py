import streamlit as st
import requests
from io import BytesIO
from PIL import Image
import base64

# Configuración de la página
st.set_page_config(page_title="Generador de Ilustraciones de Escenas", layout="centered")

# Título de la aplicación
st.title("Generador de Ilustraciones de Escenas")

# Instrucciones
st.markdown("""
Ingresa una descripción de la escena que deseas ilustrar, selecciona un estilo artístico y elige el tamaño de la imagen. 
La aplicación transformará esta información en un prompt adecuado para el modelo FLUX de Stable Diffusion, 
incluyendo un prompt negativo para controlar la calidad y características de la imagen, 
y generará **dos** imágenes con las dimensiones especificadas.
""")

def transform_description_and_style_to_prompt(description, style):
    """
    Transforma la descripción de la escena y el estilo artístico en un prompt optimizado para el modelo FLUX 
    utilizando la API de OpenRouter, incluyendo un prompt negativo.
    """
    openrouter_api_key = st.secrets["OPENROUTER_API_KEY"]
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openrouter_api_key}"
    }
    
    # Prompt negativo definido
    negative_prompt = "(no text, no hard edges, no vibrant colors, no harsh lighting, no digital art, no watermarks, no low resolution, no pixelation, no bad art, no beginner, no amateur)"
    
    # Prompt positivo basado en la entrada del usuario
    positive_prompt = f"{description}, {style}"
    
    # Construcción del prompt para OpenRouter siguiendo la estructura recomendada
    prompt_for_openrouter = (
        f"Transforma la siguiente descripción y estilo en un prompt detallado y optimizado para el modelo FLUX de Stable Diffusion:\n\n"
        f"Descripción: {description}\n"
        f"Estilo artístico: {style}\n\n"
        f"Prompt: {positive_prompt} {negative_prompt}"
    )
    
    data = {
        "model": "openai/gpt-4o-mini",  # Verificar el nombre correcto del modelo
        "messages": [
            {
                "role": "user",
                "content": prompt_for_openrouter
            }
        ]
    }
    
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        response_json = response.json()
        
        # Validar la estructura de la respuesta
        if "choices" in response_json and len(response_json["choices"]) > 0:
            prompt = response_json["choices"][0]["message"]["content"].strip()
            return prompt
        else:
            st.error("La respuesta de OpenRouter no contiene el formato esperado.")
    except requests.exceptions.HTTPError as http_err:
        st.error(f"Error HTTP al transformar la descripción y estilo: {http_err}")
    except Exception as e:
        st.error(f"Error al transformar la descripción y estilo: {e}")
    return None

def generate_images(prompt, width, height, num_images=2):
    """
    Genera múltiples imágenes utilizando la API de Together (Stable Diffusion) a partir de un prompt.
    Las imágenes tendrán el tamaño especificado por el usuario.
    """
    together_api_key = st.secrets["TOGETHER_API_KEY"]
    headers = {
        "Authorization": f"Bearer {together_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "black-forest-labs/FLUX.1-pro",  # Verificar el nombre correcto del modelo
        "prompt": prompt,
        "width": width,
        "height": height,
        "steps": 28,
        "n": num_images,  # Solicitar múltiples imágenes
        "response_format": "b64_json"
    }
    try:
        response = requests.post("https://api.together.xyz/v1/images/generations", headers=headers, json=data)
        response.raise_for_status()
        response_data = response.json()
        
        images = []
        # Validar la estructura de la respuesta
        if "data" in response_data and len(response_data["data"]) >= num_images:
            for i in range(num_images):
                b64_image = response_data["data"][i].get("b64_json")
                if b64_image:
                    image_bytes = base64.b64decode(b64_image)
                    image = Image.open(BytesIO(image_bytes))
                    images.append(image)
                else:
                    st.error(f"La imagen {i+1} no contiene datos en formato base64.")
        else:
            st.error("La respuesta de Together no contiene suficientes datos de imagen.")
        return images
    except requests.exceptions.HTTPError as http_err:
        st.error(f"Error HTTP al generar las imágenes: {http_err}")
    except Exception as e:
        st.error(f"Error al generar las imágenes: {e}")
    return None

# Opciones de estilos artísticos soportados por FLUX
supported_styles = [
    "Realismo",
    "Impresionismo",
    "Expresionismo",
    "Surrealismo",
    "Arte Abstracto",
    "Arte Digital",
    "Estilo Manga",
    "Estilo de Cómic",
    "Arte Minimalista",
    "Arte Pop",
    "Cyberpunk",
    "Arte Gótico",
    "Steampunk",
    "Arte Deco",
    "Arte Futurista",
    "Arte Fantástico",
    "Arte Sci-Fi",
    "Arte Barroco",
    "Arte Moderno"
]

# Entrada del usuario: Descripción de la escena
scene_description = st.text_area(
    "Descripción de la Escena",
    height=150,
    placeholder="Ingresa la descripción de la escena que deseas ilustrar aquí..."
)

# Selección del estilo artístico
st.markdown("**Selecciona un estilo artístico para la ilustración:**")
selected_style = st.selectbox(
    "Estilo Artístico",
    options=supported_styles,
    index=0,
    help="Selecciona un estilo artístico para guiar la generación de la ilustración."
)

# Alternativamente, permitir que el usuario ingrese un estilo personalizado
custom_style = st.text_input(
    "O ingresa un estilo artístico personalizado",
    placeholder="Por ejemplo: cyberpunk, arte gótico, etc."
)

# Selección del tamaño de la imagen
st.markdown("**Selecciona el tamaño de la imagen:**")

# Opciones de tamaños predefinidos
predefined_sizes = {
    "Pequeño (512x512)": (512, 512),
    "Mediano (768x768)": (768, 768),
    "Grande (1024x768)": (1024, 768),
    "Personalizado": None  # Indica que se ingresarán dimensiones personalizadas
}

size_option = st.selectbox(
    "Tamaño de la Imagen",
    options=list(predefined_sizes.keys()),
    index=0,
    help="Selecciona un tamaño predefinido o elige 'Personalizado' para ingresar dimensiones específicas."
)

# Variables para almacenar el tamaño seleccionado
selected_width = None
selected_height = None

if size_option == "Personalizado":
    col1, col2 = st.columns(2)
    with col1:
        selected_width = st.number_input(
            "Ancho (px)",
            min_value=64,
            max_value=2048,
            value=1024,
            step=64,
            help="Ingresa el ancho de la imagen en píxeles. Valores recomendados entre 64 y 2048."
        )
    with col2:
        selected_height = st.number_input(
            "Alto (px)",
            min_value=64,
            max_value=2048,
            value=768,
            step=64,
            help="Ingresa el alto de la imagen en píxeles. Valores recomendados entre 64 y 2048."
        )
else:
    selected_width, selected_height = predefined_sizes[size_option]

# Botón para generar las ilustraciones
if st.button("Generar Ilustraciones"):
    if not scene_description.strip():
        st.warning("Por favor, ingresa una descripción de la escena.")
    elif not (selected_style.strip() or custom_style.strip()):
        st.warning("Por favor, selecciona un estilo artístico o ingresa uno personalizado.")
    elif size_option == "Personalizado" and (selected_width is None or selected_height is None):
        st.warning("Por favor, ingresa las dimensiones personalizadas para la imagen.")
    else:
        # Determinar el estilo a utilizar
        style_to_use = custom_style.strip() if custom_style.strip() else selected_style.strip()
        
        # Determinar el tamaño de la imagen
        width = selected_width
        height = selected_height
        
        # Validación adicional de dimensiones
        if width % 64 != 0 or height % 64 != 0:
            st.warning("Por favor, ingresa dimensiones que sean múltiplos de 64 para garantizar la compatibilidad.")
        elif width < 64 or height < 64:
            st.warning("Las dimensiones mínimas recomendadas son 64x64 píxeles.")
        elif width > 2048 or height > 2048:
            st.warning("Las dimensiones máximas recomendadas son 2048x2048 píxeles.")
        else:
            with st.spinner("Transformando la descripción y estilo en un prompt para el modelo FLUX..."):
                prompt = transform_description_and_style_to_prompt(scene_description, style_to_use)
            
            if prompt:
                st.subheader("Prompt Generado para el Modelo FLUX de Stable Diffusion")
                st.write(prompt)
                
                with st.spinner("Generando las imágenes con el modelo FLUX de Stable Diffusion..."):
                    images = generate_images(prompt, width, height, num_images=2)
            
                if images:
                    st.subheader("Ilustraciones Generadas")
                    # Mostrar las dos imágenes lado a lado
                    col1, col2 = st.columns(2)
                    with col1:
                        st.image(images[0], caption="Imagen 1 generada por FLUX de Stable Diffusion", use_column_width=True)
                    with col2:
                        st.image(images[1], caption="Imagen 2 generada por FLUX de Stable Diffusion", use_column_width=True)
                else:
                    st.error("No se pudieron generar las imágenes.")
