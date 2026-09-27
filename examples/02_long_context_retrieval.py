from mastering_rag.cli import dependencies
from mastering_rag.generation import generate_answer
from mastering_rag.retrieval import Retriever

_, db, ollama = dependencies()
query = "Compare normal and emergency deployment controls, including audit requirements."
results = Retriever(db, ollama).long_context(query, top_k=3, token_budget=5000, radius=2)
print(generate_answer(ollama, query, results))
