"""Based on the `README.md` file and the project structure, the purpose of the `scripts/ingest_data.py` file is to implement a data ingestion pipeline. This script is intended to:

1. **Fetch Patent Data**: Retrieve patent data from external sources, such as `SerpAPI` or a custom scraper.
2. **Parse and Process Data**: Extract relevant fields like `abstract`, `title`, and `CPC codes` from the fetched data.
3. **Chunk Text Documents**: Break down large patent documents into smaller, manageable chunks for embedding.
4. **Generate Embeddings**: Use an embedding model (e.g., OpenAI's `text-embedding-3-small`) to create vector representations of the processed data.
5. **Upsert Data to Pinecone**: Store the generated embeddings in the Pinecone vector database, along with metadata (e.g., `patent_id`, `cpc_codes`) for efficient retrieval.

This script is a critical part of the pipeline, as it prepares the data for the retrieval-augmented generation (RAG) process used by the application.
"""

import os
import sys
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


# Add the root directory ('patent-and-prior-art-analyst') to the Python path
# This allows us to import from 'src.backend'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


try:
    from src.backend.config import PINECONE_API_KEY, PINECONE_INDEX_NAME, EMBEDDING_MODEL, OPENAI_API_KEY
except ImportError as e:
    print(f"Error importing configuration: {e}")
    print(
        "Make sure 'src/backend/config.py' exists and you are running this script from the root 'patent-prior-art-analyst' directory.")
    sys.exit(1)


# --- 1. Mock Data ---
# In a real app, this would come from your SerpAPI scraper
MOCK_PATENT_DATA = [
    {
        "patent_id": "US20080163926A1",
        "title": "Organic solar cell",
        "abstract": "An organic solar cell including a substrate, an organic solar cell device, at least one hydrophobic polymer layer and at least one metal layer. The hydrophobic polymer layer prevents moisture from entering the device, while the metal layer blocks both moisture and oxygen. The invention covers the cell's structure and packaging method.",
        "cpc_codes": ["Y02E10/549", "Y02P70/50", "H10K30/20", "H10K30/88", "H10K30/50"]
    },
    {
        "patent_id": "US11171289B2",
        "title": "Method for manufacturing organic solar cell and organic solar cell manufactured using same",
        "abstract": "A method for manufacturing an organic solar cell includes forming electrodes and a photoactive layer on a substrate, drying the layer in a controlled system, and completing with a second electrode. The process enhances yield and longevity of the organic solar cell.",
        "cpc_codes": ["Y02E10/549", "H10K71/811", "H10K71/40", "H10K30/211", "H10K30/57"]
    },
    {
        "patent_id": "US20190378942A1",
        "title": "Thin film packaging device and solar cell",
        "abstract": "A packaging device for thin film solar cells includes inorganic and organic thin film layers in an alternate stacked fashion, optimizing core solar materials' protection against environmental exposure and improving the cell’s power generation efficiency.",
        "cpc_codes": ["Y02E10/50", "H10F77/50", "H10F19/80", "H10F19/31"]
    },
    {
        "patent_id": "US10847724B2",
        "title": "Organic solar cell module and method for manufacturing same",
        "abstract": "This invention describes an organic solar cell module with electrodes arranged to reduce photoactive area and increase the number of sub cells, reducing installation and manufacturing cost. It includes optimized coating and etching methods for scalable solar modules.",
        "cpc_codes": ["Y02E10/549", "H10K39/10", "H10K71/621", "H10K30/81", "H10K39/12"]
    },
    {
        "patent_id": "US20210229883A1",
        "title": "Biodegradable additive",
        "abstract": "A biodegradable additive designed to accelerate decomposition of packaging materials while releasing nutrients into the soil. It can be applied as a coating or adhesive and includes organic fertilizer and optionally seaweed extract, water, starch, and other eco-friendly ingredients.",
        "cpc_codes": ["C05G5/16", "B65D65/403", "Y02W90/10", "B65D65/466", "C05F11/00"]
    },
    {
        "patent_id": "US20240206479A1",
        "title": "Packaging material",
        "abstract": "A multi-layer packaging material enabling release of antimicrobial or antifungal agents in a biodegradable substrate, plus at least one nanocellulose-based coating. The substrate can be cellulose, starch-based, or certain biodegradable polymers, designed for food preservation and waste reduction.",
        "cpc_codes": ["C08J2300/16", "C09D175/04", "B65D81/267", "Y02W90/10", "A01N25/10"]
    }
]


# --- 2. Initialize Clients ---
print("Initializing clients...")

# Initialize Pinecone
try:
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index_name = PINECONE_INDEX_NAME

    # Check if index exists, create if not (using settings from your README)
    if index_name not in pc.list_indexes().names():
        print(f"Index '{index_name}' not found. Creating...")
        pc.create_index(
            name=index_name,
            dimension=1536,  # Dimension for text-embedding-3-small
            metric='cosine',
            spec=ServerlessSpec(
                cloud='aws',
                region='us-east-1'
            )
        )
        print(f"Index '{index_name}' created successfully.")
    else:
        print(f"Index '{index_name}' already exists.")

    index = pc.Index(index_name)

except Exception as e:
    print(f"Error initializing Pinecone: {e}")
    sys.exit(1)

# Initialize Embedding Model
embeddings = OpenAIEmbeddings(
    model=EMBEDDING_MODEL,
    openai_api_key=OPENAI_API_KEY
)

# Initialize Text Splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)


# --- 3. Ingestion Pipeline ---
print("Starting ingestion pipeline...")

for patent in MOCK_PATENT_DATA:
    print(f"Processing patent: {patent['patent_id']}...")

    # Combine title and abstract for a richer text to embed
    text_to_embed = f"Title: {patent['title']}\nAbstract: {patent['abstract']}"

    # Chunk the text
    chunks = text_splitter.split_text(text_to_embed)

    # Generate embeddings for each chunk
    chunk_embeddings = embeddings.embed_documents(chunks)

    # Prepare vectors for upsert
    vectors_to_upsert = []
    for i, (chunk, embedding) in enumerate(zip(chunks, chunk_embeddings)):
        vector_id = f"{patent['patent_id']}-chunk-{i}"

        # Create the vector with rich metadata
        # This metadata is CRITICAL for your hybrid search
        vectors_to_upsert.append({
            "id": vector_id,
            "values": embedding,
            "metadata": {
                "patent_id": patent['patent_id'],
                "cpc_codes": patent['cpc_codes'], # Key for metadata filtering!
                "text": chunk
            }
        })

    # Upsert the vectors to Pinecone
    print(f"Upserting {len(vectors_to_upsert)} vectors for {patent['patent_id']}...")
    index.upsert(vectors=vectors_to_upsert)

print("\n--- Ingestion Complete ---")
print("Pinecone index stats:")
print(index.describe_index_stats())