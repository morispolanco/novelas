import streamlit as st
import requests
import json

st.title("Generador de Novelas de Suspenso Político")

# Obtener el tema proporcionado por el usuario
tema = st.text_input("Introduce el tema de tu novela:")

if tema:
    # Configurar los encabezados y datos para la solicitud API
    headers = {
        "Authorization": f"Bearer {st.secrets['TOGETHER_API_KEY']}",
        "Content-Type": "application/json"
    }

    # Función para llamar a la API de Together
    def call_together_api(prompt):
        data = {
            "model": "Qwen/Qwen2.5-7B-Instruct-Turbo",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2512,
            "temperature": 0.7,
            "top_p": 0.7,
            "top_k": 50,
            "repetition_penalty": 1,
            "stop": ["<|eot_id|>"],
            "stream": False
        }
        response = requests.post(
            "https://api.together.xyz/v1/chat/completions",
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
    """
    detalles = call_together_api(prompt_detalles)
    st.markdown(detalles)

    # Almacenar escenas previas para revisión
    escenas_previas = []

    # Generar novela capítulo por capítulo, escena por escena
    for capitulo in range(1, 13):
        st.header(f"Capítulo {capitulo}")
        for escena in range(1, 4):
            st.subheader(f"Escena {escena}")
            # Repasar lo ya escrito
            resumen_previas = " ".join(escenas_previas)
            prompt_escena = f"""
            Continúa la novela de suspenso político titulada '{tema}'. Hasta ahora, hemos escrito lo siguiente:

            {resumen_previas}

            Ahora, escribe la siguiente escena (Capítulo {capitulo}, Escena {escena}). Asegúrate de:

            - Mantener coherencia y consistencia con las escenas anteriores.
            - Desarrollar bien los personajes y sus motivaciones.
            - Evitar clichés y frases hechas.
            - Incluir giros y dilemas éticos que el protagonista enfrenta.
            - Seguir el tono tenso y emocionante con giros inesperados.

            La escena debe tener entre 150 y 300 palabras.
            """
            escena_actual = call_together_api(prompt_escena)
            st.write(escena_actual)

            # Agregar la escena actual a la lista de escenas previas
            escenas_previas.append(escena_actual)

            # Botón para continuar a la siguiente escena
            continuar = st.button("Continuar a la siguiente escena", key=f"{capitulo}-{escena}")
            if not continuar:
                st.stop()

    st.success("¡Novela completada!")

    # Funcionalidad para subir una novela y revisarla
    st.header("Revisión de una novela existente")
    novela_subida = st.file_uploader("Sube tu novela en formato TXT para revisarla:")
    if novela_subida:
        contenido_novela = novela_subida.read().decode('utf-8')
        st.text_area("Contenido de la novela:", value=contenido_novela, height=300)

        # Dividir la novela en escenas para revisión
        escenas_novela = contenido_novela.split("Escena")
        for idx, escena in enumerate(escenas_novela[1:], start=1):
            st.subheader(f"Revisión de Escena {idx}")
            prompt_revision = f"""
            Revisa la siguiente escena:

            {escena}

            Busca y señala:

            - Incoherencias e inconsistencias con escenas anteriores.
            - Mal desarrollo de los personajes.
            - Problemas de ritmo y trama.
            - Uso de clichés o frases hechas.

            Proporciona sugerencias para mejorar la escena.
            """
            revision = call_together_api(prompt_revision)
            st.write(revision)

            # Botón para regenerar la escena
            regenerar = st.button("Regenerar esta escena", key=f"regenerar-{idx}")
            if regenerar:
                prompt_regenerar = f"""
                Basándote en las sugerencias anteriores, reescribe la escena {idx} mejorando los aspectos mencionados. Asegúrate de mantener coherencia con el resto de la novela.
                """
                nueva_escena = call_together_api(prompt_regenerar)
                st.write(nueva_escena)

