from pinecone import Pinecone
from . import config
from .llm_client import get_embedding_model


# --- Helper Function ---
def get_pinecone_index():
    """
    Initializes and returns the Pinecone index object.
    """
    try:
        pc = Pinecone(api_key=config.PINECONE_API_KEY)
        index = pc.Index(config.PINECONE_INDEX_NAME)
        return index
    except Exception as e:
        print(f"Error initializing Pinecone index: {e}")
        return None


# --- Main Retrieval Function ---
def fetch_relevant_patents(hyde_abstract: str, cpc_codes: list, top_k: int = 5):
    """
    Performs the Advanced Hybrid Retrieval.

    1. Generates an embedding for the HyDE abstract.
    2. Creates a metadata filter for the AI-generated CPC codes.
    3. Queries Pinecone using both the vector and the filter.

    Args:
        hyde_abstract (str): The AI-generated hypothetical abstract.
        cpc_codes (list): A list of AI-generated CPC codes (e.g., ['G06N 3/08']).
        top_k (int): The number of patents to retrieve.

    Returns:
        list: A list of retrieved patent contexts (dictionaries).
    """
    print(f"--- Starting Retrieval ---")
    print(f"  Querying with CPC Codes: {cpc_codes}")

    # 1. Initialize dependencies
    index = get_pinecone_index()
    embedding_model = get_embedding_model()

    if index is None or embedding_model is None:
        return []  # Return empty if clients failed to init

    # 2. Generate embedding for the HyDE abstract
    try:
        query_vector = embedding_model.embed_query(hyde_abstract)
    except Exception as e:
        print(f"Error generating query embedding: {e}")
        return []

    # 3. Create the metadata filter
    # This filter ensures we only search within the relevant CPC codes.
    # We use $in to match any document that has *at least one* of the predicted codes.
    if not cpc_codes:
        print("  Warning: No CPC codes provided. Performing pure vector search.")
        metadata_filter = {}
    else:
        metadata_filter = {
            "cpc_codes": {
                "$in": cpc_codes
            }
        }

    # 4. Query Pinecone (Hybrid Search)
    try:
        query_response = index.query(
            vector=query_vector,
            filter=metadata_filter,
            top_k=top_k,
            include_metadata=True
        )
        print(f"  Pinecone query successful. Found {len(query_response.get('matches', []))} matches.")
    except Exception as e:
        print(f"Error querying Pinecone: {e}")
        return []

    # 5. Format and return results
    contexts = []
    for match in query_response.get('matches', []):
        contexts.append({
            "text": match['metadata'].get('text', ''),
            "patent_id": match['metadata'].get('patent_id', ''),
            "score": match.get('score', 0)
        })

    return contexts
