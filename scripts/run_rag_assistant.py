# scripts/run_rag_assistant.py

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from evcopilot.rag.qa import (  # noqa: E402
    RAGIndexNotFoundError,
    answer_question,
    load_index,
)


@st.cache_resource(show_spinner=False)
def _load_index_cached():
    return load_index()


def main() -> None:
    st.set_page_config(
        page_title="EREV Copilot – RAG Q&A",
        page_icon="⚡",
        layout="wide",
    )

    st.title("⚡ EREV Copilot – RAG Q&A (Open-Source)")
    st.write(
        "Ask questions about the EREV range analysis, FHWA VMT data, and the paper. "
        "Answers are grounded in your local knowledge base (docs/knowledge_base)."
    )

    try:
        embeddings, chunks_meta = _load_index_cached()
    except RAGIndexNotFoundError as e:
        st.error(str(e))
        st.info(
            "Steps:\n"
            "1. Put your EREV paper and related docs into `docs/knowledge_base/`.\n"
            "2. Run `python scripts/build_knowledge_base.py`.\n"
            "3. Make sure an Ollama server is running with your chosen model.\n"
            "4. Restart this app."
        )
        return

    question = st.text_area(
        "Question",
        placeholder="Example: How many additional electrified miles do EREVs "
                    "deliver compared with 300-mile BEVs at 2023 U.S. VMT?",
        height=120,
    )

    col1, col2 = st.columns([1, 3])
    with col1:
        top_k = st.slider("Context chunks", 2, 8, 4)

    ask = st.button("Ask EREV Copilot", type="primary")

    if ask:
        if not question.strip():
            st.warning("Please enter a question.")
            return

        with st.spinner("Thinking with your EREV knowledge base..."):
            try:
                answer, retrieved = answer_question(
                    question,
                    embeddings=embeddings,
                    chunks_meta=chunks_meta,
                    top_k=top_k,
                )
            except Exception as e:
                st.error(f"Error while answering question: {e}")
                return

        st.subheader("Answer")
        st.markdown(answer)

        with st.expander("Show retrieved context"):
            for i, ch in enumerate(retrieved, start=1):
                st.markdown(
                    f"**Chunk {i}**  \n"
                    f"*source:* `{ch.source}`  \n"
                    f"*score:* `{ch.score:.3f}`  \n\n"
                    f"{ch.text}"
                )


if __name__ == "__main__":
    main()
