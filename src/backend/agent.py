import json
from . import llm_client, prompts, retrieval


def run_analysis(user_description: str):
    """
    Executes the full Patent Analyst Agent pipeline using a
    multi-query retrieval strategy.

    1. Query Transformation (Broad + Novel)
    2. Advanced Hybrid Retrieval (Run twice)
    3. De-duplication and Combining
    4. Analyst Synthesis
    """
    print("--- 1. Starting Query Transformation ---")

    llm = llm_client.get_llm()
    if llm is None:
        return {
            "Error": "Could not initialize LLM. Check API keys and config."
        }

    # --- Stage 1: Query Transformation ---
    search_artifacts = {}
    try:
        qt_prompt_formatted = prompts.QUERY_TRANSFORMATION_PROMPT.format(
            user_description=user_description
        )

        response = llm.invoke(qt_prompt_formatted)

        response_content = response.content.strip()
        if response_content.startswith("```json"):
            response_content = response_content[7:-4].strip()

        search_artifacts = json.loads(response_content)

        # Parse the two separate search query objects
        base_search = search_artifacts.get("base_technology_search", {})
        novel_search = search_artifacts.get("novel_features_search", {})

        base_hyde = base_search.get("hyde_abstract")
        base_cpc = base_search.get("cpc_codes")

        novel_hyde = novel_search.get("hyde_abstract")
        novel_cpc = novel_search.get("cpc_codes")

        print(f"  Generated Base HyDE: {base_hyde[:50]}...")
        print(f"  Generated Base CPCs: {base_cpc}")
        print(f"  Generated Novel HyDE: {novel_hyde[:50]}...")
        print(f"  Generated Novel CPCs: {novel_cpc}")

        if not (base_hyde and base_cpc and novel_hyde and novel_cpc):
            return "Error: LLM failed to generate all required search artifacts."

    except json.JSONDecodeError:
        print(f"Error: Failed to decode LLM JSON response. Response was:\n{response.content}")
        return "Error: Agent failed to parse LLM response during query transformation."
    except Exception as e:
        print(f"Error in Stage 1 (Query Transformation): {e}")
        return "Error during query transformation."

    # --- Stage 2: Advanced Hybrid Retrieval (Multi-Query) ---
    print("\n--- 2. Starting Advanced Hybrid Retrieval ---")

    all_contexts = {}  # Use a dict for easy de-duplication by patent_id

    try:
        # Call 1: Broad search for base technology
        print("  Running Base Technology Search...")
        base_contexts = retrieval.fetch_relevant_patents(
            hyde_abstract=base_hyde,
            cpc_codes=base_cpc,
            top_k=3  # Get 3 top results for broad search
        )
        for ctx in base_contexts:
            all_contexts[ctx['patent_id']] = ctx  # Add to dict

        # Call 2: Specific search for novel features
        print("  Running Novel Features Search...")
        novel_contexts = retrieval.fetch_relevant_patents(
            hyde_abstract=novel_hyde,
            cpc_codes=novel_cpc,
            top_k=3  # Get 3 top results for novel search
        )
        for ctx in novel_contexts:
            all_contexts[ctx['patent_id']] = ctx  # Add/overwrite in dict

        # --- Stage 3: De-duplication ---
        # The 'all_contexts' dict now has de-duplicated results.
        # Convert it back to a list.
        final_contexts = list(all_contexts.values())

        if not final_contexts:
            print("  No relevant prior art found in either search.")
            formatted_contexts = "No relevant prior art was found."
        else:
            print(f"  Total unique prior art documents found: {len(final_contexts)}")
            # Format the contexts for the final prompt
            formatted_contexts = "\n\n---\n\n".join(
                [f"Patent ID: {ctx['patent_id']}\nText: {ctx['text']}" for ctx in final_contexts]
            )

    except Exception as e:
        print(f"Error in Stage 2 (Retrieval): {e}")
        return "Error during patent retrieval."

    # --- Stage 4: Analyst Synthesis ---
    print("\n--- 3. Starting Analyst Synthesis ---")

    final_report = ""
    try:
        synthesis_prompt_formatted = prompts.ANALYST_SYNTHESIS_PROMPT.format(
            user_description=user_description,
            prior_art_contexts=formatted_contexts
        )

        final_report_response = llm.invoke(synthesis_prompt_formatted)
        final_report = final_report_response.content

    except Exception as e:
        print(f"Error in Stage 3 (Synthesis): {e}")
        return "Error during final report synthesis."

    print("\n--- Analysis Complete ---")

    # Return a dictionary with all results
    return {
        "final_report": final_report,
        "search_artifacts": search_artifacts
    }


