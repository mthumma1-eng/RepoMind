# Codebase Intelligence

A Python + Streamlit MVP for analyzing public GitHub repositories.

## Features
- Clone a public GitHub repository
- Index supported source and documentation files
- Ask questions using lexical retrieval, optional dense embeddings, RRF fusion, and Groq generation
- Run lightweight Python static checks for potential issues
- Visualize Python import relationships
- Generate a Markdown onboarding report

## Requirements
- Python 3.10+
- Git installed and available on PATH
- Internet access for cloning public repositories and downloading the embedding model
- Optional Groq API key for generated answers

## Setup with uv
```bash
uv init
uv add -r requirements.txt
cp .env.example .env
# Add your GROQ_API_KEY to .env (optional)
uv run streamlit run app.py
```

## Setup with pip
```bash
python -m venv .venv
# Windows PowerShell:
.venv\\Scripts\\Activate.ps1
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

## Notes
- First dense indexing may take time and download model weights.
- If the embedding model cannot load, the app still falls back to BM25-like lexical retrieval.
- Bug findings are heuristics, not proof of vulnerabilities or defects.
- Architecture visualization currently focuses on Python import relationships.
- Only analyze repositories you are authorized to inspect. Repository content is treated as untrusted input.
- This is a hackathon MVP, not a production security scanner.
