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
    DEFAULT_MAX_TOKENS: int = 4000
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_REPETITION_PENALTY: float = 1.2
    DEFAULT_FREQUENCY_PENALTY: float = 0.5

class NovelProposal:
    def __init__(self):
        self.titulo = ""
        self.trama = ""
        self.personajes = []
        self.ambientacion = ""
        self.tecnica_literaria = ""
        self.aprobada = False

    def to_dict(self):
        return {
            "título": self.titulo,
            "trama": self.trama,
            "personajes": self.personajes,
            "ambientación": self.ambientacion,
            "técnica_literaria": self.tecnica_literaria
        }

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
                'instrucciones_adicionales': "",
                'propuesta': None,
                'propuesta_aprobada': False
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
            'instrucciones_adicionales': "",
            'propuesta': None,
            'propuesta_aprobada': False
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

    def _configuracion(self):
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
        
        if st.sidebar.checkbox(" configuración avanzada"):
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

    def generar_propuesta(self, tema: str, instrucciones: str) -> Optional[NovelProposal]:
        prompt = f"""
        Basándote en el siguiente tema e instrucciones, genera una propuesta detallada para una novela:

        TEMA:
        {tema}

        INSTRUCCIONES ESPECÍFICAS:
        {instrucciones}

        La propuesta debe incluir:

        1. TÍTULO:
        Un título atractivo y relevante para la novela.

        2. TRAMA PRINCIPAL:
        Un resumen conciso pero completo de la historia principal (250-300 palabras).

        3. PERSONAJES PRINCIPALES (3-5 personajes):
        - Nombre completo y rol en la historia
        - Descripción física y psicológica detallada
        - Motivaciones y conflictos internos
        - Arco de desarrollo previsto
        - Relaciones con otros personajes

        4. AMBIENTACIÓN:
        - Época y lugar específicos
        - Contexto social, político y cultural
        - Descripción del ambiente y atmósfera
        - Elementos distintivos del escenario
        - Detalles relevantes del mundo de la historia

        5. TÉCNICA LITERARIA:
        - Estilo narrativo principal
        - Punto de vista y voz narrativa
        - Recursos literarios a utilizar
        - Estructura narrativa planificada
        - Manejo del tiempo y ritmo narrativo

        Formatea la respuesta de manera clara y organizada.
        """

        respuesta = self.api_handler.generar_contenido(
            prompt,
            max_tokens=3000,
            temperature=0.7
        )

        if respuesta:
            try:
                propuesta = NovelProposal()
                
                # Extraer secciones
                secciones = re.split(r'\n(?=TÍTULO:|TRAMA PRINCIPAL:|PERSONAJES PRINCIPALES:|AMBIENTACIÓN:|TÉCNICA LITERARIA:)', respuesta)
                
                for seccion in secciones:
                    if seccion.startswith('TÍTULO:'):
                        propuesta.titulo = seccion.replace('TÍTULO:', '').strip()
                    elif seccion.startswith('TRAMA PRINCIPAL:'):
                        propuesta.trama = seccion.replace('TRAMA PRINCIPAL:', '').strip()
                    elif seccion.startswith('PERSONAJES PRINCIPALES:'):
                        propuesta.personajes = [p.strip() for p in seccion.replace('PERSONAJES PRINCIPALES:', '').strip().split('\n') if p.strip()]
                    elif seccion.startswith('AMBIENTACIÓN:'):
                        propuesta.ambientacion = seccion.replace('AMBIENTACIÓN:', '').strip()
                    elif seccion.startswith('TÉCNICA LITERARIA:'):
                        propuesta.tecnica_literaria = seccion.replace('TÉCNICA LITERARIA:', '').strip()

                return propuesta
            except Exception as e:
                logging.error(f"Error al procesar la propuesta: {str(e)}")
                return None
        return None

        class NovelUI:
        # ... (otros métodos permanecen igual)
    
            def mostrar_propuesta(self, propuesta: NovelProposal):
                st.header("📚 Propuesta de Novela")
                
                # Título
                st.markdown(f"## {propuesta.titulo}")
                
                # Trama
                st.markdown("### 📖 Trama Principal")
                st.write(propuesta.trama)
                
                # Personajes
                st.markdown("### 👥 Personajes Principales")
                for personaje in propuesta.personajes:
                    st.markdown(f"- {personaje}")
                
                # Ambientación
                st.markdown("### 🌍 Ambientación")
                st.write(propuesta.ambientacion)
                
                # Técnica Literaria
                st.markdown("### ✍️ Técnica Literaria")
                st.write(propuesta.tecnica_literaria)
        
                # Botones de acción con claves únicas
                col1, col2 = st.columns(2)
                with col1:
                    aprobar = st.button(
                        "✅ Aprobar y Continuar",
                        key="btn_aprobar_propuesta"
                    )
                    if aprobar:
                        self.state.actualizar_estado(propuesta_aprobada=True)
                        return True
                with col2:
                    nueva = st.button(
                        "🔄 Generar Nueva Propuesta",
                        key="btn_nueva_propuesta"
                    )
                    if nueva:
                        self.state.actualizar_estado(propuesta=None)
                        return False
                
                return None
        
        def main():
            config = AppConfig(
                OPENROUTER_API_KEY=st.secrets["OPENROUTER_API_KEY"]
            )
            
            state = NovelState()
            api_handler = APIHandler(config)
            ui = NovelUI(state, api_handler)
            
            num_capitulos, num_escenas, max_tokens, temperature = ui.mostrar_configuracion()
            tema, instrucciones = ui.mostrar_entrada()
            
            # Botón para generar propuesta con clave única
            if st.button("Generar Propuesta", key="btn_generar_propuesta") and not state.estado_actual['propuesta_aprobada']:
                valido, mensaje = ui.validar_entrada(tema, instrucciones)
                if valido:
                    with st.spinner("Generando propuesta de novela..."):
                        propuesta = ui.generar_propuesta(tema, instrucciones)
                        if propuesta:
                            state.actualizar_estado(propuesta=propuesta.to_dict())
                        else:
                            st.error("Error al generar la propuesta")
                else:
                    st.error(mensaje)
            
            # Mostrar propuesta existente si hay una
            if state.estado_actual['propuesta'] and not state.estado_actual['propuesta_aprobada']:
                propuesta = NovelProposal()
                propuesta.__dict__.update(state.estado_actual['propuesta'])
                ui.mostrar_propuesta(propuesta)
            
            # Si la propuesta está aprobada, mostrar el botón de generación de novela
            if state.estado_actual['propuesta_aprobada']:
                if st.button("Comenzar Generación de Novela", key="btn_generar_novela"):
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
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    key="btn_descargar_docx"
                                )
                        else:
                            st.error(f"Error: {resultado}")
        
        if __name__ == "__main__":
            main()
