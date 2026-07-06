# Arabic Legal AI Dataset Pipeline

Production-grade dataset builder for Arabic legal books, optimized for RAG, semantic search, vector databases, source citation, and low-hallucination legal assistants.

The pipeline reads PDF, DOCX, and TXT files; detects scanned PDFs; extracts or OCRs text; cleans Arabic carefully; chunks by legal structure; generates metadata; exports dataset formats; and validates retrieval readiness.

## Project Structure

```text
legal-ai-dataset/
├── books/
├── extracted/
├── cleaned/
├── clean_text/
├── chunks/
├── metadata/
├── embeddings_ready/
├── vector_exports/
├── reports/
├── scripts/
├── configs/
├── tests/
├── legal_dataset.json
├── legal_dataset.jsonl
├── legal_dataset.csv
└── README.md
```

`clean_text/` is kept as a compatibility output for systems expecting that exact folder name. `cleaned/` is the canonical project folder.

## Installation

```powershell
cd "C:\Users\moham\Desktop\law books\legal-ai-dataset"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If you use the bundled Codex runtime, replace `python` with:

```powershell
& "C:\Users\moham\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
```

## OCR Setup

For scanned Arabic PDFs, install Tesseract with Arabic language data.

Windows:

1. Install Tesseract OCR from the UB Mannheim Windows builds.
2. During installation, include Arabic language data.
3. Add the Tesseract installation directory to `PATH`.
4. Verify:

```powershell
tesseract --list-langs
```

The output should include `ara` and preferably `eng`.

EasyOCR is also supported by the code path:

```powershell
python -m pip install easyocr
```

For production Arabic legal OCR, Tesseract with `ara+eng`, 300 DPI rendering, and manual inspection of low-confidence pages is recommended.

## Usage

Copy source files into `books/`, then run:

```powershell
python scripts/run_pipeline.py --books-dir books --output-dir . --config configs/pipeline.yaml --ocr auto
```

Useful variants:

```powershell
python scripts/run_pipeline.py --ocr false
python scripts/run_pipeline.py --verbose
```

## Pipeline

1. File analysis: detects format, pages, language, scanned PDFs, OCR need, extraction difficulty, and text quality.
2. Extraction: prefers PyMuPDF, then pdfplumber, then pypdf. OCR runs when a page has too little extractable text.
3. Arabic cleaning: applies Unicode normalization, removes extraction noise, preserves legal numbering and citations, and avoids aggressive semantic rewrites.
4. Legal chunking: chunks by book, chapter, section, article, and paragraph with target chunk sizes of 500-1200 tokens and overlap for long articles.
5. Metadata generation: adds page references, article numbers, summaries, keywords, legal topics, token counts, and previous/next chunk links.
6. Embedding preparation: creates citation-rich `embedding_ready_text` for vector indexing.
7. Quality control: validates empty chunks, duplicate chunks, OCR failures, metadata completeness, Arabic corruption, and broken references.

## Outputs

- `legal_dataset.json`
- `legal_dataset.jsonl`
- `legal_dataset.csv`
- `extracted/*.pages.json`
- `cleaned/*.txt`
- `clean_text/*.txt`
- `chunks/*.chunks.jsonl`
- `metadata/*.metadata.json`
- `embeddings_ready/legal_embeddings_ready.jsonl`
- `vector_exports/vector_records.jsonl`
- `reports/book_analysis_report.md`
- `reports/dataset_quality_report.md`
- `reports/embedding_model_recommendation.md`

Each dataset entry contains:

```json
{
  "id": "",
  "book_name": "",
  "chapter": "",
  "section": "",
  "article_number": "",
  "page_number": "",
  "language": "",
  "chunk_text": "",
  "summary": "",
  "keywords": [],
  "legal_topics": [],
  "embedding_ready_text": "",
  "source_file": "",
  "token_count": 0,
  "chunk_index": 0,
  "previous_chunk_id": "",
  "next_chunk_id": ""
}
```

## Embedding Model Recommendation

Default recommendation: `BAAI/bge-m3`.

Why: Arabic legal retrieval benefits from both semantic and lexical matching. BGE-M3 supports multilingual retrieval, 1024-dimensional embeddings, long inputs up to 8192 tokens, and dense + sparse + multi-vector retrieval modes. That combination is valuable for exact article numbers, legal terms, and source-sensitive RAG.

Recommended evaluation stack:

- Primary: `BAAI/bge-m3`
- Baseline: `intfloat/multilingual-e5-large`
- Long-context experiment: `jinaai/jina-embeddings-v3`
- Managed API baseline: `text-embedding-3-large`

Primary references:

- [BGE-M3 model card](https://huggingface.co/BAAI/bge-m3)
- [Multilingual-E5-large model card](https://huggingface.co/intfloat/multilingual-e5-large)
- [Jina embeddings v3 model card](https://huggingface.co/jinaai/jina-embeddings-v3)
- [OpenAI text-embedding-3-large docs](https://developers.openai.com/api/docs/models/text-embedding-3-large)

## Vector Database Integration

Ready-to-use loaders are provided in `vector_exports/`:

```powershell
cd vector_exports
python chroma_loader.py --records vector_records.jsonl
python faiss_loader.py --records vector_records.jsonl
python qdrant_loader.py --records vector_records.jsonl --url http://localhost:6333
python weaviate_loader.py --records vector_records.jsonl
python pinecone_loader.py --records vector_records.jsonl
```

For legal RAG, use hybrid retrieval where possible:

1. Dense vector retrieval from `embedding_ready_text`.
2. Lexical/BM25 retrieval over normalized Arabic text.
3. Reranking with a multilingual/legal reranker.
4. Answer generation only from retrieved chunks, with page and article citations.

## Future RAG Integration

Recommended answer contract:

- Always cite `book_name`, `page_number`, and `article_number` when available.
- If retrieved context is weak or contradictory, answer with uncertainty instead of guessing.
- Keep `chunk_text` as the authoritative source and use `summary` only for preview.
- Use `previous_chunk_id` and `next_chunk_id` to expand context around close matches.

Recommended retrieval metrics:

- Recall@5
- MRR@10
- citation accuracy
- duplicate hit rate
- unsupported answer rate

## Quality Notes

Legal text must not be over-cleaned. The pipeline uses a light display-normalization path for `chunk_text` and a stronger normalization path only in `embedding_ready_text`. This keeps citations and article numbers intact while improving semantic search.

