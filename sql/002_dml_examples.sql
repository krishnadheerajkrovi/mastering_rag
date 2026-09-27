-- Inspect indexed documents and their chunk counts.
SELECT d.id, d.title, d.source, count(c.id) AS chunks, d.indexed_at
FROM documents d
LEFT JOIN chunks c ON c.document_id = d.id
GROUP BY d.id
ORDER BY d.id;

-- BM25-like PostgreSQL full-text ranking. Replace the phrase as needed.
SELECT c.id, d.title,
       ts_rank_cd(c.search_vector, websearch_to_tsquery('english', 'deployment approval')) AS score,
       left(c.contextual_content, 180) AS preview
FROM chunks c
JOIN documents d ON d.id = c.document_id
WHERE c.search_vector @@ websearch_to_tsquery('english', 'deployment approval')
ORDER BY score DESC
LIMIT 5;

-- Vector search template. Replace the zero vector with a real Ollama embedding.
-- SELECT id, content, 1 - (embedding <=> '[0, ...]'::vector) AS similarity
-- FROM chunks ORDER BY embedding <=> '[0, ...]'::vector LIMIT 5;

-- Safe cleanup when you want to re-run ingestion manually.
-- TRUNCATE chunks, documents RESTART IDENTITY CASCADE;
