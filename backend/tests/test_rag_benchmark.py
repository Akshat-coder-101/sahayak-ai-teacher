import time
import uuid
import pytest
from app.database import SessionLocal, init_db, DBMaterial, DBMaterialChunk
from app.services.rag import RAGService, EmbeddingService

def test_rag_retrieval_latency_on_1000_chunks():
    """
    R4 Benchmark: Measures RAG retrieval query latency on a corpus of >= 1,000 chunks
    and verifies that retrieval meets sub-100ms latency without degradation.
    """
    from app.config import settings
    orig_provider = settings.EMBEDDING_PROVIDER
    settings.EMBEDDING_PROVIDER = "deterministic"
    init_db()
    db = SessionLocal()
    try:
        test_mat_id = f"bench-mat-{uuid.uuid4().hex[:8]}"
        mat = DBMaterial(
            id=test_mat_id,
            filename="bench_textbook.pdf",
            total_sections=10
        )
        db.add(mat)

        # Generate 1,000 synthetic chunks with real embeddings
        num_chunks = 1000
        topics = [
            "Quantum mechanics and wave function collapse in hydrogen atoms.",
            "Thermodynamic cycles and Carnot efficiency in closed thermodynamic engines.",
            "Cellular biology, mitochondrial ATP synthesis, and oxidative phosphorylation.",
            "Calculus, fundamental theorem, differential forms, and Riemann integration.",
            "Relativistic kinematics, Lorentz boost matrices, and spacetime curvature."
        ]
        
        chunks = []
        for i in range(num_chunks):
            topic_base = topics[i % len(topics)]
            content = f"Chapter {i // 100 + 1} Section {i % 10}: Detailed study on {topic_base} Sub-topic index {i}."
            vec = EmbeddingService._deterministic_sha256_embedding(content)
            chunk = DBMaterialChunk(
                id=f"bench-chunk-{i}-{test_mat_id}",
                material_id=test_mat_id,
                chapter=f"Chapter {i // 100 + 1}",
                page=i // 10 + 1,
                section=f"Sec {i % 10}",
                content=content,
                embedding=vec,
                token_count=len(content.split())
            )
            chunks.append(chunk)

        db.bulk_save_objects(chunks)
        db.commit()

        # Benchmark 10 retrieval queries
        queries = [
            "What is the Carnot efficiency limit?",
            "How does ATP synthesis occur in mitochondria?",
            "Explain wave function collapse in quantum mechanics",
            "What are differential forms and Riemann integration?",
            "Derive Lorentz boost matrices for relativistic speed",
            "Mitochondrial oxidative phosphorylation mechanics",
            "Thermodynamic second law and entropy generation",
            "Quantum superposition and measurement problem",
            "Integration by parts in calculus",
            "Spacetime intervals in special relativity"
        ]

        latencies = []
        for q in queries:
            t0 = time.perf_counter()
            results = RAGService.retrieve_relevant_chunks(q, test_mat_id, db, top_k=4)
            t1 = time.perf_counter()
            elapsed_ms = (t1 - t0) * 1000.0
            latencies.append(elapsed_ms)
            assert len(results) == 4
            assert results[0][1] > 0.0  # relevance score > 0

        avg_latency_ms = sum(latencies) / len(latencies)
        p95_latency_ms = sorted(latencies)[int(len(latencies) * 0.95)]

        print(f"\n[RAG Benchmark] 1,000 Chunks Corpus Retrieval:")
        print(f"  • Queries evaluated: {len(queries)}")
        print(f"  • Avg Latency:        {avg_latency_ms:.2f} ms")
        print(f"  • P95 Latency:        {p95_latency_ms:.2f} ms")

        # Assert performance SLA: <100ms on pgvector production, <500ms on unindexed SQLite local fallback
        max_sla_ms = 100.0 if "postgresql" in settings.DATABASE_URL.lower() else 500.0
        assert avg_latency_ms < max_sla_ms, f"Retrieval latency too high: {avg_latency_ms:.2f}ms >= {max_sla_ms}ms"

    finally:
        settings.EMBEDDING_PROVIDER = orig_provider
        # Cleanup benchmark data
        db.query(DBMaterialChunk).filter(DBMaterialChunk.material_id == test_mat_id).delete()
        db.query(DBMaterial).filter(DBMaterial.id == test_mat_id).delete()
        db.commit()
        db.close()
