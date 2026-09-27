import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mastering_rag.cli import dependencies
from mastering_rag.retrieval import Retriever

_, db, ollama = dependencies()
results = Retriever(db, ollama).hybrid("production deployment approval and rollback", top_k=5)
for item in results:
    print(f"{item.score:.4f} | {item.citation}\n{item.content}\n")
