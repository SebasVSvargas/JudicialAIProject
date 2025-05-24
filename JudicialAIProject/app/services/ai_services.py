'''
Services for interacting with Generative AI models for summarization and classification.
'''
import logging
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
# Assuming llm_config.py is in the same directory and default_llm is configured
from app.config.llm_config import default_llm 

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Prompt Templates ---

# Prompt for summarizing an "anotacion" (judicial action description)
summarization_template_text = """
Eres un asistente legal experto en el sistema judicial colombiano.
Por favor, resume el siguiente texto de una actuación judicial (anotación) de manera concisa y clara, 
extrayendo los puntos clave y la información más relevante para un abogado que necesita entender rápidamente de qué se trata.
Enfócate en el propósito principal de la actuación, las decisiones tomadas, las fechas importantes mencionadas (si las hay) y cualquier requerimiento o plazo.

Texto de la actuación judicial:
{texto_actuacion}

Resumen conciso:
"""
summarization_prompt = PromptTemplate(
    input_variables=["texto_actuacion"],
    template=summarization_template_text
)

# Prompt for classifying the urgency of a judicial action
# We can provide a few examples (few-shot) or let the model decide based on keywords and context.
# For simplicity, starting with a zero-shot prompt that can be refined.
classification_template_text = """
Eres un asistente legal experto en el sistema judicial colombiano.
Analiza la siguiente actuación judicial (tipo y anotación) y clasifica su urgencia en una de las siguientes categorías: ALTA, MEDIA, BAJA.

Considera los siguientes criterios para la clasificación:
- ALTA: Requiere acción inmediata, vencimiento de términos inminente, citaciones a audiencias próximas, decisiones cruciales que cambian el estado del proceso significativamente.
- MEDIA: Actualizaciones importantes que deben ser revisadas pronto pero no requieren acción inmediata, autos de trámite relevantes.
- BAJA: Notificaciones informativas, actualizaciones menores, constancias.

Anotación de la Actuación: {texto_actuacion}

Clasificación de Urgencia (solo una palabra: ALTA, MEDIA, o BAJA):
"""
classification_prompt = PromptTemplate(
    input_variables=["texto_actuacion"],
    template=classification_template_text
)

# --- Service Functions ---

def generar_resumen_actuacion(texto_actuacion: str) -> str | None:
    '''
    Generates a summary for the given judicial action text using the configured LLM.

    Args:
        texto_actuacion: The text (anotacion) of the judicial action.

    Returns:
        The generated summary as a string, or None if an error occurs or LLM is not available.
    '''
    if not default_llm:
        logging.warning("LLM not available. Cannot generate summary.")
        return None
    if not texto_actuacion or not texto_actuacion.strip():
        logging.warning("Texto de actuación vacío o nulo. No se generará resumen.")
        return ""

    try:
        # Create the chain: prompt | llm | output_parser
        chain = summarization_prompt | default_llm | StrOutputParser()
        summary = chain.invoke({"texto_actuacion": texto_actuacion})
        logging.info(f"Resumen generado para la actuación (primeros 50 chars): {texto_actuacion[:50]}...")
        return summary.strip()
    except Exception as e:
        logging.error(f"Error al generar resumen con LLM: {e}")
        return None

def clasificar_urgencia_actuacion(texto_actuacion: str) -> str | None:
    '''
    Classifies the urgency of a given judicial action using the configured LLM.

    Args:
        tipo_actuacion: The type of the judicial action (e.g., "Fijación Estado").
        texto_actuacion: The text (anotacion) of the judicial action.

    Returns:
        The urgency classification (e.g., "ALTA", "MEDIA", "BAJA") or None if an error occurs.
    '''
    if not default_llm:
        logging.warning("LLM not available. Cannot classify urgency.")
        return None
    if not texto_actuacion or not texto_actuacion.strip():
        logging.warning("Texto de actuación vacío o nulo. No se clasificará urgencia.")
        return "BAJA" # Default to BAJA if no text to analyze

    try:
        chain = classification_prompt | default_llm | StrOutputParser()
        classification = chain.invoke({
            
            "texto_actuacion": texto_actuacion
        })
        # Ensure the output is one of the expected categories
        valid_classifications = ["ALTA", "MEDIA", "BAJA"]
        parsed_classification = classification.strip().upper()
        if parsed_classification in valid_classifications:
            logging.info(f"Clasificación de urgencia generada: {parsed_classification}")
            return parsed_classification
        else:
            logging.warning(f"Clasificación no reconocida '{parsed_classification}'. Se devolverá MEDIA por defecto.")
            return "MEDIA" # Default if the LLM returns something unexpected
    except Exception as e:
        logging.error(f"Error al clasificar urgencia con LLM: {e}")
        return None

# --- Example Usage (for testing this module directly) ---
# if __name__ == "__main__":
#     if not default_llm:
#         logging.error("LLM no configurado. Por favor, verifica tu .env y llm_config.py")
#     else:
#         logging.info("Probando servicios de IA...")
        
#         sample_anotacion_1 = ("SE ADMITE DEMANDA Y SE ORDENA NOTIFICAR A LA PARTE DEMANDADA. "
#                               "SE CONCEDE TÉRMINO DE 10 DÍAS PARA CONTESTAR.")
#         sample_tipo_1 = "AUTO ADMISORIO"

#         sample_anotacion_2 = ("SE RECIBE MEMORIAL DE LA PARTE ACTORA APORTANDO PRUEBAS. "
#                               "SECRETARÍA AGREGUE AL EXPEDIENTE.")
#         sample_tipo_2 = "Memorial"

#         sample_anotacion_3 = ("AUDIENCIA DE CONCILIACIÓN FIJADA PARA EL DÍA 05 DE JUNIO DE 2025 A LAS 09:00 AM. "
#                               "SE REQUIERE LA COMPARECENCIA DE LAS PARTES.")
#         sample_tipo_3 = "FIJACION FECHA AUDIENCIA"

#         print("\n--- Prueba de Resumen 1 ---")
#         resumen1 = generar_resumen_actuacion(sample_anotacion_1)
#         if resumen1:
#             print(f"Anotación Original: {sample_anotacion_1}")
#             print(f"Resumen IA: {resumen1}")

#         print("\n--- Prueba de Clasificación 1 ---")
#         clasificacion1 = clasificar_urgencia_actuacion(sample_tipo_1, sample_anotacion_1)
#         if clasificacion1:
#             print(f"Tipo: {sample_tipo_1}, Anotación: {sample_anotacion_1}")
#             print(f"Clasificación IA: {clasificacion1}")

#         print("\n--- Prueba de Resumen 2 ---")
#         resumen2 = generar_resumen_actuacion(sample_anotacion_2)
#         if resumen2:
#             print(f"Anotación Original: {sample_anotacion_2}")
#             print(f"Resumen IA: {resumen2}")

#         print("\n--- Prueba de Clasificación 2 ---")
#         clasificacion2 = clasificar_urgencia_actuacion(sample_tipo_2, sample_anotacion_2)
#         if clasificacion2:
#             print(f"Tipo: {sample_tipo_2}, Anotación: {sample_anotacion_2}")
#             print(f"Clasificación IA: {clasificacion2}")

#         print("\n--- Prueba de Clasificación 3 (Urgente) ---")
#         clasificacion3 = clasificar_urgencia_actuacion(sample_tipo_3, sample_anotacion_3)
#         if clasificacion3:
#             print(f"Tipo: {sample_tipo_3}, Anotación: {sample_anotacion_3}")
#             print(f"Clasificación IA: {clasificacion3}")
