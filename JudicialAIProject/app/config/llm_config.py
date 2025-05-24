'''
Configuration and initialization for Generative AI models using LangChain.
'''
import os
import logging
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_groq import ChatGroq # Uncomment if you add Groq  #otra alternativa a Google por si las moscas

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
# Ensure .env is in the project root: JudicialAIProject/.env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

# --- Google Generative AI Configuration ---
google_api_key = os.getenv("GOOGLE_API_KEY") #OJO SE DEBE BORRAR, NO COMPARTIR

if not google_api_key:
    logging.warning("GOOGLE_API_KEY not found in .env file. Google GenAI services will not be available.")
    llm_google = None
else:
    try:
        # Initialize the Google Generative AI model
        # You can specify the model name, e.g., "gemini-pro" or "gemini-1.5-flash-latest"
        # "gemini-1.5-flash-latest" is often a good balance of speed and capability for summarization/classification
        llm_google = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest", 
            google_api_key=google_api_key,
            temperature=0.3, # Adjust for creativity vs. factuality
            # convert_system_message_to_human=True # Depending on model and Langchain version
        )
        logging.info("Google GenAI model initialized successfully (gemini-1.5-flash-latest).")
    except Exception as e:
        logging.error(f"Failed to initialize Google GenAI model: {e}")
        llm_google = None

# --- Groq Configuration (Optional) ---
# groq_api_key = os.getenv("GROQ_API_KEY")
# llm_groq = None

# if not groq_api_key:
#     logging.warning("GROQ_API_KEY not found in .env file. Groq services will not be available.")
# else:
#     try:
#         # Initialize the Groq model
#         # Example: "mixtral-8x7b-32768" or "llama3-8b-8192"
#         llm_groq = ChatGroq(
#             model_name="llama3-8b-8192", # Or another model you prefer from Groq
#             groq_api_key=groq_api_key,
#             temperature=0.3
#         )
#         logging.info("Groq model initialized successfully (e.g., llama3-8b-8192).")
#     except Exception as e:
#         logging.error(f"Failed to initialize Groq model: {e}")
#         llm_groq = None

# --- Default LLM Selection ---
# You can set a default LLM to be used by other modules
# For now, let's prioritize Google if available.

default_llm = None
if llm_google:
    default_llm = llm_google
    logging.info("Using Google GenAI as the default LLM.")
# elif llm_groq:  # Uncomment if you configure Groq
#     default_llm = llm_groq
#     logging.info("Using Groq as the default LLM as Google GenAI is not available.")
else:
    logging.warning("No LLM has been initialized successfully. AI features will be disabled.")

# You can add functions here to get specific LLMs if needed, e.g.:
# def get_google_llm():
#     return llm_google

# def get_groq_llm():
#     return llm_groq

# def get_default_llm():
#     return default_llm

if __name__ == "__main__":
    if default_llm:
        logging.info(f"Default LLM ({type(default_llm).__name__}) is configured and ready.")
        # try:
        #     # Test invocation (optional, might incur costs)
        #     # response = default_llm.invoke("Hello, how are you today?")
        #     # logging.info(f"Test LLM response: {response.content}")
        # except Exception as e:
        #     logging.error(f"Error during test LLM invocation: {e}")
    else:
        logging.error("No LLM is available. Please check your .env file and API keys.")
