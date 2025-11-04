# Patent-and-Prior-Art-Analyst


### Project Overview

This project is an advanced **Retrieval-Augmented Generation (RAG)** application designed to democratize professional patent research. It functions as an intelligent **Prior Art Analyst Agent**, allowing inventors to paste a natural language description of their idea and receive an expert-level summary of existing, similar inventions (prior art).

Unlike basic keyword search tools, this application utilizes **Query Transformation** to mimic the strategic reasoning of a professional patent researcher, resulting in highly accurate and relevant results.

---

### The Problem Solved

Traditional patent search relies on a user's ability to craft complex boolean queries, brainstorm technical keywords, and find correct **Cooperative Patent Classification (CPC) codes**. This application automates this expert-level strategic work, offering a novel and accessible solution for assessing the novelty of a new invention.

---

### Key Architectural Innovations

The core novelty of this system lies in its multi-stage RAG pipeline:

1.  **Query Transformation (The Agent Brain):** Instead of simply embedding the user's input, the LLM first generates three crucial artifacts:
    * **Technical Keywords** and synonyms.
    * A **Hypothetical Document Embedding (HyDE)** abstract.
    * The most likely **CPC Codes** for the invention.
2.  **Advanced Hybrid Retrieval:** The system performs a **hybrid search** against the vector database:
    * **Vector Search:** Using the HyDE abstract vector for semantic similarity.
    * **Metadata Filtering:** Using the AI-generated **CPC Codes** to strictly filter the result set, ensuring only highly relevant patents are returned.
3.  **Analyst Synthesis:** The final LLM prompt instructs the model to act as a **patent analyst**, synthesizing the retrieved prior art and the user's idea into a structured report that identifies specific technological overlaps.

---

### Tech Stack

| Component | Tool / Model | Purpose |
| :--- | :--- | :--- |
| **Orchestration** | Python, LangChain | Building the complex multi-step RAG chain. |
| **Vector Database** | **Pinecone** | Storing patent vectors and enabling advanced metadata filtering (e.g., by CPC code). |
| **LLM (Reasoning)** | OpenAI GPT-4o / GCP Gemini 1.5 Pro | Query Transformation (HyDE/Keywords/CPC) and final Analyst Synthesis. |
| **Embedding Model** | OpenAI `text-embedding-3-small` / GCP `text-embedding-004` | Generating high-quality patent embeddings. |
| **Data Source** | Google Patents Database | Primary source for patent abstracts and metadata. |
| **Frontend** | Streamlit | Creating an interactive, web-based UI for demonstration. |


---

### Project Workflow

This project is built using a "Separation of Concerns" principle. The core AI logic (the "agent") is developed separately from the web interface (the "frontend"), making the system modular, testable, and scalable.



#### Phase 1: Setup & Data Ingestion Pipeline

1.  **Environment & DB Setup**:
    * Initialize a new **Pinecone serverless index** to store patent vectors.
    * Set up a Python environment with all dependencies (`langchain`, `pinecone-client`, `openai` or `google-cloud-aiplatform`, `streamlit`).
2.  **Data Ingestion Script (`scripts/ingest_data.py`)**:
    * Write a script to fetch patent data (e.g., via `SerpAPI` or a custom scraper).
    * Parse the data to extract the `abstract`, `title`, and `cpc_codes`.
    * Chunk the text documents.
    * Generate embeddings for each chunk using a model like `text-embedding-3-small`.
    * **Upsert** the vectors to Pinecone, including rich metadata (e.g., `{'patent_id': '...', 'cpc_codes': ['G06N 3/08']}`).

#### Phase 2: Building the Core "Analyst Agent" (`src/patent_analyst/`)

1.  **Prompt Engineering (`prompts.py`)**:
    * Define all LLM prompts as string constants in a central file for easy editing. This includes the "Query Transformation" prompt and the final "Analyst Synthesis" prompt.
2.  **Vector Retrieval (`retrieval.py`)**:
    * Create a module to handle all interactions with Pinecone (e.g., `initialize_pinecone`, `query_patents`).
3.  **Core Agent Logic (`agent.py`)**:
    * Build the main `run_analysis(user_description)` function.
    * This function calls an LLM to perform **Query Transformation** (extract keywords, generate HyDE abstract, and predict CPC codes).
    * It then calls the `retrieval.py` module to perform the **Hybrid Search** (vector search + metadata filtering).
    * Finally, it calls the LLM with the "Analyst Synthesis" prompt to generate the final report.

#### Phase 3: Frontend & Showcase (`app.py`)

1.  **Build the UI (`app.py`)**:
    * Create a simple **Streamlit** interface.
    * Add a title (`st.title`), a text area (`st.text_area`) for the invention description, and a button (`st.button`).
2.  **Connect the Brain to the UI**:
    * Import the `run_analysis` function from `src/patent_analyst/agent.py`.
    * When the user clicks the button, call this function with the user's input.
    * Display the returned report using `st.markdown()` and `st.spinner()`.