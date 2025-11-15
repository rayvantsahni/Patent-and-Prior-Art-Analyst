import sys
import os
import time
from google.cloud import bigquery
from pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tqdm import tqdm  # For a nice progress bar

# --- Path Setup ---
# This allows us to import from 'src.backend'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from src.backend import config
except ImportError:
    print("Error: Could not import config.py. Make sure you are running this from the root directory.")
    sys.exit(1)

# --- Configuration ---
BIGQUERY_SQL_QUERY = """
-- Use a Common Table Expression (CTE) for clarity
WITH patents_with_text AS (
    SELECT
        pub.publication_number,
        pub.cpc,
        -- Efficient subquery to get just the English title
        (SELECT text FROM UNNEST(pub.title_localized) WHERE language = 'en' LIMIT 1) AS title,
        -- Efficient subquery to get just the English abstract
        (SELECT text FROM UNNEST(pub.abstract_localized) WHERE language = 'en' LIMIT 1) AS abstract
    FROM
        `patents-public-data.patents.publications` AS pub
    WHERE
        pub.filing_date > 20170101 -- "Modern Era" filter
)
-- Main query
SELECT
    pwt.publication_number,
    pwt.title,
    pwt.abstract,
    -- Get all CPC codes for this patent as a single, comma-separated string
    ARRAY_TO_STRING(ARRAY(
        SELECT cpc.code
        FROM UNNEST(pwt.cpc) AS cpc
    ), ', ') AS cpc_codes
FROM
    patents_with_text AS pwt
WHERE
    -- Filter out patents that didn't have an English title or abstract
    pwt.title IS NOT NULL
    AND pwt.abstract IS NOT NULL
    -- This 'peeks' into the cpc array, which is much faster
    -- than the old JOIN + GROUP BY pattern.
    AND EXISTS (
        SELECT 1
        FROM UNNEST(pwt.cpc) AS cpc_code_check
        WHERE
            -- Cluster 1: AI & Computing
            cpc_code_check.code LIKE 'G06N%' OR -- AI / Machine Learning
            cpc_code_check.code LIKE 'G06F%' OR -- Digital Data Processing
            cpc_code_check.code LIKE 'G06K%' OR -- Pattern Recognition

            -- Cluster 2: Hardware, Semis & Batteries
            cpc_code_check.code LIKE 'H01L%' OR -- Semiconductors
            cpc_code_check.code LIKE 'H01M%' OR -- Batteries / Energy Storage

            -- Cluster 3: Autonomous Systems & Connectivity
            cpc_code_check.code LIKE 'B60W%' OR -- Autonomous Vehicle Control
            cpc_code_check.code LIKE 'G05D%' OR -- Drones / Robotics
            cpc_code_check.code LIKE 'H04W%' OR -- Wireless / 5G / 6G
            cpc_code_check.code LIKE 'H04B%' OR -- Transmission / Near-Field

            -- Cluster 4: MedTech & Biotech
            cpc_code_check.code LIKE 'A61B%' OR -- Diagnosis / Surgery / Wearables
            cpc_code_check.code LIKE 'G16H%' OR -- Healthcare Informatics
            cpc_code_check.code LIKE 'C12N%' OR -- Micro-organisms / Gene Editing (CRISPR)
            cpc_code_check.code LIKE 'C12Q%'    -- Measuring / Testing (Bio-assays)
    )
LIMIT 80000;
"""

# Batch sizes for efficiency
EMBED_BATCH_SIZE = 100  # Number of texts to embed at once
PINECONE_BATCH_SIZE = 100  # Number of vectors to upsert at once


# --- Helper Functions ---

def initialize_clients():
    """Initializes and returns all required API clients."""
    print("Initializing clients...")
    try:
        # Assumes GOOGLE_APPLICATION_CREDENTIALS env var is set
        bq_client = bigquery.Client()
        print("  BigQuery client initialized.")
    except Exception as e:
        print(f"  Error initializing BigQuery (check GOOGLE_APPLICATION_CREDENTIALS): {e}")
        return None, None, None, None

    try:
        pc = Pinecone(api_key=config.PINECONE_API_KEY)
        index_name = config.PINECONE_INDEX_NAME

        # First, check if the index actually exists.
        if index_name not in pc.list_indexes().names():
            print(f"  ---!! FATAL ERROR !! ---")
            print(f"  Index '{index_name}' does NOT exist in your Pinecone project.")
            print(f"  Please check your .env file (PINECONE_INDEX_NAME) and the Pinecone console.")
            print(f"  Available indexes: {pc.list_indexes().names()}")
            return None, None, None, None

        # We must create the index object *before* we can use it
        index = pc.Index(index_name)
        print(f"  Pinecone index '{index_name}' successfully found.")

        # # Clear out any old data
        # print("  Clearing all old data from Pinecone index...")
        # index.delete(delete_all=True)
        # print("  Pinecone index cleared.")

    except Exception as e:
        print(f"  Error initializing Pinecone: {e}")
        return None, None, None, None

    embeddings = OpenAIEmbeddings(
        model=config.EMBEDDING_MODEL,
        openai_api_key=config.OPENAI_API_KEY
    )
    print("  Embedding model initialized.")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    print("  Text splitter initialized.")

    return bq_client, index, embeddings, text_splitter


