import streamlit as st
import requests
from io import BytesIO
import re
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import random
import json
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Constantes
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

# Configuración inicial
@dataclass
class AppConfig:
    OPENROUTER_API_KEY: str
    API_URL: str = "https://openrouter.ai/api/v1/chat/completions"
    MODEL: str = "openai/gpt-4-mini"
    DEFAULT_MAX_TOKENS: int = 3000
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_REPETITION_PENALTY: float = 1.2
    DEFAULT_FREQUENCY_PENALTY: float = 0.5

class NovelState:
    def __init__(self):
        if 'novela' not in st.session_state:
            st.session_state.novela = {
                'personajes': [],
                'eventos': [],
                'trama_general': "",
                'resumen_capitulos': [],
                'contenido_inicial': "",
                'contenido_final': "",
                'aprobado': False,
                'novela_generada': False,
                'tema': "",
                'instrucciones_adicionales': ""
            }

    @property
    def estado_actual(self) -> dict:
        return st.session_state.novela

    def actualizar_estado(self, **kwargs):
        for key, value in kwargs.items():
            st.session_state.novela[key] = value

    def reiniciar_estado(self):
        st.session_state.novela = {
            'personajes': [],
            'eventos': [],
            'trama_general': "",
            'resumen_capitulos': [],
            'contenido_inicial': "",
            'contenido_final': "",
            'aprobado': False,
            'novela_generada': False,
            'tema': "",
            'instrucciones_adicionales': ""
        }

class APIHandler:
    def __init__(self, config: AppConfig):
        self.config = config
        self.session = self._create_session()

    def _create_session(self):
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        return session

    def generar_contenido(self, prompt: str, max_tokens: int = None, 
                         temperature: float = None, 
                         repetition_penalty: float = None,
                         frequency_penalty: float = None) -> Optional[str]:
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.OPENROUTER_API_KEY}"
            }
            
            data = {
                "model": self.config.MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens or self.config.DEFAULT_MAX_TOKENS,
                "temperature": temperature or self.config.DEFAULT_TEMPERATURE,
                "repetition_penalty": repetition_penalty or self.config.DEFAULT_REPETITION_PENALTY,
                "frequency_penalty": frequency_penalty or self.config.DEFAULT_FREQUENCY_PENALTY
            }

            response = self.session.post(
                self.config.API_URL,
                headers=headers,
                json=data,
                timeout=120
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

        except Exception as e:
            logging.error(f"Error en la generación de contenido: {str(e)}")
            st.error(f"Error al generar contenido: {str(e)}")
            return None

class NovelExporter:
    @staticmethod
    def exportar_a_docx(contenido: str) -> Optional[BytesIO]:
        try:
            doc = Document()
            # Configuración del documento
            for section in doc.sections:
                section.page_width = Inches(6)
                section.page_height = Inches(9)
                section.top_margin = Inches(0.7)
                section.bottom_margin = Inches(0.5)
                section.left_margin = Inches(0.7)
                section.right_margin = Inches(0.5)

            # Configuración de estilos
            style_normal = doc.styles['Normal']
            font_normal = style_normal.font
            font_normal.name = 'Times New Roman'
            font_normal.size = Pt(12)

            # Procesar contenido
            for linea in contenido.split('\n'):
                if linea.strip():
                    if linea.startswith("Capítulo"):
                        p = doc.add_heading(linea, level=2)
                    else:
                        p = doc.add_paragraph(linea)
                    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            return buffer

        except Exception as e:
            logging.error(f"Error al exportar a DOCX: {str(e)}")
            return None
class NovelUI:
    def __init__(self, state: NovelState, api_handler: APIHandler):
        self.state = state
        self.api_handler = api_handler

    def mostrar_configuracion(self):
        st.sidebar.title("Configuración")
        num_capitulos = st.sidebar.slider(
            "Número de Capítulos",
            min_value=5,
            max_value=20,
            value=12
        )
        num_escenas = st.sidebar.slider(
            "Escenas por Capítulo",
            min_value=3,
            max_value=10,
            value=5
        )
        
        if st.sidebar.checkbox("Mostrar configuración avanzada"):
            max_tokens = st.sidebar.number_input(
                "Máximo de tokens",
                min_value=500,
                max_value=4000,
                value=3000
            )
            temperature = st.sidebar.slider(
                "Temperatura",
                min_value=0.0,
                max_value=1.0,
                value=0.7
            )
        else:
            max_tokens = 3000
            temperature = 0.7
            
        return num_capitulos, num_escenas, max_tokens, temperature

    def mostrar_entrada(self):
        st.title("Generador de Novelas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Paso 1: Tema Principal")
            tema = st.text_input(
                "Tema de la novela:",
                help="Introduce el tema principal de tu novela"
            )

        with col2:
            st.subheader("Paso 2: Instrucciones Adicionales")
            instrucciones = st.text_area(
                "Instrucciones específicas (opcional):",
                help="Añade instrucciones específicas para la generación de tu novela.",
                height=100
            )

        with st.expander("Ver ejemplos de instrucciones"):
            st.markdown("""
            **Ejemplos de instrucciones útiles:**
            
            1. **Estilo narrativo:**
               - "Usar un estilo descriptivo y detallado"
               - "Mantener un tono sobrio y formal"
               - "Incluir diálogos frecuentes y dinámicos"
            
            2. **Elementos específicos:**
               - "Incorporar elementos de misterio en cada capítulo"
               - "Mantener un ritmo rápido en las escenas de acción"
               - "Desarrollar subtramas románticas sutiles"
            
            3. **Restricciones:**
               - "Evitar descripciones violentas explícitas"
               - "Mantener el lenguaje apropiado para todos los públicos"
               - "No incluir elementos sobrenaturales"
            
            4. **Desarrollo de personajes:**
               - "Enfocarse en el desarrollo psicológico de los personajes"
               - "Incluir flashbacks para revelar el pasado de los personajes"
               - "Mostrar conflictos internos en los personajes principales"
            """)

        return tema, instrucciones

    def validar_entrada(self, tema: str, instrucciones: str) -> Tuple[bool, str]:
        if not tema:
            return False, "El tema no puede estar vacío."
        if len(tema) < 5:
            return False, "El tema es demasiado corto."
        if len(tema) > 250:
            return False, "El tema es demasiado largo."
        
        if len(instrucciones) > 1000:
            return False, "Las instrucciones son demasiado largas."
        
        palabras_prohibidas = ["explicito", "violento", "gore", "nsfw"]
        for palabra in palabras_prohibidas:
            if palabra in instrucciones.lower():
                return False, f"Las instrucciones contienen contenido no permitido: '{palabra}'"
        
        return True, ""

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
                    
                    contenido_escena = self.generar_escena(
                        capitulo,
                        escena,
                        estructura
                    )
                    
                    if contenido_escena:
                        contenido_final.append(contenido_escena + "\n")
                    else:
                        return False, f"Error al generar escena {escena} del capítulo {capitulo}"
                    
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

def main():
    config = AppConfig(
        OPENROUTER_API_KEY=st.secrets["OPENROUTER_API_KEY"]
    )
    
    state = NovelState()
    api_handler = APIHandler(config)
    ui = NovelUI(state, api_handler)
    
    num_capitulos, num_escenas, max_tokens, temperature = ui.mostrar_configuracion()
    tema, instrucciones = ui.mostrar_entrada()
    
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
                    
                    with st.expander("Ver contenido de la novela", expanded=True):
                        st.write(resultado)
                    
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
