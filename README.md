# Patent & Prior Art Analyst Agent

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-running-brightgreen.svg)](https://streamlit.io)
[![LangChain](https://img.shields.io/badge/LangChain-enabled-purple.svg)](https://www.langchain.com/)
[![Pinecone](https://img.shields.io/badge/Pinecone-v7.3.0-blue.svg)](https://www.pinecone.io/)
[![Google BigQuery](https://img.shields.io/badge/Google_BigQuery-Data_Source-orange.svg)](https://cloud.google.com/bigquery)

This project is an advanced **Retrieval-Augmented Generation (RAG)** application designed to democratize professional patent research. It functions as an intelligent **Prior Art Analyst Agent**, allowing an inventor or researcher to paste a natural-language description of an idea and receive an expert-level summary of existing, similar inventions.

The agent's "brain" is a multi-step, multi-query reasoning pipeline that mimics the strategy of a professional patent researcher.

---

### Key Features

* **Natural Language Translator:** Converts plain-English ideas into expert-level search queries (semantic vectors and CPC codes).
* **Deep Analysis Report:** Generates a structured report that identifies specific technological overlaps with real patents, not just a list of links.
* **Transparent "AI Thinking":** Features an expandable "See AI Search Strategy" panel that shows the user the exact keywords, CPC codes, and hypothetical abstracts the agent used for its search.
* **Export Tools:** Allows the user to download the final report as a `.txt`, `.md`, or `.docx` file for their records.

---

### The Problem Solved

Traditional patent search (like Google Patents) is difficult. It relies on a user's ability to:
1.  Craft complex boolean queries.
2.  Brainstorm all possible technical **keywords** and synonyms.
3.  Find and use the correct **Cooperative Patent Classification (CPC) codes** (the "expert" tags for patents).

This application automates this entire strategic process, solving the "you don't know what you don't know" problem for inventors.

---

### Key Architectural Innovations

The core of this project is a **multi-query reasoning agent**. Unlike simple RAG apps, it doesn't just embed the user's query. It executes a strategic plan.

1.  **Multi-Query Transformation:** The agent first calls an LLM (Llama 3.3 70B) to act as a researcher. It analyzes the user's idea and generates *two* distinct search plans:
    * **Base Technology Search:** Artifacts for the *general field* (e.g., "organic solar cells").
    * **Novel Features Search:** Artifacts for the *specific improvements* (e.g., "self-healing substrates," "quantum dots").
    * Each plan includes keywords, a **HyDE** abstract (for semantic search), and a list of **CPC codes**.

2.  **Advanced Hybrid Retrieval:** The agent runs *both* search plans against the Pinecone vector database. It performs a **hybrid search** using:
    * **Vector Search:** For semantic meaning (using the HyDE abstracts).
    * **Metadata Filtering:** To strictly filter the search by the AI-generated CPC codes.

3.  **Analyst Synthesis:** The agent de-duplicates the results from both searches and feeds the final list of *grounded* patent data to the LLM's final prompt. This prompt instructs the LLM to act as a patent analyst, compare the user's idea to the *real* prior art, and write the final structured report.

---

### Architecture Diagram

The project is split into two distinct phases: a one-time **Data Ingestion** and the real-time **Runtime Pipeline**.

```

[ONE-TIME INGESTION]

[Google BigQuery] --(1. Efficient SQL Query for 80k patents)--> [scripts/ingest/data.py]
|
(2. Embed in batches)
|
v
[Pinecone Vector DB]
(Our 80,000-patent "Knowledge Base")

```

```

[RUNTIME PIPELINE (app.py)]

[User Idea] --(1. Transform)--> [LLM (Groq)]  --  (2. Plan)--> [agent.py]
                                                        |
(6. Final Report)                                  (3. Query)  [Pinecone DB]
|                                                       |
[LLM (Groq)] <--(5. Grounded Data)--- [retrieval.py] <--(4. Results)
(Synthesize Report)

```

---

### Tech Stack

| Component | Tool / Model                                                               | Purpose |
| :--- |:---------------------------------------------------------------------------| :--- |
| **Orchestration** | Python, LangChain                                                          | Building the multi-step agent logic. |
| **Vector Database** | **Pinecone** (Serverless)                                                  | Storing 80k+ patent vectors; hybrid search. |
| **Data Source** | **Google BigQuery**                                                        | Source for the `patents-public-data` dataset. |
| **LLM (Reasoning)** | **Llama** `3.3-70b-versatile` (via Groq)                                   | Agentic reasoning, query transformation, final synthesis. |
| **Embedding Model** | OpenAI `text-embedding-3-small`                                            | Generating embeddings for the ingestion pipeline. |
| **Frontend** | Streamlit                                                                  | Creating the interactive, user-facing web app. |
| **Dependencies** | `google-cloud-bigquery`, `tqdm`, `python-docx`, `langchain-text-splitters` | Data ingestion, progress bars, and report downloading. |

---

### How to Run This Project (Local Setup)

#### Part A: Application Setup

1.  **Prerequisites:**
    * Python 3.10 or newer.
    * Git.

2.  **Clone the Repository:**
    ```bash
    git clone https://github.com/your-username/Patent-and-Prior-Art-Analyst.git
    cd Patent-and-Prior-Art-Analyst
    ```

3.  **Create a Virtual Environment:**
    ```bash
    # On Windows
    python -m venv venv
    .\venv\Scripts\activate
    
    # On macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Configure Environment Variables:**
    * Copy `.env.example` to `.env` in the root directory:
        ```bash
        cp .env.example .env
        ```
    * Fill in the following keys in your `.env` file:
        * `PINECONE_API_KEY`: Get this from your Pinecone account.
        * `PINECONE_INDEX_NAME`: The name of your Pinecone index (e.g., `patent-analyst-index`).
        * `OPENAI_API_KEY`: Get this from OpenAI (used for embeddings).
        * `GROQ_API_KEY`: Get this from Groq (used for the Llama 3.3 70B LLM).
        * `EMBEDDING_MODEL`: Set to `text-embedding-3-small`.
        * `LLM_MODEL`: Set to `llama-3.3-70b-versatile`.
        * `GOOGLE_APPLICATION_CREDENTIALS`: Path to your Google Cloud JSON key (see Part B).
    * **Windows Path Warning:** For `GOOGLE_APPLICATION_CREDENTIALS`, you MUST use forward slashes (`/`) or double backslashes (`\\`) in your path:
        ```ini
        # GOOD (Recommended)
        GOOGLE_APPLICATION_CREDENTIALS="C:/Users/YourUser/keys/my-gcp-key.json"
        
        # GOOD
        GOOGLE_APPLICATION_CREDENTIALS="C:\\Users\\YourUser\\keys\\my-gcp-key.json"
        
        # BAD (Will fail)
        GOOGLE_APPLICATION_CREDENTIALS="C:\Users\YourUser\keys\my-ggcp-key.json"
        ```

#### Part B: Data Ingestion (One-Time Setup)

This app requires a vector database to function. You must run the ingestion script *once* to populate your Pinecone index.

6.  **Set up Pinecone:**
    * Log in to Pinecone and create a new **Serverless Index**.
    * **Dimensions:** `1536` (for `text-embedding-3-small`).
    * **Metric:** `cosine`.
    * **Name:** Give it a name (e.g., `patent-analyst-index`).
    * **Crucial:** Put this *exact name* into your `.env` file for the `PINECONE_INDEX_NAME` variable.

7.  **Set up Google BigQuery:**
    * Create a new Google Cloud Project.
    * Enable the **BigQuery API** for that project.
    * Go to "IAM & Admin" -> "Service Accounts" -> "Create Service Account".
    * Give it a name, and grant it the **"BigQuery User"** role.
    * Go to the "Keys" tab for that service account, create a new JSON key, and download it.
    * Save this `.json` file somewhere safe (e.g., in your project root) and set the path in your `.env` file (see step 5).
    * **Enable Billing:** You must enable billing on your Google Cloud account for the BigQuery API to work.

8.  **Run the Ingestion Script:**
    * The script is configured to fetch **80,000 patents**. This is a long, one-time process.
    * **Estimated Cost:** This will be very cheap, but not free.
        * **Google BigQuery:** The efficient query scans GBs, not TBs. The cost will be negligible (pennies).
        * **OpenAI Embeddings:** Ingesting 80,000 patents (240k+ chunks) will use ~14M tokens, costing ~$0.28.
        * **Pinecone:** Fits within the 2GB free tier.
    * Run the script from your terminal:
        ```bash
        python scripts/ingest_data.py
        ```
    * This may take **about two hours**. I recommend running it overnight. When it's finished, your Pinecone index will be loaded and ready.

#### Part C: Run the Application

9.  **Launch Streamlit:**
    * Once the ingestion is complete, run the main app:
        ```bash
        streamlit run app.py
        ```
    * Your browser will open, and you can now test the agent!

---

### Limitations & Future Vision

This project is a powerful proof-of-concept, but it has two main limitations based on its "closed-domain" architecture.

* **Limitation 1: The "Walled Garden" (Closed Domain):**
    * The agent does **not** search the live internet. Its knowledge is strictly limited to the **80,000 patents** in its Pinecone database.
    * The database is highly specialized in the following "hot topics":
        * **AI & Computing:** (`G06N`, `G06F`, `G06K`)
        * **Hardware & Energy:** (`H01L` - Semis, `H01M` - Batteries)
        * **Connectivity & Autos:** (`B60W`, `G05D`, `H04W`/`H04B` - Wireless)
        * **MedTech & Biotech:** (`A61B`, `G16H`, `C12N`/`C12Q`)
    * An invention for "a new fishing lure" or "a new concrete mixture" will (correctly) return no results.

* **Limitation 2: The Date Cut-off:**
    * The ingestion query is filtered for patents filed **after 2017**. This was a strategic choice to focus on the "modern era" of tech (e.g., the post-Transformer AI boom) and to stay within our 80,000-patent limit.
    * The agent will not find foundational patents from before 2017.

* **Future Vision (The "Hybrid Agent"):**
    * A future version could implement an "escape hatch."
    * The agent would first search its fast, cheap Pinecone "cache."
    * If it finds nothing, it would then ask the user for permission to perform a *live, slower, and more expensive* query against the entire Google Patents database using a tool like SerpAPI, giving the user the best of both worlds.