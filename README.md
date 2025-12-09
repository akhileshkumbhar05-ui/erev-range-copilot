# EREV Copilot – Streamlit + Local RAG on CPU (AWS t3.large)

EREV Copilot is a research-driven analytics and question-answering system focused on Extended-Range Electric Vehicles (EREVs) and national VMT electrification. The system combines interactive data visualizations with a Retrieval-Augmented Generation (RAG) copilot that answers questions using research PDFs and FHWA 2023 data, **without using paid APIs or GPUs**.

This entire pipeline is deployed on a low-cost **AWS t3.large** CPU instance and runs completely locally using **Ollama** + **Llama 3.2 (1B)** model.

---

## What this project demonstrates

- EREV range vs. cost vs. CO₂ savings
- Electric vehicle miles vs total VMT using U.S. FHWA 2023 data
- A working local RAG system using open-source models
- Fully CPU-only inference and deployment
- End-to-end cloud deployment (AWS EC2)

This shows that meaningful AI + transportation analytics can be deployed **without expensive GPU infrastructure**.

---

## Why it matters

Battery cost and EV range are the biggest barriers to rapid EV adoption. EREVs provide a practical transition path by enabling higher electric miles using smaller batteries. This platform helps:
- Visualize EV electrification potential
- Explore emissions reductions
- Understand range trade-offs
- Ask natural questions about the research

---

## Technology Stack

- Streamlit
- Ollama (local LLM)
- Llama 3.2 1B
- SentenceTransformers
- Python
- AWS EC2 (t3.large CPU)

---

## How to Run Locally (minimal steps)

```bash
git clone https://github.com/<yourusername>/<yourrepo>.git
cd <yourrepo>
python -m venv .venv
.venv\Scripts\activate   # or source .venv/bin/activate
pip install -r requirements.txt
ollama pull llama3.2:1b
export PYTHONPATH=$PWD/src
python scripts/build_knowledge_base.py
streamlit run scripts/run_dashboard.py --server.port 8501
