import streamlit as st
import requests
from docx import Document
from io import BytesIO

# Configuración de la API Key
OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Función para generar el contenido de cada escena
def generar_escena(tema, capitulo, escena):
    prompt = f"Una novela de suspenso político suele centrarse en conflictos de poder, conspiraciones gubernamentales, y temas de espionaje, aprovechando elementos de la política para crear una trama tensa y llena de intriga. Aquí tienes algunas características claves:\n\n\
1. **Contexto político realista y contemporáneo**: La historia se desarrolla en un escenario político reconocible, a menudo inspirado en situaciones de conflicto geopolítico, corrupción, o crisis gubernamentales. Esto agrega realismo y relevancia al suspenso, haciendo que los lectores se sientan inmersos en el trasfondo político.\n\
2. **Conspiraciones y secretos de estado**: Las novelas de suspenso político giran en torno a secretos ocultos por gobiernos, agencias de inteligencia, o figuras de poder. Las conspiraciones pueden involucrar desde operaciones encubiertas hasta traiciones de alto nivel, presentando una constante amenaza de revelación.\n\
3. **Personajes en posiciones de influencia**: Los personajes suelen ocupar roles importantes, como diplomáticos, agentes secretos, periodistas o políticos. La interacción entre ellos revela sus motivaciones complejas, dilemas morales, y lealtades divididas, lo que añade profundidad psicológica.\n\
4. **Amenazas a la seguridad y consecuencias globales**: Estas novelas suelen exponer amenazas graves, como el riesgo de guerra, terrorismo, o colapso económico. La tensión aumenta al saber que los errores de los personajes podrían tener consecuencias devastadoras para naciones enteras.\n\
5. **Trama compleja y ritmo acelerado**: Las novelas de suspenso político son conocidas por tener tramas enredadas y giros inesperados. El ritmo suele ser rápido, con capítulos cortos que cambian de perspectiva o saltan entre escenas de acción e investigación, manteniendo la tensión.\n\
6. **Ética y moralidad en conflicto**: Los personajes suelen enfrentarse a decisiones éticamente ambiguas que los ponen en conflicto entre el deber, la lealtad y la moralidad personal. Este dilema moral realza el suspenso y lleva a los lectores a cuestionarse qué harían en situaciones similares.\n\
7. **Diálogos y debates políticos**: El diálogo en estas novelas es fundamental y a menudo está cargado de lenguaje político y estratégico, lo cual ayuda a establecer la autenticidad del contexto. Las discusiones políticas y las reuniones de alto nivel pueden ser tan emocionantes como las escenas de acción.\n\
8. **Ambientación detallada**: Las descripciones de edificios gubernamentales, oficinas de inteligencia, y lugares de reunión secretos son típicas y dan un tono sombrío o serio a la atmósfera. El detalle en la ambientación ayuda a crear un sentido de verosimilitud.\n\
9. **Final impactante y revelador**: Las novelas de suspenso político tienden a tener finales que revelan secretos que cambian la comprensión de la historia, ya sea exponiendo la verdadera lealtad de los personajes o revelando la magnitud de la conspiración.\n\n\
Escribe una escena para una novela de suspenso político sobre el tema '{tema}'. Capítulo {capitulo}, Escena {escena}. Incluye descripciones detalladas, diálogos con raya en cada intervención de los personajes, y desarrolla las motivaciones de los personajes. Mantén un ritmo trepidante y evita colocar nombres a los capítulos o escenas."

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}"
    }
    data = {
        "model": "openai/gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }

    response = requests.post(API_URL, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        st.error("Error al generar la escena. Por favor, intenta de nuevo.")
        return None

# Función para generar toda la novela con barra de progreso
def generar_novela(tema):
    document = Document()
    progreso_total = 10 * 4  # 10 capítulos, 4 escenas por capítulo
    progreso_actual = 0

    # Agregar barra de progreso en Streamlit
    barra_progreso = st.progress(0)
    for capitulo in range(1, 11):
        document.add_paragraph(f"Capítulo {capitulo}", style="Heading 1")
        for escena in range(1, 5):
            escena_texto = generar_escena(tema, capitulo, escena)
            if escena_texto:
                document.add_paragraph(escena_texto)
                progreso_actual += 1
                barra_progreso.progress(progreso_actual / progreso_total)
            else:
                st.error(f"No se pudo generar la Escena {escena} del Capítulo {capitulo}.")
                break

    # Guardar el documento en un archivo Word
    buffer = BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer

# Interfaz de la aplicación
st.title("Generador de Novelas de Suspenso Político en Streamlit")
st.write("Introduce el tema de la novela para generar una historia de suspenso político dividida en diez capítulos y exportar el resultado en un archivo Word.")

# Entrada del usuario para el tema de la novela
tema = st.text_input("Tema de la novela", help="Introduce el tema principal para la novela.")

# Botón para iniciar la generación de la novela
if st.button("Generar Novela"):
    if tema:
        st.info("Generando novela... puede tardar unos minutos.")
        buffer = generar_novela(tema)
        st.success("¡Novela generada exitosamente!")
        st.download_button(
            label="Descargar Novela en Word",
            data=buffer,
            file_name="novela_generada.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    else:
        st.warning("Por favor, introduce un tema para la novela.")
