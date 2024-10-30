import streamlit as st
import requests
import json
import time

# Configuración de la página
st.set_page_config(
    page_title="Editor de Escenas de Novela",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Título de la aplicación
st.title("Editor de Escenas de Novela con Sugerencias")

# Descripción
st.markdown("""
Esta aplicación te permite pegar el texto de una escena de una novela y tus críticas o sugerencias de mejora. 
Al aplicar las sugerencias, la escena será regenerada con las modificaciones propuestas.
""")

# Área de texto para la escena
scene_text = st.text_area(
    "Pega el texto de la escena de la novela aquí:",
    height=300,
    placeholder="Escribe o pega aquí el texto de tu escena..."
)

# Área de texto para las críticas o sugerencias
feedback_text = st.text_area(
    "Pega tus críticas o sugerencias de mejora aquí:",
    height=200,
    placeholder="Escribe o pega aquí tus críticas o sugerencias..."
)

# Función para procesar la escena con las sugerencias
def process_scene(scene, feedback):
    # Mostrar la barra de progreso
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Actualizar la barra de progreso
    for percent_complete in range(1, 101, 10):
        progress_bar.progress(percent_complete)
        status_text.text(f"Procesando... {percent_complete}%")
        time.sleep(0.05)  # Simular tiempo de procesamiento

    # Preparar la solicitud a la API de OpenRouter
    api_url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}",
    }
    
    # Crear el mensaje para la IA
    prompt = (
        "Toma el siguiente texto de una escena de una novela y aplica las siguientes críticas o sugerencias de mejora. "
        "Reescribe la escena incorporando dichas mejoras.\n\n"
        "Texto de la escena:\n"
        f"{scene}\n\n"
        "Críticas/Sugerencias:\n"
        f"{feedback}"
    )
    
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
        # Enviar la solicitud a la API
        response = requests.post(api_url, headers=headers, data=json.dumps(data))
        response.raise_for_status()  # Verificar si hubo un error en la solicitud
        
        # Parsear la respuesta
        result = response.json()
        regenerated_scene = result['choices'][0]['message']['content'].strip()
        
        # Actualizar la barra de progreso a 100%
        progress_bar.progress(100)
        status_text.text("¡Procesamiento completado!")
        
        return regenerated_scene
    except requests.exceptions.RequestException as e:
        # Manejar errores de la solicitud
        st.error(f"Ocurrió un error al procesar la solicitud: {e}")
        progress_bar.empty()
        status_text.empty()
        return None
    except KeyError:
        # Manejar errores en el parseo de la respuesta
        st.error("Respuesta inesperada de la API.")
        progress_bar.empty()
        status_text.empty()
        return None

# Botón para aplicar las sugerencias
if st.button("Aplicar Críticas y Sugerencias"):
    if not scene_text.strip():
        st.warning("Por favor, pega el texto de la escena.")
    elif not feedback_text.strip():
        st.warning("Por favor, pega tus críticas o sugerencias de mejora.")
    else:
        with st.spinner("Aplicando críticas y regenerando la escena..."):
            updated_scene = process_scene(scene_text, feedback_text)
            if updated_scene:
                st.subheader("Escena Regenerada:")
                st.text_area(
                    "Aquí está la escena con las mejoras aplicadas:",
                    value=updated_scene,
                    height=300
                )

# Opcional: Mostrar información sobre la API utilizada
st.markdown("""
---
Desarrollado utilizando la [API de OpenRouter](https://openrouter.ai/).
""")
