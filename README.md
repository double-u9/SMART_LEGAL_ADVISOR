
# 🏛️ المستشار القانوني الذكي — Smart Legal Advisor

Enterprise-grade AI legal assistant for Iraqi law. Powered by **local Ollama** — no cloud APIs, no costs.

## ✨ Features

- 🔍 **Hybrid Search**: Semantic (BGE-M3) + BM25 keyword search with Reciprocal Rank Fusion
- 📚 **Citation-Aware**: Every answer cites book, article, and page number
- 🌐 **Arabic NLP**: Full Arabic normalization, tokenization, and OCR support
- ⚡ **Streaming**: Real-time SSE token streaming for responsive answers
- 🔒 **Secure**: Prompt injection detection, rate limiting, input validation
- 🖥️ **100% Local**: Ollama LLM + Qdrant vector DB — everything runs on your machine

## 📦 Architecture

```
┌─────────────────────────────────────────────────┐
│                   Frontend (Next.js)            │
│         Premium dark UI • RTL Arabic            │
├─────────────────────────────────────────────────┤
│                   FastAPI Backend               │
│   Query → Retrieve → Rerank → Cite → Generate  │
├──────────┬──────────┬──────────┬────────────────┤
│  Qdrant  │  BM25    │ BGE-M3   │  Ollama (LLM)  │
│ Vectors  │ Keywords │ Embeddings│  llama3.1      │
└──────────┴──────────┴──────────┴────────────────┘
```

## 🚀 Quick Start

### Prerequisites

1. **Python 3.10+**
2. **Node.js 18+**
3. **Docker** (for Qdrant)
4. **Ollama** — [Download](https://ollama.com)

### Step 1: Install Ollama & Pull Model

```bash
# Install Ollama from https://ollama.com
ollama pull llama3.1
```

### Step 2: Start Qdrant

```bash
docker compose up -d
```

### Step 3: Install Backend

```bash
pip install -r requirements.txt
```

### Step 4: Ingest Legal Dataset

```bash
python scripts/ingest_data.py
```

### Step 5: Start Backend

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 6: Install & Start Frontend

```bash
cd frontend
npm install
npm run dev
```

### Or: One-Click Start

```bash
start.bat
```

Open **http://localhost:3000** 🎉

## 📖 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/query` | Legal Q&A with citations (supports SSE streaming) |
| POST | `/api/retrieve` | Raw retrieval without LLM |
| GET | `/api/health` | System health check |
| GET | `/api/books` | List available law books |
| GET | `/api/citations/{id}` | Citation details |
| POST | `/api/ingest/dataset` | Trigger data ingestion |

## 📚 Legal Books Included

- قانون العقوبات العراقي (Iraqi Penal Code)
- القانون المدني العراقي (Iraqi Civil Code)
- قانون الأحوال الشخصية (Personal Status Law)
- قانون المرافعات المدنية (Civil Procedure Law)
- قانون أصول المحاكمات الجزائية (Criminal Procedure Law)
- قانون العمل العراقي (Iraqi Labor Law)

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| LLM | Ollama (llama3.1) |
| Embeddings | BAAI/bge-m3 (1024-dim) |
| Reranker | BAAI/bge-reranker-v2-m3 |
| Vector DB | Qdrant |
| Backend | FastAPI + Python 3.10+ |
| Frontend | Next.js 14 + Tailwind CSS |
| Keyword Search | BM25 (rank-bm25) |

## 📁 Project Structure

```
smart legal advisor/
├── backend/
│   ├── api/           # FastAPI routes & middleware
│   ├── rag/           # RAG engine, prompts, Ollama integration
│   ├── ingestion/     # PDF processing, chunking, cleaning
│   ├── embeddings/    # BGE-M3 embedding service
│   ├── retrieval/     # Vector search, BM25, hybrid retriever
│   ├── reranking/     # BGE cross-encoder reranker
│   ├── citations/     # Citation extraction & formatting
│   ├── configs/       # Pydantic settings
│   ├── utils/         # Arabic NLP, logging, validators
│   └── main.py        # FastAPI app entry point
├── frontend/
│   ├── app/           # Next.js pages & layout
│   ├── components/    # React components
│   ├── hooks/         # Custom hooks (useChat)
│   ├── services/      # API service layer
│   └── types/         # TypeScript interfaces
├── scripts/           # Standalone ingestion script
├── docker-compose.yml # Qdrant container
├── requirements.txt   # Python dependencies
├── start.bat          # One-click startup
└── .env               # Configuration
```

---

**⚖️ Disclaimer**: This is an AI assistant for legal reference only. Always consult a qualified lawyer for legal advice.
