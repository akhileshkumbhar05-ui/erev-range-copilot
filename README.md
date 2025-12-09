# EREV Copilot – Analytics & RAG Q&A

This project extends the analysis from the Extended-Range Electric Vehicle (EREV) research paper and provides two main deliverables:

1. Analytics Dashboard (Streamlit) – Visualizing EREV vs BEV trade-offs, CO2 savings, and 2023 VMT.
2. RAG Copilot – Ask questions about the PDFs using a fully local LLM and embeddings (no OpenAI, no API keys).

The system runs fully locally or on an AWS EC2 t3.large CPU-only instance using Ollama + Llama 3.2-1B.

---

## Features
- FHWA 2023 VMT integration
- Cost-per-mile and CO2 savings metrics
- Batteries vs electrified miles comparison
- EREV vs BEV range trade-off visuals
- Local retrieval augmented generation (RAG)
- SentenceTransformers embeddings
- Ollama local LLM backend (Llama 3.2-1B)

---

## Objective
Identify the battery range that maximizes electrified vehicle miles per kWh while minimizing excessive battery size. The analysis suggests that smaller battery ranges (≈50–150 miles) achieve highly efficient electrification vs cost and CO2 impact.

---

## Getting Started (Local)

### Requirements
- Python 3.10
- pip
- Ollama installed locally

### Install dependences
```
pip install -r requirements.txt
```

### Pull the model
```
ollama pull llama3.2:1b
```

### Build embeddings index
```
python scripts/build_knowledge_base.py
```

### Launch dashboard
```
streamlit run scripts/run_dashboard.py
```

Open:
```
http://localhost:8501
```

---

## Deployment (AWS t3.large)

### Instance Settings
- Ubuntu 24.04 LTS (x86_64)
- Instance: t3.large (2 vCPU, 8 GB RAM)
- Storage: 30GB
- Open TCP 8501

### Setup Commands (EC2)
```bash
sudo apt update
sudo apt install -y git python3-venv python3-pip
git clone <repo>
cd <repo>

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:1b

export PYTHONPATH=$PWD/src
python scripts/build_knowledge_base.py

streamlit run scripts/run_dashboard.py --server.address 0.0.0.0 --server.port 8501
```

Open in your browser:
```
http://<EC2_PUBLIC_IP>:8501
```

---

## Challenges We Faced

### No GPU budget
AWS prevented GPU instance launch due to quota. We redesigned everything around CPU-only deployment.

### Large LLMs failed
Bigger models crashed due to RAM. We switched to Llama 3.2-1B (the smallest and most efficient CPU model).

### Slow inference
CPU inference takes time. We reduced context chunks and accepted slower answers instead of paying for GPU.

### Streamlit not reachable externally
Required:
```
--server.address 0.0.0.0
```
plus security group inbound rule for 8501.

---

## How We Solved Them
- Chose smallest LLM (Llama 3.2-1B)
- Increased EBS (30GB)
- Tuned prompt/contexts
- CPU-only architecture
- Fixed PYTHONPATH
- Rebuilt RAG index on EC2 instead of copying

---

## Evidence of Deployment
See:
```
pipeline-outputs/
```
Contains:
- 4 screenshots of deployed copilot dashboard
- A short video walkthrough demonstrating working Q&A

---

## What Could Be Added Next?
- GPU version (g4, g5)
- Larger LLM variants (pending quota)
- Faster retrieval (FAISS/Chroma)
- Additional policy PDFs
- RAG quality evaluation metrics

---

## Repository Structure
```
project/
├─ src/evcopilot/app/       # Streamlit UI
├─ src/evcopilot/rag/       # RAG + Ollama logic
├─ scripts/                 # Build / run scripts
├─ docs/knowledge_base/     # Input PDFs
├─ data/knowledge_base/     # Generated embeddings
├─ pipeline-outputs/        # Screenshots + demo video
├─ requirements.txt
└─ README.md
```

---


