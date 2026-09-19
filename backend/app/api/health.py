import os
import asyncio
import logging
from typing import Dict, Any
from fastapi import APIRouter
from ..config import settings
from ..services.llm import LLMService
from ..services.rag import RAGService

logger = logging.getLogger("sahayak.health")

router = APIRouter(tags=["Health & Diagnostics"])

@router.get("/health/llm")
@router.get("/api/health/llm")
async def health_llm() -> Dict[str, Any]:
    """
    Live diagnostic endpoint verifying configured AI providers and embedding capabilities.
    Executes a bounded live ping to each provider with zero key leakage.
    """
    providers_result: Dict[str, str] = {}
    provider_list = [p.strip().lower() for p in settings.LLM_PROVIDER_ORDER.split(",") if p.strip()]
    if not provider_list:
        provider_list = ["gemini", "groq", "anthropic"]

    for provider in provider_list:
        key = ""
        if provider == "gemini":
            key = settings.GEMINI_API_KEY
        elif provider == "groq":
            key = settings.GROQ_API_KEY
        elif provider == "anthropic":
            key = settings.ANTHROPIC_API_KEY

        if not key or len(key.strip()) < 5:
            providers_result[provider] = "unconfigured"
            continue

        try:
            # 6-second live probe ping
            async def _probe(p: str) -> str:
                if p == "gemini":
                    return await LLMService._call_gemini("You are a health check.", "Reply with the single word OK.", 0.0)
                elif p == "groq":
                    return await LLMService._call_groq("You are a health check.", "Reply with the single word OK.", 0.0)
                elif p == "anthropic":
                    return await LLMService._call_anthropic("You are a health check.", "Reply with the single word OK.", 0.0)
                return ""

            probe_resp = await asyncio.wait_for(_probe(provider), timeout=6.0)
            if probe_resp and len(probe_resp.strip()) > 0:
                providers_result[provider] = "live"
            else:
                providers_result[provider] = "error"
        except Exception as e:
            logger.warning(f"[Health] Provider {provider} health probe failed: {e}")
            providers_result[provider] = "error"

    # Embedding Diagnostic
    embeddings_status = "deterministic"
    try:
        if settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 5 and settings.EMBEDDING_PROVIDER.lower() == "gemini":
            # Test embedding call
            emb = RAGService.generate_embedding("healthcheck")
            if emb and len(emb) == 768:
                embeddings_status = "live"
    except Exception as e:
        logger.warning(f"[Health] Embedding probe error: {e}")
        embeddings_status = "deterministic"

    # Media Dir Writable Diagnostic
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    media_dir = os.path.join(backend_dir, settings.MEDIA_DIR)
    media_writable = False
    try:
        os.makedirs(media_dir, exist_ok=True)
        test_file = os.path.join(media_dir, ".health_probe")
        with open(test_file, "w") as f:
            f.write("probe")
        if os.path.exists(test_file):
            os.remove(test_file)
            media_writable = True
    except Exception as e:
        logger.warning(f"[Health] Media directory write probe failed: {e}")
        media_writable = False

    return {
        "providers": providers_result,
        "embeddings": embeddings_status,
        "media_dir_writable": media_writable
    }
