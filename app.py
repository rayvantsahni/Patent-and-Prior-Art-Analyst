import streamlit as st
import sys
import os
import io  # Needed for in-memory file creation
from datetime import datetime  # Needed for smart filenames
from docx import Document  # Needed for .docx creation

# --- Path Setup ---
# Add the 'src' directory to the Python path
# This allows us to import from 'src.backend'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.backend import agent
except ImportError:
    st.error("Error: Could not import the backend agent. Make sure 'src/backend/agent.py' exists.")
    st.stop()


def _generate_filename_prefix():
    """Generates a clean, timestamped filename prefix."""
    now = datetime.now()
    return f"patent_analysis_{now.strftime('%Y%m%d_%H%M%S')}"


def _create_docx(content):
    """Creates an in-memory .docx file from the report text."""
    doc = Document()
    doc.add_heading('Patent Analysis Report', 0)

    # Add the full report as paragraphs
    # This preserves line breaks
    for line in content.split('\n'):
        doc.add_paragraph(line)

    # Save to an in-memory buffer
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


# --- Page Configuration ---
st.set_page_config(
    page_title="Patent Prior Art Analyst",
    page_icon="🤖",
    layout="wide"
)

# --- Page Title & Description ---
st.title("🤖 Patent & Prior Art Analyst Agent")
st.markdown("""
Welcome! This application uses an advanced AI-powered agent to help you research prior art for your invention.
Simply describe your idea in plain English, and the agent will:

1.  **Transform** your idea into technical keywords, a hypothetical abstract, and relevant CPC codes.
2.  **Search** a patent database for semantically similar and relevant documents.
3.  **Synthesize** the findings into an expert-level summary.
""")

st.divider()

# --- Input Area ---
user_description = st.text_area(
    "Describe your invention here:",
    height=200,
    placeholder="e.g., A smart coffee mug that uses a rechargeable battery to keep coffee at a perfect 140°F and "
                "syncs with a mobile app..."
)

# --- Button Styling (Safer Injection) ---
# Inject the custom CSS for the button
st.markdown(
    """
<style>
div.stButton > button:first-child {
    background-color: #4CAF50; /* Green */
    color: white;
    border: none;
    padding: 10px 20px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 16px;
    margin: 4px 2px;
    cursor: pointer;
    border-radius: 8px;
}
div.stButton > button:first-child:hover {
    background-color: #45a049; /* Darker green */
}
</style>
""",
    unsafe_allow_html=True
)

# --- Analysis Button Logic ---
# Use a standard 'st.button' check, which is more reliable
if st.button("Analyze Prior Art"):
    if not user_description.strip():
        st.warning("Please enter a description of your invention.")
    else:
        # Show a spinner while the agent is working
        with st.spinner("Agent is analyzing... This may take a moment."):
            try:
                # Call the core agent logic
                final_report = agent.run_analysis(user_description)

                # --- Display Final Report ---
                # st.header("Analysis Report")
                st.markdown("<h3 style='text-align: center; text-decoration: underline;'>Analysis Report</h3>", unsafe_allow_html=True)

                # 1. Show the "pretty" rendered markdown. This wraps text.
                st.markdown(final_report)

                # 2. Put the 'code' block (with the copy button) inside an expander.
                with st.expander("Copy Report Text"):
                    st.code(final_report, language="markdown")

                # --- Download Buttons ---
                st.subheader("Download Report")

                # Generate a single, unique filename prefix (using updated function name)
                file_prefix = _generate_filename_prefix()

                # Use columns to place buttons side-by-side
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.download_button(
                        label="Download as Text (.txt)",
                        data=final_report,
                        file_name=f"{file_prefix}.txt",
                        mime="text/plain"
                    )

                with col2:
                    st.download_button(
                        label="Download as Markdown (.md)",
                        data=final_report,
                        file_name=f"{file_prefix}.md",
                        mime="text/markdown"
                    )

                with col3:
                    # Create the docx file in memory (using updated function name)
                    docx_data = _create_docx(final_report)
                    st.download_button(
                        label="Download as Word (.docx)",
                        data=docx_data,
                        file_name=f"{file_prefix}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )

            except Exception as e:
                st.error(f"An error occurred during analysis: {e}")
