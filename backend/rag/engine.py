"""RAG Engine — main orchestrator for the legal assistant pipeline."""

from __future__ import annotations

import json
from typing import AsyncGenerator, Optional
from backend.retrieval.hybrid_retriever import HybridRetriever
from backend.reranking.reranker import Reranker
from backend.citations.citation_engine import CitationEngine, Citation
from backend.rag.response_generator import ResponseGenerator
from backend.utils.arabic_utils import normalize_for_search
from backend.utils.logging_config import get_logger

logger = get_logger("rag_engine")


class RAGEngine:
    """Main RAG orchestrator: query → retrieve → rerank → cite → generate."""

    def __init__(
        self,
        retriever: HybridRetriever,
        reranker: Reranker,
        citation_engine: CitationEngine,
        response_generator: ResponseGenerator,
        top_k_retrieval: int = 20,
        top_k_rerank: int = 5,
    ):
        self.retriever = retriever
        self.reranker = reranker
        self.citation_engine = citation_engine
        self.generator = response_generator
        self.top_k_retrieval = top_k_retrieval
        self.top_k_rerank = top_k_rerank

    async def query(
        self,
        question: str,
        filters: Optional[dict] = None,
    ) -> dict:
        """Full RAG pipeline — returns complete response with citations.

        Returns:
            {answer, citations, query, confidence}
        """
        logger.info("RAG query: %s", question[:80])

        # 1. Hybrid retrieval
        retrieved = self.retriever.search(
            query=question,
            top_k=self.top_k_retrieval,
            filters=filters,
        )

        if not retrieved:
            logger.warning("No documents retrieved for query")
            return {
                "answer": "⚠️ لم يتم العثور على نتائج مطابقة في الكتب القانونية المتاحة.",
                "citations": [],
                "query": question,
                "confidence": 0.0,
            }

        # 2. Rerank
        reranked = self.reranker.rerank(
            query=question,
            documents=retrieved,
            top_k=self.top_k_rerank,
        )

        # 3. Extract citations
        citations = self.citation_engine.extract_citations(reranked)

        # 4. Build context for LLM
        context = self.citation_engine.format_context_for_llm(citations)

        # 5. Generate response
        answer = await self.generator.generate(question, context)

        # 6. Compute confidence
        confidence = self._compute_confidence(reranked, citations)

        return {
            "answer": answer,
            "citations": [c.to_dict() for c in citations],
            "query": question,
            "confidence": confidence,
        }

    async def query_stream(
        self,
        question: str,
        filters: Optional[dict] = None,
    ) -> AsyncGenerator[str, None]:
        """Streaming RAG pipeline — yields SSE events.

        Event types:
          - {"type": "status", "content": "..."} — progress updates
          - {"type": "citation", "content": {...}} — citation data
          - {"type": "token", "content": "..."} — response token
          - {"type": "done", "content": ""} — stream complete
        """
        logger.info("RAG stream query: %s", question[:80])

        # Status: searching
        yield self._sse_event("status", "جاري البحث في الكتب القانونية...")

        # 1. Hybrid retrieval
        retrieved = self.retriever.search(
            query=question,
            top_k=self.top_k_retrieval,
            filters=filters,
        )

        if not retrieved:
            yield self._sse_event("token", "⚠️ لم يتم العثور على نتائج مطابقة في الكتب القانونية المتاحة.")
            yield self._sse_event("done", "")
            return

        # Status: reranking
        yield self._sse_event("status", "جاري تحليل النتائج وترتيبها...")

        # 2. Rerank
        reranked = self.reranker.rerank(
            query=question,
            documents=retrieved,
            top_k=self.top_k_rerank,
        )

        # 3. Extract & send citations
        citations = self.citation_engine.extract_citations(reranked)
        for citation in citations:
            yield self._sse_event("citation", citation.to_dict())

        # 4. Build context
        context = self.citation_engine.format_context_for_llm(citations)

        # Status: generating
        yield self._sse_event("status", "جاري صياغة الإجابة القانونية...")

        # 5. Stream response tokens
        async for token in self.generator.generate_stream(question, context):
            yield self._sse_event("token", token)

        yield self._sse_event("done", "")

    def _compute_confidence(self, reranked: list[dict], citations: list[Citation]) -> float:
        """Estimate answer confidence from retrieval/rerank scores."""
        if not reranked:
            return 0.0

        scores = []
        for doc in reranked:
            s = doc.get("rerank_score", doc.get("hybrid_score", doc.get("score", 0)))
            scores.append(float(s))

        if not scores:
            return 0.0

        avg_score = sum(scores) / len(scores)
        # Normalize to 0-1 range (rerank scores can vary)
        confidence = min(1.0, max(0.0, avg_score))
        return round(confidence, 3)

    @staticmethod
    def _sse_event(event_type: str, content) -> str:
        """Format an SSE event as JSON string."""
        return json.dumps({"type": event_type, "content": content}, ensure_ascii=False)
