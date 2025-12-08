# Dockerfile – EREV Copilot app (analytics + RAG) using open-source stack

FROM python:3.11-slim

WORKDIR /app

# System deps (build tools and basic libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Streamlit port
EXPOSE 8501

# On container start:
# 1. Build the RAG knowledge base (if docs exist).
# 2. Launch Streamlit dashboard.
CMD bash -lc "\
  if [ -d docs/knowledge_base ] && [ \"\$(ls -A docs/knowledge_base 2>/dev/null)\" ]; then \
    echo 'Building RAG knowledge base...'; \
    python scripts/build_knowledge_base.py || echo 'RAG build failed, continuing...'; \
  else \
    echo 'No docs/knowledge_base found, skipping RAG build.'; \
  fi && \
  streamlit run scripts/run_dashboard.py --server.port 8501 --server.address 0.0.0.0"
