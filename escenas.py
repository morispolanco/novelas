# Configuración inicial de Streamlit
import streamlit as st
import requests
from docx import Document
import time

# Clave API almacenada en los Secrets de Streamlit
api_key = st.secrets["OPENROUTER_API_KEY"]

# Función para formatear el diálogo con raya
def formatear_dialogo(texto):
    lineas = texto.split('\n')
    texto_formateado = ""
    for linea in lineas:
        if linea.strip().startswith('"'):
            linea = '—' + linea[1:]  # Reemplaza comillas iniciales por raya
        texto_formateado += linea + '\n'
    return texto_formateado

# Función para conectarse a la API de OpenRouter y generar texto
def generar_escena(capitulo, escena, tema, max_tokens=1500):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    prompt = f"Escribe la escena {escena + 1} del capítulo {capitulo + 1} de una novela sobre '{tema}', usando la raya (—) para todos los diálogos."
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
        response.raise_for_status()
        resultado = response.json()
        texto = resultado["choices"][0]["message"]["content"]
        texto = formatear_dialogo(texto)
        return texto
    except Exception as e:
        st.error(f"Error al generar la escena: {e}")
        return None

# Función principal para escribir la novela
def escribir_novela(tema):
    st.write("Iniciando la escritura de la novela...")
    titulo = f"Novela sobre {tema}"
    texto_novela = ''
    documento = Document()
    documento.add_heading(titulo, level=1)
    documento.add_paragraph(f"Tema: {tema}")
    
    progreso_total = 10 * 4  # 10 capítulos con 4 escenas cada uno
    progreso_actual = 0
    
    for capitulo in range(10):
        st.subheader(f"Capítulo {capitulo + 1}")  # Visualización en Streamlit
        documento.add_paragraph(f"Capítulo {capitulo + 1}", style='Heading 2')  # Número de capítulo en el documento
        
        for escena in range(4):
            st.write(f"Generando escena {escena + 1} del capítulo {capitulo + 1}...")
            texto_escena = generar_escena(capitulo, escena, tema)
            
            if texto_escena:
                texto_novela += texto_escena + '\n'
                documento.add_paragraph(f"Escena {escena + 1}", style='Heading 3')  # Número de escena en el documento
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
