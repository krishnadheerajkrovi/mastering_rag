import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mastering_rag.cli import dependencies
from mastering_rag.generation import generate_answer, validate_answer
from mastering_rag.retrieval import Retriever

_, db, ollama = dependencies()
query = "Who can authorize emergency production changes and what happens afterward?"
results = Retriever(db, ollama).hybrid(query, top_k=5)
answer = generate_answer(ollama, query, results)
print(answer)
print(json.dumps(validate_answer(ollama, query, answer, results), indent=2))
