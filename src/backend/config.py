import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

# OpenAI (for embeddings)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Groq (for LLM reasoning)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Model Names
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
LLM_MODEL = os.getenv("LLM_MODEL")  # Using OpenAI for easy setup TODO: Switch to Groq later

# SerpAPI
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
