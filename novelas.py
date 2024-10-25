import streamlit as st
import requests
import json
from docx import Document
from docx.shared import Pt
import base64

st.title("Generador de Novelas de Suspenso Político")

# Obtener el tema proporcionado por el usuario
tema = st.text_input("Introduce el tema de tu novela:")

if tema:
    # Configurar los encabezados y datos para la solicitud API
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}",
        "HTTP-Referer": "tu_app_nombre",  # Reemplaza "tu_app_nombre" con el nombre de tu aplicación
        "X-Title": "tu_app_titulo"        # Reemplaza "tu_app_titulo" con el título de tu aplicación
    }

    # Función para llamar a la API de OpenRouter
    def call_openrouter_api(prompt, max_tokens=4000):
        data = {
            "model": "openai/gpt-4",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.8,  # Aumentar ligeramente para mayor diversidad
            "top_p": 0.9         # Aumentar para permitir más opciones de palabras
            # Nota: Algunos parámetros como "repetition_penalty" pueden no ser compatibles
        }
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(data)
        )
        result = response.json()
        return result['choices'][0]['message']['content']

    # Generar título, trama, personajes, ambientación y técnica literaria
    st.header("Generando detalles de la novela...")
    prompt_detalles = f"""
Basado en el tema: {tema}, genera el título, trama, personajes principales, ambientación y técnica literaria para una novela de suspenso político. Asegúrate de seguir estas instrucciones:

# Detalles

- Protagonista: Debe ser alguien inesperado, como un periodista o un funcionario subalterno, que descubre una trama mayor.
- Antagonista: Un alto funcionario del gobierno con motivaciones ocultas.
- Ambiente: Entornos políticos, reuniones secretas y locaciones internacionales.
- Tema: Corrupción, traición y la búsqueda de la verdad.
- Tono: Tenso y emocionante con giros inesperados.

Proporciona la información en formato estructurado.

**Importante:**

- Utiliza la raya (—) para indicar los diálogos entre personajes.
- Evita repeticiones y redundancias en el texto.
"""
    detalles = call_openrouter_api(prompt_detalles)
    st.markdown(detalles)

    # Almacenar escenas previas para revisión y exportación
    escenas_previas = []

    # Generar novela capítulo por capítulo, escena por escena automáticamente
    st.header("Generando novela...")
    progress_text = "Generando escenas. Por favor espera..."
    my_bar = st.progress(0, text=progress_text)
    total_escenas = 12 * 3
    escena_actual_num = 0

    for capitulo in range(1, 13):
        st.header(f"Capítulo {capitulo}")
        for escena in range(1, 4):
            escena_actual_num += 1
            # Actualizar barra de progreso
            my_bar.progress(escena_actual_num / total_escenas, text=progress_text)
            st.subheader(f"Escena {escena}")
            # Repasar lo ya escrito
            resumen_previas = " ".join(escenas_previas)
            prompt_escena = f"""
Continúa la novela de suspenso político titulada '{tema}'. Hasta ahora, hemos escrito lo siguiente:

{resumen_previas}

Ahora, escribe la siguiente escena (Capítulo {capitulo}, Escena {escena}). Asegúrate de:

- Mantener coherencia y consistencia con las escenas anteriores.
- Desarrollar bien los personajes y sus motivaciones.
- Evitar clichés, repeticiones y frases hechas.
- **Utilizar la raya (—) en los diálogos.**
- Cada escena debe tener al menos 1000 palabras.
- Incluir giros y dilemas éticos que el protagonista enfrenta.
- Seguir el tono tenso y emocionante con giros inesperados.
- Utilizar un lenguaje variado y evitar redundancias.

La escena debe ser narrativa y descriptiva, enfocándose en avanzar la trama y profundizar en los personajes.
"""
            escena_actual = call_openrouter_api(prompt_escena, max_tokens=4000)
            st.write(escena_actual)

            # Agregar la escena actual a la lista de escenas previas
            escenas_previas.append(f"Capítulo {capitulo}, Escena {escena}\n{escena_actual}\n")

    st.success("¡Novela completada!")

    # Funcionalidad para exportar la novela a un archivo DOCX
    st.header("Exportar novela a DOCX")

    exportar = st.button("Exportar novela")
    if exportar:
        # Crear un nuevo documento de Word
        documento = Document()

        # Establecer el estilo de la fuente
        estilo = documento.styles['Normal']
        fuente = estilo.font
        fuente.name = 'Times New Roman'
        fuente.size = Pt(12)

        # Agregar título y detalles de la novela
        documento.add_heading("Título de la novela", level=0)
        documento.add_paragraph(detalles)

        # Agregar las escenas al documento
        for escena in escenas_previas:
            documento.add_paragraph(escena)

        # Guardar el documento en un buffer en memoria
        from io import BytesIO
        buffer = BytesIO()
        documento.save(buffer)
        buffer.seek(0)

        # Codificar el buffer para descargar
        b64 = base64.b64encode(buffer.read()).decode()
        href = f'<a href="data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,{b64}" download="novela.docx">Haz clic aquí para descargar tu novela</a>'
        st.markdown(href, unsafe_allow_html=True)

    # Funcionalidad para subir una novela y revisarla
    st.header("Revisión de una novela existente")
    novela_subida = st.file_uploader("Sube tu novela en formato TXT para revisarla:")
    if novela_subida:
        contenido_novela = novela_subida.read().decode('utf-8')
        st.text_area("Contenido de la novela:", value=contenido_novela, height=300)

        # Dividir la novela en escenas para revisión
        escenas_novela = contenido_novela.split("Escena")
        escenas_novela = ["Escena" + escena for escena in escenas_novela if escena.strip() != ""]

        escenas_previas = []
        for idx, escena in enumerate(escenas_novela, start=1):
            st.subheader(f"Revisión de Escena {idx}")
            resumen_previas = " ".join(escenas_previas)
            prompt_revision = f"""
Revisa la siguiente escena en el contexto de las escenas anteriores:

Escenas anteriores:
{resumen_previas}

Escena actual:
{escena}

Busca y señala:

- Incoherencias e inconsistencias con escenas anteriores.
- Mal desarrollo de los personajes y sus motivaciones.
- Problemas de ritmo y trama.
- Uso de clichés, repeticiones o frases hechas.
- **Verifica que los diálogos usen la raya (—) correctamente.**
- Asegúrate de que la escena tenga al menos 1000 palabras.

Proporciona sugerencias detalladas para mejorar la escena.
"""
            revision = call_openrouter_api(prompt_revision, max_tokens=1500)
            st.write(revision)

            # Agregar la escena actual a las escenas previas
            escenas_previas.append(escena)

            # Botón para regenerar la escena
            regenerar = st.button("Regenerar esta escena", key=f"regenerar-{idx}")
            if regenerar:
                prompt_regenerar = f"""
Basándote en las sugerencias anteriores, reescribe la escena {idx} mejorando los aspectos mencionados. Asegúrate de:

- Mantener coherencia con las escenas anteriores.
- Desarrollar bien los personajes y sus motivaciones.
- Evitar clichés, repeticiones y frases hechas.
- **Utilizar la raya (—) en los diálogos.**
- La escena debe tener al menos 1000 palabras.
- Mantener un tono tenso y emocionante con giros inesperados.

La escena reescrita es:
"""
                nueva_escena = call_openrouter_api(prompt_regenerar, max_tokens=4000)
                st.write(nueva_escena)

                # Actualizar la escena en la lista de escenas previas
                escenas_previas[-1] = nueva_escena

        # Botón para exportar la novela revisada
        exportar_revisada = st.button("Exportar novela revisada")
        if exportar_revisada:
            # Crear un nuevo documento de Word
            documento = Document()

            # Establecer el estilo de la fuente
            estilo = documento.styles['Normal']
            fuente = estilo.font
            fuente.name = 'Times New Roman'
            fuente.size = Pt(12)

            # Agregar las escenas revisadas al documento
            for escena in escenas_previas:
                documento.add_paragraph(escena)

            # Guardar el documento en un buffer en memoria
            buffer = BytesIO()
            documento.save(buffer)
            buffer.seek(0)

            # Codificar el buffer para descargar
            b64 = base64.b64encode(buffer.read()).decode()
            href = f'<a href="data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,{b64}" download="novela_revisada.docx">Haz clic aquí para descargar tu novela revisada</a>'
            st.markdown(href, unsafe_allow_html=True)
