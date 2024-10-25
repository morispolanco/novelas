# Añade estas constantes al inicio del archivo
INICIOS_ESCENA = [
    "La escena comienza con",
    "En esta parte de la historia,",
    "De repente,",
    "Mientras tanto,",
    "En un giro inesperado,",
    "El ambiente se tensa cuando",
    "Con determinación,",
    "Sorprendentemente,",
    "En medio del caos,",
    "Silenciosamente,"
]

# Modifica la clase NovelUI para incluir estas funciones adicionales:
class NovelUI:
    # ... (código anterior se mantiene igual)

    def generar_estructura_inicial(self, tema: str, instrucciones: str) -> str:
        prompt = f"""
        Genera una estructura detallada para una novela de thriller político basada en el siguiente tema:
        {tema}

        Instrucciones adicionales:
        {instrucciones}

        La estructura debe incluir:
        1. Resumen general de la trama
        2. Lista de personajes principales con sus características y motivaciones
        3. Desarrollo de la historia por capítulos
        4. Puntos de giro principales
        5. Resolución final

        Formato de salida:
        TRAMA GENERAL:
        [Resumen de la trama]

        PERSONAJES PRINCIPALES:
        - [Nombre]: [Descripción y motivaciones]

        ESTRUCTURA DE CAPÍTULOS:
        Capítulo 1: [Título]
        - Escena 1: [Descripción breve]
        - Escena 2: [Descripción breve]
        [etc.]

        RESOLUCIÓN:
        [Descripción del final]
        """
        
        return self.api_handler.generar_contenido(
            prompt,
            max_tokens=3000,
            temperature=0.7
        )

    def generar_escena(self, capitulo: int, escena: int, contexto: str) -> str:
        inicio = random.choice(INICIOS_ESCENA)
        prompt = f"""
        Basándote en el siguiente contexto de la historia:
        {contexto}

        Genera la escena {escena} del capítulo {capitulo}.
        {inicio}

        La escena debe:
        - Ser detallada y envolvente
        - Incluir diálogo cuando sea apropiado
        - Mantener la coherencia con la trama general
        - Contribuir al desarrollo de la historia
        - Tener aproximadamente 500-800 palabras

        Usa un estilo narrativo profesional y mantén el tono de thriller político.
        """

        return self.api_handler.generar_contenido(
            prompt,
            max_tokens=1500,
            temperature=0.8
        )

    def generar_novela(self, tema: str, instrucciones: str, num_capitulos: int, 
                      num_escenas: int, max_tokens: int, temperature: float):
        try:
            # Paso 1: Generar estructura inicial
            with st.spinner("Generando estructura de la novela..."):
                estructura = self.generar_estructura_inicial(tema, instrucciones)
                if not estructura:
                    return False, "Error al generar la estructura inicial"
                
                self.state.actualizar_estado(
                    contenido_inicial=estructura,
                    tema=tema,
                    instrucciones_adicionales=instrucciones
                )

            # Paso 2: Generar el contenido completo
            contenido_final = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for capitulo in range(1, num_capitulos + 1):
                contenido_final.append(f"\nCapítulo {capitulo}\n")
                
                for escena in range(1, num_escenas + 1):
                    status_text.text(f"Generando Capítulo {capitulo}, Escena {escena}...")
                    
                    # Generar escena individual
                    contenido_escena = self.generar_escena(
                        capitulo,
                        escena,
                        estructura  # Pasamos la estructura como contexto
                    )
                    
                    if contenido_escena:
                        contenido_final.append(contenido_escena + "\n")
                    else:
                        return False, f"Error al generar escena {escena} del capítulo {capitulo}"
                    
                    # Actualizar progreso
                    progress = (((capitulo - 1) * num_escenas + escena) / 
                              (num_capitulos * num_escenas))
                    progress_bar.progress(progress)

            # Unir todo el contenido
            novela_completa = "\n".join(contenido_final)
            
            # Actualizar estado
            self.state.actualizar_estado(
                contenido_final=novela_completa,
                novela_generada=True
            )
            
            return True, novela_completa
            
        except Exception as e:
            logging.error(f"Error en la generación de la novela: {str(e)}")
            return False, str(e)

# Modifica la función main para mostrar el contenido generado:
def main():
    # ... (código anterior se mantiene igual hasta el if st.button("Generar Novela"))

    if st.button("Generar Novela"):
        valido, mensaje = ui.validar_entrada(tema, instrucciones)
        if valido:
            with st.spinner("Generando tu novela..."):
                exito, resultado = ui.generar_novela(
                    tema, instrucciones, num_capitulos, num_escenas,
                    max_tokens, temperature
                )
                if exito:
                    st.success("¡Novela generada exitosamente!")
                    
                    # Mostrar el contenido generado
                    with st.expander("Ver contenido de la novela", expanded=True):
                        st.write(resultado)
                    
                    # Opciones de exportación
                    buffer = NovelExporter.exportar_a_docx(resultado)
                    if buffer:
                        st.download_button(
                            label="Descargar como DOCX",
                            data=buffer,
                            file_name="novela.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                else:
                    st.error(f"Error: {resultado}")
        else:
            st.error(mensaje)

if __name__ == "__main__":
    main()
