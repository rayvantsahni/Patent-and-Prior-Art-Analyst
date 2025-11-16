from langchain_groq import ChatGroq
from langchain_openai import OpenAIEmbeddings

from . import config


def get_llm():
    """
    Initializes and returns the main Language Model (LLM) for reasoning.

    This function reads the model name and API key from the config
    and returns an initialized LangChain model object.
    """
    if not config.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not found in environment variables.")
    try:
        llm = ChatGroq(
            model=config.LLM_MODEL,
            api_key=config.GROQ_API_KEY,
            temperature=0.0  # We want deterministic, analytical output
        )
        return llm
    except Exception as e:
        print(f"Error initializing Groq LLM: {e}")
        return None


def get_embedding_model():
    """
    Initializes and returns the embedding model.

    This function reads the embedding model name and API key from the
    config and returns an initialized LangChain embedding model object.
    """
    if not config.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not found in environment variables.")

    try:
        embedding_model = OpenAIEmbeddings(
            model=config.EMBEDDING_MODEL,
            openai_api_key=config.OPENAI_API_KEY
        )
        return embedding_model
    except Exception as e:
        print(f"Error initializing Embedding Model: {e}")
        return None
