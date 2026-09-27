# Mastering RAG locally

A compact, runnable Python lab for retrieval-augmented generation with **Ollama**, **PostgreSQL**, and **pgvector**. It includes synthetic PDFs and separate samples for hybrid retrieval, long-context retrieval, contextual retrieval, grounded generation, citations, and output validation.

Everything runs locally. The sample documents are fictional and contain no private data.

## What each sample demonstrates

| Technique | Implementation |
| --- | --- |
| Vector retrieval | Ollama `nomic-embed-text` embeddings and pgvector cosine distance |
| Hybrid retrieval | Dense vector search + PostgreSQL full-text ranking fused with reciprocal rank fusion (RRF) |
| Long-context retrieval | Hybrid seed chunks expanded with neighboring chunks, then packed into a token budget |
| Contextual retrieval | A short Ollama-generated document/section prefix is stored and embedded with each chunk |
| LLM synthesis | Retrieved chunks are labeled `[S1]`, `[S2]`, etc. and passed to a local chat model |
| Summarization/reasoning | The prompt asks the model to synthesize evidence across retrieved sources |
| Output validation | A second Ollama call audits support and citation coverage and returns structured JSON |
| Auditability | Answer citations map to PDF filename, page, and chunk; indexed metadata is retained in PostgreSQL |

PostgreSQL full-text search uses `ts_rank_cd`, which is BM25-like lexical ranking rather than the exact BM25 formula. The learning point is the same: fuse a lexical ranker with a dense ranker without mixing incomparable raw scores.

## Architecture

```text
PDFs -> extract -> overlapping chunks -> optional contextual prefix
   -> Ollama embeddings -> PostgreSQL (pgvector + tsvector)

question -> vector rank + lexical rank -> reciprocal rank fusion
         -> optional neighbor expansion/token budget
         -> cited Ollama answer -> optional second-model validation
```

## Prerequisites

- Python 3.11+
- Docker with Compose
- [Ollama](https://ollama.com/) running locally

## Quick start

```bash
git clone git@github.com:krishnadheerajkrovi/mastering_rag.git
cd mastering_rag
cp .env.example .env
make setup
make models
make db-up
make pdfs
make ingest
make demo
```

If Ollama is not already running, start it in another terminal with `ollama serve`.

The database schema is applied automatically only when Docker creates a fresh volume. To reset all local database data and reapply the DDL:

```bash
docker compose down -v
docker compose up -d --wait
```

## Run the examples

```bash
.venv/bin/python examples/01_hybrid_retrieval.py
.venv/bin/python examples/02_long_context_retrieval.py
.venv/bin/python examples/03_contextual_retrieval.py
.venv/bin/python examples/04_generation_and_validation.py
```

Or use the CLI:

```bash
# Compare retrieval modes
.venv/bin/python -m mastering_rag.cli search "deployment approval" --mode vector
.venv/bin/python -m mastering_rag.cli search "deployment approval" --mode hybrid
.venv/bin/python -m mastering_rag.cli search "deployment approval" --mode long_context

# Generate a cited answer, then run a separate validation pass
.venv/bin/python -m mastering_rag.cli ask \
  "What controls protect Acme's production deployments?" \
  --mode hybrid --top-k 5 --validate
```

## Contextual ingestion

Normal ingestion embeds each raw chunk. Contextual ingestion first asks the local chat model for a concise prefix describing where the chunk belongs, then stores and embeds `prefix + chunk`:

```bash
.venv/bin/python -m mastering_rag.cli ingest data/pdfs --contextualize
```

This makes extra LLM calls at indexing time. It is useful when chunks are ambiguous out of context, but slower than normal ingestion. Re-ingestion is idempotent by source filename and replaces that document's old chunks.

## SQL files

- `sql/001_schema.sql` is the DDL: extension, document/chunk tables, generated full-text columns, HNSW vector index, GIN lexical index, and document-order index.
- `sql/002_dml_examples.sql` contains inspection, lexical query, vector-query template, and cleanup examples.

Run the DML examples with:

```bash
docker compose exec -T postgres psql -U rag -d rag < sql/002_dml_examples.sql
```

The schema fixes vectors at 768 dimensions for `nomic-embed-text`. If you choose another embedding model, change both `EMBEDDING_DIM` in `.env` and `vector(768)` in `sql/001_schema.sql`, then recreate the database volume.

## Retrieval details

**Hybrid retrieval.** The code retrieves a larger candidate pool independently from pgvector and PostgreSQL full-text search. RRF combines ranks using `1 / (60 + rank)`, rewarding chunks that appear in both lists while avoiding raw-score calibration.

**Long-context retrieval.** The top hybrid hits become seeds. Adjacent chunks from the same document are included in document order until the configured approximate token budget is full. This provides broader context without blindly sending the entire corpus to the model.

**Contextual retrieval.** Each chunk can receive a short prefix generated from its document title, a document excerpt, and the chunk. Both the prefix and original text participate in lexical and semantic retrieval; the raw chunk remains separately available for citations.

**Generation and validation.** The generator is instructed to use only labeled evidence and cite it inline. Validation is deliberately a separate call and returns JSON. Treat it as a signal, not proof: for high-stakes systems, add deterministic claim checks and human review.

## Tests

The fast unit tests do not require Docker or Ollama:

```bash
make test
```

They cover chunk overlap/page tracking and reciprocal rank fusion. The end-to-end commands above exercise the actual local services.

## Production notes

- Authenticate and authorize access before retrieval; this demo has no tenant filtering.
- Store content hashes and model/prompt versions for reproducibility.
- Add retries, batching, observability, evaluation sets, and backup/restore policies.
- Never treat an LLM judge as the sole validation mechanism in medicine, law, finance, or safety-critical workflows.
- Tune chunk size, overlap, candidate pool, RRF constant, and top-k using labeled evaluation data.

## Project layout

```text
mastering_rag/
├── data/pdfs/                  # generated synthetic fixtures
├── examples/                   # one runnable file per concept
├── mastering_rag/              # ingestion, retrieval, generation, validation
├── scripts/create_dummy_pdfs.py
├── sql/001_schema.sql          # DDL
├── sql/002_dml_examples.sql    # DML/query examples
├── tests/
├── docker-compose.yml
├── Makefile
└── README.md
```

## License

MIT
