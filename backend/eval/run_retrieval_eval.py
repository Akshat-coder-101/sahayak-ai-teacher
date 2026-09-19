import os
import sys
import json
import re
from typing import Dict, Any, List

# Ensure backend root is on sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.database import SessionLocal, init_db, DBMaterialChunk
from app.services.rag import RAGService, EmbeddingService

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = sum(a * a for a, b in zip(v1, v2)) ** 0.5
    norm2 = sum(b * b for a, b in zip(v1, v2)) ** 0.5
    return dot / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0.0

def run_retrieval_benchmark():
    init_db()
    db = SessionLocal()

    dataset_path = os.path.join(os.path.dirname(__file__), "retrieval_dataset.json")
    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset: List[Dict[str, Any]] = json.load(f)

    # Fetch candidate chunks from demo material
    all_chunks = db.query(DBMaterialChunk).filter(DBMaterialChunk.material_id == "doc-demo-photosynthesis").all()
    if not all_chunks:
        # Fallback to all chunks in db
        all_chunks = db.query(DBMaterialChunk).all()

    print(f"Running retrieval evaluation on {len(dataset)} queries against {len(all_chunks)} candidate chunks...")

    vector_hits_at_1 = 0
    vector_hits_at_3 = 0
    vector_reciprocal_ranks = []

    hybrid_hits_at_1 = 0
    hybrid_hits_at_3 = 0
    hybrid_reciprocal_ranks = []

    query_details = []

    for item in dataset:
        query = item["query"]
        target_id = item["target_chunk_id"]

        q_vec = EmbeddingService.get_embedding(query)
        q_words = set(re.findall(r'\w+', query.lower()))

        vector_scores = []
        hybrid_scores = []

        for c in all_chunks:
            c_vec = c.embedding
            if not c_vec:
                c_vec = EmbeddingService.get_embedding(c.content)
            
            sim = cosine_similarity(q_vec, c_vec)
            
            c_words = set(re.findall(r'\w+', c.content.lower()))
            overlap = len(q_words.intersection(c_words)) / max(len(q_words), 1)

            # Pure vector score
            vector_scores.append((c.id, sim))
            
            # Hybrid score (0.7 vector + 0.3 lexical)
            hybrid_score = 0.7 * sim + 0.3 * overlap
            hybrid_scores.append((c.id, hybrid_score))

        # Rank candidates
        vector_scores.sort(key=lambda x: x[1], reverse=True)
        hybrid_scores.sort(key=lambda x: x[1], reverse=True)

        vec_ranked_ids = [x[0] for x in vector_scores]
        hyb_ranked_ids = [x[0] for x in hybrid_scores]

        # Evaluate Pure Vector
        vec_rank = (vec_ranked_ids.index(target_id) + 1) if target_id in vec_ranked_ids else 999
        if vec_rank == 1:
            vector_hits_at_1 += 1
        if vec_rank <= 3:
            vector_hits_at_3 += 1
        vector_reciprocal_ranks.append(1.0 / vec_rank if vec_rank <= len(all_chunks) else 0.0)

        # Evaluate Hybrid
        hyb_rank = (hyb_ranked_ids.index(target_id) + 1) if target_id in hyb_ranked_ids else 999
        if hyb_rank == 1:
            hybrid_hits_at_1 += 1
        if hyb_rank <= 3:
            hybrid_hits_at_3 += 1
        hybrid_reciprocal_ranks.append(1.0 / hyb_rank if hyb_rank <= len(all_chunks) else 0.0)

        query_details.append({
            "id": item["id"],
            "query": query,
            "target_chunk": target_id,
            "pure_vector_rank": vec_rank,
            "hybrid_rank": hyb_rank
        })

    n = len(dataset)
    vec_hit3_pct = (vector_hits_at_3 / n) * 100
    vec_hit1_pct = (vector_hits_at_1 / n) * 100
    vec_mrr = sum(vector_reciprocal_ranks) / n

    hyb_hit3_pct = (hybrid_hits_at_3 / n) * 100
    hyb_hit1_pct = (hybrid_hits_at_1 / n) * 100
    hyb_mrr = sum(hybrid_reciprocal_ranks) / n

    results = {
        "queries_evaluated": n,
        "candidate_chunks": len(all_chunks),
        "pure_vector": {
            "hit_at_1_percent": round(vec_hit1_pct, 2),
            "hit_at_3_percent": round(vec_hit3_pct, 2),
            "mean_reciprocal_rank": round(vec_mrr, 4)
        },
        "hybrid_0.7_vector_0.3_lexical": {
            "hit_at_1_percent": round(hyb_hit1_pct, 2),
            "hit_at_3_percent": round(hyb_hit3_pct, 2),
            "mean_reciprocal_rank": round(hyb_mrr, 4)
        },
        "delta": {
            "hit_at_1_improvement_percent": round(hyb_hit1_pct - vec_hit1_pct, 2),
            "hit_at_3_improvement_percent": round(hyb_hit3_pct - vec_hit3_pct, 2),
            "mrr_improvement": round(hyb_mrr - vec_mrr, 4)
        },
        "details": query_details
    }

    out_file = os.path.join(os.path.dirname(__file__), "retrieval_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 65)
    print("RETRIEVAL BENCHMARK: PURE VECTOR vs HYBRID (0.7/0.3)")
    print("=" * 65)
    print(f"Total Test Queries:               {n}")
    print(f"Pure Vector Search Hit@3:         {round(vec_hit3_pct, 2)}% (Hit@1: {round(vec_hit1_pct, 2)}%, MRR: {round(vec_mrr, 4)})")
    print(f"Hybrid (0.7/0.3) Search Hit@3:    {round(hyb_hit3_pct, 2)}% (Hit@1: {round(hyb_hit1_pct, 2)}%, MRR: {round(hyb_mrr, 4)})")
    print(f"Delta Hit@1 Improvement:          +{round(hyb_hit1_pct - vec_hit1_pct, 2)}%")
    print(f"Delta Hit@3 Improvement:          +{round(hyb_hit3_pct - vec_hit3_pct, 2)}%")
    print(f"Delta MRR Improvement:            +{round(hyb_mrr - vec_mrr, 4)}")
    print("=" * 65 + "\n")

    db.close()
    return results

if __name__ == "__main__":
    run_retrieval_benchmark()
