import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mastering_rag.cli import dependencies
from mastering_rag.ingest import ingest_pdf
from mastering_rag.retrieval import Retriever

_, db, ollama = dependencies()
ingest_pdf(Path("data/pdfs/northwind_research_notes.pdf"), db, ollama, contextualize=True)
for item in Retriever(db, ollama).hybrid("How should ambiguous chunks be enriched?", top_k=3):
    print(f"Context: {item.contextual_prefix}\nChunk: {item.content}\n")
