# Embedding Model Recommendation For Arabic Legal RAG

## Recommendation

Use `BAAI/bge-m3` as the default local/open-source embedding model for this corpus. It is the best fit for Arabic legal retrieval because it combines multilingual dense retrieval with sparse lexical weights and ColBERT-style multi-vector scoring. That matters for law: exact article numbers, procedural phrases, and named legal institutions often need lexical recall as much as semantic recall.

For a managed API baseline, use `text-embedding-3-large` and evaluate it against `bge-m3` on a small Arabic legal benchmark. It is strong and simple to operate, but it does not provide BGE-M3's native hybrid dense/sparse/multi-vector modes.

## Comparison

| Model | Strengths | Limits | Best use |
|---|---|---|---|
| `BAAI/bge-m3` | Multilingual, 1024 dimensions, up to 8192 tokens, dense + sparse + multi-vector retrieval | Heavier local serving than E5; best results may need FlagEmbedding-specific code | Default for Arabic legal RAG and hybrid retrieval |
| `intfloat/multilingual-e5-large` | Mature multilingual SentenceTransformers model, 1024 dimensions, strong Arabic score on Mr. TyDi | 512 token max in the model card; requires `query:` / `passage:` prefixes | Lightweight dense-only baseline |
| `jinaai/jina-embeddings-v3` | Multilingual, long-context up to 8192 tokens, task adapters | Requires `trust_remote_code` in common HF usage; API/local behavior should be pinned | Long-context experiments and late chunking |
| `text-embedding-3-large` | Managed API, strong English and non-English embedding model, easy ops | External API cost/data-governance considerations; dense-only | Production API baseline or low-maintenance deployment |

## Evaluation Plan

1. Create 50-100 Arabic legal queries with known source articles.
2. Measure Recall@5, MRR@10, citation accuracy, and false positive rate.
3. Compare dense-only against hybrid BM25 + dense retrieval.
4. Use a reranker for final answer contexts, especially for similar article language.

## Sources

- BGE-M3 model card: https://huggingface.co/BAAI/bge-m3
- Multilingual-E5-large model card: https://huggingface.co/intfloat/multilingual-e5-large
- Jina embeddings v3 model card: https://huggingface.co/jinaai/jina-embeddings-v3
- OpenAI text-embedding-3-large docs: https://developers.openai.com/api/docs/models/text-embedding-3-large
