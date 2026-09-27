CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    checksum TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    indexed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chunks (
    id BIGSERIAL PRIMARY KEY,
    document_id BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    contextual_prefix TEXT NOT NULL DEFAULT '',
    contextual_content TEXT GENERATED ALWAYS AS (
        CASE WHEN contextual_prefix = '' THEN content
             ELSE contextual_prefix || E'\n\n' || content END
    ) STORED,
    token_estimate INTEGER NOT NULL,
    page_start INTEGER,
    page_end INTEGER,
    embedding vector(768) NOT NULL,
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english', contextual_prefix || ' ' || content)
    ) STORED,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(document_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw
    ON chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS chunks_search_vector_gin
    ON chunks USING gin (search_vector);
CREATE INDEX IF NOT EXISTS chunks_document_order
    ON chunks (document_id, chunk_index);