def fetch_data_from_bigquery(client, query):
    """Queries BigQuery and returns the results."""
    print(f"Running BigQuery query... (This may take a moment, it's processing TBs of data)")
    try:
        query_job = client.query(query)  # Make API request
        results = query_job.result()  # Wait for the job to complete
        total_rows = results.total_rows
        print(f"  Query complete. Fetched {total_rows} patents.")
        return list(results)
    except Exception as e:
        print(f"  Error running BigQuery query: {e}")
        return []


def process_and_upsert(patents, index, embeddings, text_splitter):
    """Takes the raw patent data and handles batch embedding and upserting."""

    # Clear the index *before* adding new data
    # We do this here, after we know the query worked.
    print("  Clearing all old data from Pinecone index...")
    try:
        index.delete(delete_all=True)
        print("  Pinecone index cleared.")
    except Exception as e:
        # This can fail on a brand new index, which is fine.
        print(f"  Info: Could not clear index (this is normal for a new index): {e}")

    print("Starting embedding and upserting process...")
    all_chunks_to_embed = []
    all_vectors_to_upsert = []

    print("Step 1/3: Chunking documents...")
    for patent in tqdm(patents, desc="Chunking patents"):
        # Handle potential None values from BigQuery
        title = patent.title or ""
        abstract = patent.abstract or ""

        text_to_embed = f"Title: {title}\nAbstract: {abstract}"
        chunks = text_splitter.split_text(text_to_embed)

        # This is critical: split the comma-separated string back into a list
        cpc_list = patent.cpc_codes.split(', ') if patent.cpc_codes else []

        for j, chunk in enumerate(chunks):
            all_chunks_to_embed.append(chunk)
            all_vectors_to_upsert.append({
                "id": f"{patent.publication_number}-chunk-{j}",
                "metadata": {
                    "patent_id": patent.publication_number,
                    "cpc_codes": cpc_list,  # Store as a list for filtering
                    "text": chunk
                }
            })

    print(f"  Total chunks to process: {len(all_chunks_to_embed)}")

    print("Step 2/3: Batch embedding... (This will take a while)")
    all_embeddings = []
    for i in tqdm(range(0, len(all_chunks_to_embed), EMBED_BATCH_SIZE), desc="Embedding batches"):
        batch_chunks = all_chunks_to_embed[i: i + EMBED_BATCH_SIZE]
        try:
            batch_embeddings = embeddings.embed_documents(batch_chunks)
            all_embeddings.extend(batch_embeddings)
        except Exception as e:
            print(f"  Error embedding batch {i}. Skipping. Error: {e}")
            # Add 'None' placeholders to keep lists in sync
            all_embeddings.extend([None] * len(batch_chunks))
        time.sleep(0.5)  # Avoid API rate limiting

    # Add embeddings to our vector objects, filtering out failed ones
    final_vectors_to_upsert = []
    for i, vec_data in enumerate(all_vectors_to_upsert):
        if all_embeddings[i] is not None:
            vec_data["values"] = all_embeddings[i]
            final_vectors_to_upsert.append(vec_data)

    print(f"  Successfully embedded {len(final_vectors_to_upsert)} chunks.")

    print("Step 3/3: Batch upserting to Pinecone...")
    for i in tqdm(range(0, len(final_vectors_to_upsert), PINECONE_BATCH_SIZE), desc="Upserting batches"):
        batch_vectors = final_vectors_to_upsert[i: i + PINECONE_BATCH_SIZE]
        try:
            index.upsert(vectors=batch_vectors)
        except Exception as e:
            print(f"  Error upserting batch {i}. Skipping. Error: {e}")

    print("--- Upsert Complete ---")


def main():
    """Main function to run the full ingestion pipeline."""
    bq_client, index, embeddings, text_splitter = initialize_clients()
    if not all([bq_client, index, embeddings, text_splitter]):
        print("Exiting due to initialization failure.")
        return

    print(f"--- Running Query to fetch ({BIGQUERY_SQL_QUERY.split('LIMIT')[-1].strip().replace(';', '')} patents) ---")
    patents = fetch_data_from_bigquery(bq_client, BIGQUERY_SQL_QUERY)

    if not patents:
        print("Test query failed to fetch patents. Exiting.")
        return

    process_and_upsert(patents, index, embeddings, text_splitter)

    print("\n--- Ingestion Pipeline Finished ---")
    print("Final Pinecone index stats after test:")
    print(index.describe_index_stats())

    print("\n--- [INFO] ---")
    print(f"Retrieval of {BIGQUERY_SQL_QUERY.split('LIMIT')[-1].strip().replace(';', '')} patents complete.")


# --- Script Execution ---
if __name__ == "__main__":
    main()
