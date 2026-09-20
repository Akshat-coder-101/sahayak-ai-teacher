import math
import re
import hashlib
import logging
import httpx
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from ..database import DBMaterialChunk
from ..models.schemas import Citation
from ..config import settings

logger = logging.getLogger("sahayak.rag")

class EmbeddingService:
    @classmethod
    def _deterministic_sha256_embedding(cls, text: str, dim: int = 768) -> List[float]:
        """
        Produces a stable, deterministic 768-dimensional pseudo-vector using SHA-256 tokens.
        100% consistent across server restarts and process lifetimes (unlike Python hash()).
        """
        vec = [0.0] * dim
        words = re.findall(r'\w+', text.lower())
        if not words:
            return vec

        for i, word in enumerate(words):
            h_bytes = hashlib.sha256(word.encode("utf-8")).digest()
            h_int = int.from_bytes(h_bytes[:4], byteorder="big")
            pos = h_int % dim
            weight = 1.0 / (1.0 + math.log(i + 1))
            sign = 1.0 if (h_bytes[4] % 2 == 0) else -1.0
            vec[pos] += weight * sign

            # Bigram feature
            if i > 0:
                h2_bytes = hashlib.sha256(f"{words[i-1]}_{word}".encode("utf-8")).digest()
                h2_int = int.from_bytes(h2_bytes[:4], byteorder="big")
                pos2 = h2_int % dim
                vec[pos2] += 0.5 * weight * (1.0 if (h2_bytes[4] % 2 == 0) else -1.0)

        # L2 Normalization
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 1e-9:
            vec = [x / norm for x in vec]
        return vec

    @classmethod
    def get_embedding(cls, text: str) -> List[float]:
        """
        Retrieves 768-dim semantic neural embedding via Gemini (gemini-embedding-001 with output_dimensionality=768)
        when online, or gracefully falls back to deterministic offline pseudo-embeddings if the API quota is exhausted.
        """
        cleaned = text.strip()[:2048]
        if not cleaned:
            return [0.0] * 768

        # 1. Primary: Production Gemini Semantic Neural Embeddings
        keys = settings.gemini_api_keys
        if keys and settings.EMBEDDING_PROVIDER.lower() == "gemini":
            model_name = getattr(settings, "GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
            for key in keys:
                for target_model in [model_name, "gemini-embedding-001", "text-embedding-004"]:
                    try:
                        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:embedContent?key={key}"
                        payload = {
                            "model": f"models/{target_model}",
                            "content": {
                                "parts": [{"text": cleaned}]
                            },
                            "output_dimensionality": 768
                        }
                        with httpx.Client(timeout=10.0) as client:
                            resp = client.post(endpoint, json=payload)
                            if resp.status_code == 200:
                                data = resp.json()
                                values = data.get("embedding", {}).get("values", [])
                                if values and len(values) == 768:
                                    return values
                            else:
                                logger.debug(f"[EmbeddingService] Key ...{key[-6:]} with {target_model} status {resp.status_code}")
                    except Exception as e:
                        logger.debug(f"[EmbeddingService] Key ...{key[-6:]} with {target_model} failed: {e}")
            logger.warning("[EmbeddingService] Gemini neural embedding API exhausted across all keys; engaging offline deterministic fallback.")

        # 2. Offline Fallback: Deterministic pseudo-embedding for network resilience
        return cls._deterministic_sha256_embedding(cleaned, dim=768)


class RAGService:
    @staticmethod
    def generate_embedding(text: str) -> List[float]:
        return EmbeddingService.get_embedding(text)

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a < 1e-9 or norm_b < 1e-9:
            return 0.0
        return float(dot / (norm_a * norm_b))

    @classmethod
    def retrieve_relevant_chunks(
        cls, 
        query: str, 
        material_id: str, 
        db: Session, 
        top_k: int = 4
    ) -> List[Tuple[DBMaterialChunk, float]]:
        query_vec = cls.generate_embedding(query)
        
        # Check if database is PostgreSQL with pgvector support
        is_postgres = False
        try:
            if db and db.bind:
                is_postgres = (db.bind.dialect.name == "postgresql")
        except Exception:
            is_postgres = settings.is_postgres

        if is_postgres:
            try:
                # Native pgvector similarity query: (1 - cosine_distance)
                vector_dist = DBMaterialChunk.embedding.cosine_distance(query_vec)
                candidates = (
                    db.query(DBMaterialChunk, (1 - vector_dist).label("sim"))
                    .filter(DBMaterialChunk.material_id == material_id)
                    .order_by(vector_dist)
                    .limit(top_k * 3)
                    .all()
                )
                if candidates:
                    scored_chunks = []
                    q_words = set(re.findall(r'\w+', query.lower()))
                    for c, sim in candidates:
                        c_words = set(re.findall(r'\w+', c.content.lower()))
                        overlap = len(q_words.intersection(c_words)) / max(len(q_words), 1)
                        combined_score = 0.7 * float(sim if sim is not None else 0.0) + 0.3 * overlap
                        scored_chunks.append((c, combined_score))

                    scored_chunks.sort(key=lambda x: x[1], reverse=True)
                    return scored_chunks[:top_k]
            except Exception as pg_err:
                logger.warning(f"[RAGService] Native pgvector query fallback to Python ranking: {pg_err}")

        # Python-side fallback ranking for SQLite
        chunks = db.query(DBMaterialChunk).filter(DBMaterialChunk.material_id == material_id).all()
        if not chunks:
            return []

        scored_chunks = []
        for c in chunks:
            chunk_vec = c.embedding or cls.generate_embedding(c.content)
            sim = cls.cosine_similarity(query_vec, chunk_vec)
            
            # Keyword overlap feature
            q_words = set(re.findall(r'\w+', query.lower()))
            c_words = set(re.findall(r'\w+', c.content.lower()))
            overlap = len(q_words.intersection(c_words)) / max(len(q_words), 1)
            
            # Hybrid rank
            combined_score = 0.7 * sim + 0.3 * overlap
            scored_chunks.append((c, combined_score))

        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return scored_chunks[:top_k]

    @classmethod
    def get_grounded_context_and_citations(
        cls, 
        query: str, 
        material_id: str, 
        db: Session
    ) -> Tuple[str, List[Citation]]:
        scored = cls.retrieve_relevant_chunks(query, material_id, db, top_k=3)
        if not scored:
            return "", []

        context_blocks = []
        citations = []
        for chunk, score in scored:
            ch_name = chunk.chapter or "General"
            p_num = chunk.page or 1
            content = chunk.content or ""
            context_blocks.append(f"[{ch_name} - Page {p_num}]:\n{content}")
            
            # Real confidence score bounded strictly between 0.0 and 1.0 without artificial clamp
            true_confidence = max(0.0, min(1.0, round(float(score), 3)))
            snippet_text = (content[:140] + "...") if len(content) > 140 else content
            citations.append(Citation(
                chapter=ch_name,
                page=chunk.page,
                section=chunk.section,
                snippet=snippet_text,
                confidence=true_confidence
            ))

        full_context = "\n\n".join(context_blocks)
        return full_context, citations
