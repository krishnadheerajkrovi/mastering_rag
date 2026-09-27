.PHONY: setup models db-up db-down pdfs ingest ingest-contextual test demo

setup:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt
	.venv/bin/pip install -e .

models:
	ollama pull nomic-embed-text
	ollama pull llama3.2:3b

db-up:
	docker compose up -d --wait

db-down:
	docker compose down

pdfs:
	.venv/bin/python scripts/create_dummy_pdfs.py

ingest:
	.venv/bin/python -m mastering_rag.cli ingest data/pdfs

ingest-contextual:
	.venv/bin/python -m mastering_rag.cli ingest data/pdfs --contextualize

test:
	.venv/bin/python -m pytest -q

demo:
	.venv/bin/python -m mastering_rag.cli ask "What controls protect Acme's production deployments?" --mode hybrid --validate
