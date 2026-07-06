"""Ollama-based response generator — local LLM, no API keys."""

from __future__ import annotations

import json
from typing import AsyncGenerator
import httpx
from backend.rag.prompt_templates import (
    SYSTEM_PROMPT,
    CONTEXT_TEMPLATE,
    QUERY_TEMPLATE,
    INSUFFICIENT_EVIDENCE,
)
from backend.utils.logging_config import get_logger

logger = get_logger("response_generator")


class ResponseGenerator:
    """Generate legal responses using local Ollama LLM."""

    def __init__(self, base_url: str = "http://localhost:11434",
                 model: str = "llama3.1", timeout: int = 120):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def _build_prompt(self, question: str, context: str) -> tuple[str, str]:
        """Build system prompt and user prompt."""
        system = SYSTEM_PROMPT
        user_prompt = CONTEXT_TEMPLATE.format(context=context)
        user_prompt += "\n\n" + QUERY_TEMPLATE.format(question=question)
        return system, user_prompt

    async def generate(self, question: str, context: str) -> str:
        """Generate a complete response (non-streaming)."""
        if not context or context.strip() == "لا توجد مصادر قانونية متاحة.":
            return INSUFFICIENT_EVIDENCE

        system, prompt = self._build_prompt(question, context)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": prompt},
                        ],
                        "stream": False,
                        "options": {
                            "temperature": 0.1,
                            "top_p": 0.9,
                            "num_predict": 2048,
                        },
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data.get("message", {}).get("content", INSUFFICIENT_EVIDENCE)

        except httpx.ConnectError:
            logger.error("Cannot connect to Ollama at %s", self.base_url)
            return "❌ خطأ: لا يمكن الاتصال بخدمة Ollama. تأكد من تشغيل Ollama محليًا."
        except Exception as e:
            logger.error("Generation failed: %s", e)
            return f"❌ خطأ في توليد الإجابة: {str(e)}"

    async def generate_stream(self, question: str, context: str) -> AsyncGenerator[str, None]:
        """Stream response tokens via Ollama API."""
        if not context or context.strip() == "لا توجد مصادر قانونية متاحة.":
            yield INSUFFICIENT_EVIDENCE
            return

        system, prompt = self._build_prompt(question, context)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": prompt},
                        ],
                        "stream": True,
                        "options": {
                            "temperature": 0.1,
                            "top_p": 0.9,
                            "num_predict": 2048,
                        },
                    },
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            data = json.loads(line)
                            token = data.get("message", {}).get("content", "")
                            if token:
                                yield token
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue

        except httpx.ConnectError:
            yield "❌ خطأ: لا يمكن الاتصال بخدمة Ollama. تأكد من تشغيل Ollama محليًا."
        except Exception as e:
            logger.error("Streaming failed: %s", e)
            yield f"❌ خطأ: {str(e)}"

    async def health_check(self) -> dict:
        """Check if Ollama is running and the model is available."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                resp.raise_for_status()
                models = resp.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                has_model = any(self.model in n for n in model_names)
                return {
                    "status": "ok",
                    "model": self.model,
                    "model_available": has_model,
                    "available_models": model_names,
                }
        except Exception as e:
            return {"status": "error", "error": str(e)}
