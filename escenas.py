# Configuración inicial de Streamlit
import streamlit as st
import requests
from docx import Document
import time

# Clave API almacenada en los Secrets de Streamlit
api_key = st.secrets["OPENROUTER_API_KEY"]

# Función para conectarse a la API de OpenRouter y generar texto
def generar_escena(capitulo, escena, tema, max_tokens=1000):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    prompt = f"Escribe la escena {escena + 1} del capítulo {capitulo + 1} de una novela sobre '{tema}'."
    data = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": max_tokens
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Verifica si la respuesta tiene un error
        resultado = response.json()
        texto = resultado["choices"][0]["message"]["content"]
        return texto
    except Exception as e:
        st.error(f"Error al generar la escena: {e}")
        return None

# Función principal para escribir la novela
def escribir_novela(tema):
    st.write("Iniciando la escritura de la novela...")
    texto_novela = ''
    documento = Document()
    documento.add_heading('Novela Generada', level=1)
    documento.add_paragraph(f"Tema: {tema}")
    
    progreso_total = 10 * 4  # 10 capítulos con 4 escenas cada uno
    progreso_actual = 0
    
    for capitulo in range(10):
        documento.add_heading(f"Capítulo {capitulo + 1}", level=2)
        st.subheader(f"Capítulo {capitulo + 1}")
        
        for escena in range(4):
            st.write(f"Generando escena {escena + 1} del capítulo {capitulo + 1}...")
            texto_escena = generar_escena(capitulo, escena, tema)
            
            if texto_escena:
                texto_novela += texto_escena + '\n'
                documento.add_paragraph(texto_escena)
                st.write(texto_escena)
            
            # Actualizar el progreso
            progreso_actual += 1
            st.progress(progreso_actual / progreso_total)
            time.sleep(1)  # Añade una pausa para simular el tiempo de procesamiento
    
    # Guardar el documento en un archivo Word
    nombre_archivo = "novela_generada.docx"
    documento.save(nombre_archivo)
    
    # Descargar el archivo Word
    with open(nombre_archivo, "rb") as file:
        st.download_button(
            label="Descargar novela completa en Word",
            data=file,
            file_name=nombre_archivo,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

# Configuración de la interfaz de Streamlit
st.title('Generador de Novelas con IA')
tema = st.text_input("Introduce el tema de la novela:")
st.write("Presiona el botón para generar una novela de cuarenta mil palabras en 10 capítulos con 4 escenas cada uno.")

if st.button('Iniciar Escritura') and tema:
    escribir_novela(tema)
elif not tema:
    st.warning("Por favor, introduce un tema para la novela.")
