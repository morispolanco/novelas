import streamlit as st
import requests
import time

# Configuración de la página
st.set_page_config(
    page_title="Regenerador de Novelas",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Regenerador de Novelas con OpenRouter AI")
st.write("""
    Sube tu novela, proporciona análisis y recomendaciones, y la aplicación regenerará tu novela capítulo por capítulo.
""")

# Función para dividir la novela en capítulos
def split_into_chapters(text):
    import re
    # Suponiendo que los capítulos están marcados con "Capítulo" o "Chapter"
    chapters = re.split(r'(Capítulo\s+\d+|Chapter\s+\d+)', text, flags=re.IGNORECASE)
    # Combinar los títulos de capítulos con su contenido
    combined = []
    for i in range(1, len(chapters), 2):
        title = chapters[i]
        content = chapters[i+1] if i+1 < len(chapters) else ""
        combined.append(f"{title}\n{content}")
    return combined

# Función para llamar a la API de OpenRouter
def call_openrouter_api(prompt):
    api_url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}",
    }
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    response = requests.post(api_url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        st.error(f"Error en la API: {response.status_code} - {response.text}")
        return None

# Interfaz de usuario
with st.form("regeneration_form"):
    uploaded_file = st.file_uploader("Sube tu novela (archivo .txt)", type=["txt"])
    analysis = st.text_area("Pega tus análisis y recomendaciones aquí")
    submit_button = st.form_submit_button(label="Regenerar Novela")

if submit_button:
    if uploaded_file is not None and analysis.strip() != "":
        # Leer el contenido del archivo
        novel_text = uploaded_file.read().decode('utf-8')
        chapters = split_into_chapters(novel_text)
        num_chapters = len(chapters)
        st.write(f"Se han detectado {num_chapters} capítulos.")

        # Barra de progreso
        progress_bar = st.progress(0)
        progress_text = st.empty()

        regenerated_chapters = []
        for idx, chapter in enumerate(chapters, 1):
            progress_text.text(f"Regenerando capítulo {idx} de {num_chapters}...")
            prompt = f"""
                Aquí está el capítulo {idx} de mi novela:

                {chapter}

                Basándote en el siguiente análisis y recomendaciones, regenera este capítulo mejorándolo:

                {analysis}
            """
            regenerated = call_openrouter_api(prompt)
            if regenerated:
                regenerated_chapters.append(regenerated)
            else:
                st.error("Hubo un problema al regenerar el capítulo. El proceso se detendrá.")
                break
            # Actualizar la barra de progreso
            progress_bar.progress(idx / num_chapters)
            # Opcional: Esperar un poco para no sobrecargar la API
            time.sleep(1)

        if len(regenerated_chapters) == num_chapters:
            st.success("Novela regenerada con éxito.")
            regenerated_novel = "\n\n".join(regenerated_chapters)
            st.text_area("Novela Regenerada", regenerated_novel, height=400)
            
            # Proporcionar opción de descarga
            st.download_button(
                label="Descargar Novela Regenerada",
                data=regenerated_novel,
                file_name="novela_regenerada.txt",
                mime="text/plain"
            )
    else:
        st.error("Por favor, sube una novela y proporciona análisis y recomendaciones.")

