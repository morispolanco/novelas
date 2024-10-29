# Configuración inicial de Streamlit
import streamlit as st
import requests
import time

# Clave API almacenada en los Secrets de Streamlit
api_key = st.secrets["OPEN_ROUTER_API_KEY"]

# Función para conectarse a la API de OpenRouter y generar texto
def generar_escena(capitulo, escena, max_tokens=1000):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    prompt = f"Escribe la escena {escena + 1} del capítulo {capitulo + 1} de una novela de ficción."
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
def escribir_novela():
    st.write("Iniciando la escritura de la novela...")
    texto_novela = ''
    
    progreso_total = 10 * 4  # 10 capítulos con 4 escenas cada uno
    progreso_actual = 0
    
    for capitulo in range(10):
        st.subheader(f"Capítulo {capitulo + 1}")
        for escena in range(4):
            st.write(f"Generando escena {escena + 1} del capítulo {capitulo + 1}...")
            
            texto_escena = generar_escena(capitulo, escena)
            if texto_escena:
                texto_novela += texto_escena + '\n'
                st.write(texto_escena)
            
            # Actualizar el progreso
            progreso_actual += 1
            st.progress(progreso_actual / progreso_total)
            time.sleep(1)  # Añade una pausa para simular el tiempo de procesamiento
            
    # Mostrar el texto completo de la novela
    st.success("Novela completada.")
    st.write(texto_novela)
    
    # Opción para descargar la novela como archivo de texto
    st.download_button(
        label="Descargar novela completa",
        data=texto_novela,
        file_name="novela_generada.txt",
        mime="text/plain"
    )

# Configuración de la interfaz de Streamlit
st.title('Generador de Novelas con IA')
st.write("Presiona el botón para generar una novela de cuarenta mil palabras en 10 capítulos con 4 escenas cada uno.")

if st.button('Iniciar Escritura'):
    escribir_novela()
