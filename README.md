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
