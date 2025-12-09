# EREV Copilot – Analytics & RAG Q&A

EREV Copilot is an interactive analytics and question-answering dashboard for our
Extended-Range Electric Vehicle (EREV) range and CO₂-savings study.

The app combines:

- **Range & VMT analytics dashboards** built in Streamlit.
- A **local Retrieval-Augmented Generation (RAG)** pipeline that answers
  questions using our paper, FHWA VMT tables, and supporting PDFs.
- A **fully local LLM** served via [Ollama](https://ollama.com/) running on CPU
  (no GPU instances used; final deployment is on an AWS `t3.large`).

The goal is to let a reviewer explore EV range trade-offs and then ask natural
language questions like:

> “How much EV share does the paper show for a 50-mile range in the worst case?”

and get answers grounded in the project documents.

---

## 1. Features

- **EREV Range Explorer**
  - Visualizes cost per mile, EV share, and range trade-offs.

- **FHWA VMT – 2023 Summary**
  - Shows 2023 U.S. VMT composition and shares used in the modeling.

- **EREV Calculations Results**
  - Summaries of carbon savings and cost metrics across ranges.

- **RAG Q&A (Open-Source)**
  - A chat-like view that:
    - Retrieves the most relevant chunks from our knowledge base.
    - Calls a local Ollama model (`llama3.2:1b` by default).
    - Shows answers plus the context used.

---

## 2. Repo Structure (simplified)

```text
.
├─ src/
│  └─ evcopilot/
│     ├─ __init__.py
│     ├─ app/                # Streamlit pages / layout
│     └─ rag/
│        ├─ __init__.py
│        ├─ indexer.py       # Builds embedding index from PDFs
│        └─ qa.py            # RAG retrieval + Ollama client
│
├─ scripts/
│  ├─ build_knowledge_base.py  # CLI wrapper around rag.indexer
│  └─ run_dashboard.py         # Entry point for Streamlit app
│
├─ docs/
│  └─ knowledge_base/        # Source PDFs for RAG
│
├─ data/
│  └─ knowledge_base/
│     ├─ embeddings.npy      # Dense vectors (created by pipeline)
│     └─ chunks_meta.json    # Chunk text + metadata
│
├─ pipeline-outputs/
│  ├─ screenshots/           # 4 screenshots of the deployed dashboard
│  └─ erev_copilot_demo.mp4  # Short walkthrough recording
│
├─ requirements.txt
└─ README.md
