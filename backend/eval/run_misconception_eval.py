import os
import sys
import json
import asyncio
from typing import Dict, Any, List

# Ensure backend root is on sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.database import SessionLocal, init_db, DBLessonSession
from app.services.evaluator import EvaluatorService

CLASSES = ["correct", "partially_correct", "misconception", "no_understanding"]

async def run_misconception_benchmark():
    init_db()
    db = SessionLocal()
    
    dataset_path = os.path.join(os.path.dirname(__file__), "misconceptions_dataset.json")
    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset: List[Dict[str, Any]] = json.load(f)

    # Use or create a dedicated benchmark session
    bench_session_id = "session-bench-misconception"
    session = db.query(DBLessonSession).filter(DBLessonSession.id == bench_session_id).first()
    if not session:
        session = DBLessonSession(
            id=bench_session_id,
            topic="General Science Benchmark",
            language="en",
            plan_json={
                "segments": [
                    {
                        "id": 1,
                        "concept": "Scientific Reasoning",
                        "checkpoint_question": {
                            "question": "General concept question",
                            "correct_answer": "Standard verified answer"
                        }
                    }
                ]
            }
        )
        db.add(session)
        db.commit()

    results = []
    confusion_matrix = {true_cls: {pred_cls: 0 for pred_cls in CLASSES} for true_cls in CLASSES}
    
    print(f"Running misconception classification benchmark across {len(dataset)} student answers...")

    for item in dataset:
        # Dynamically set session question and correct answer for this item
        session.topic = item["concept"]
        session.plan_json = {
            "segments": [
                {
                    "id": 1,
                    "concept": item["concept"],
                    "checkpoint_question": {
                        "question": item["question"],
                        "correct_answer": item["correct_answer"]
                    }
                }
            ]
        }
        db.commit()

        # Run through EvaluatorService
        eval_res = await EvaluatorService.evaluate_student_answer(
            session_id=bench_session_id,
            segment_id=1,
            student_answer=item["student_answer"],
            is_demo_mode=False,
            force_misconception=False,
            db=db
        )

        pred_classification = (eval_res.classification or "no_understanding").lower()
        
        # Normalize classification name to standard taxonomy
        if pred_classification in ["advance", "mastery", "correct"]:
            normalized_pred = "correct"
        elif pred_classification in ["adapt", "misconception"]:
            normalized_pred = "misconception"
        elif pred_classification in ["partial", "partially_correct", "hint"]:
            normalized_pred = "partially_correct"
        else:
            normalized_pred = "no_understanding"

        expected = item["expected_classification"]
        if expected in confusion_matrix and normalized_pred in confusion_matrix[expected]:
            confusion_matrix[expected][normalized_pred] += 1

        is_match = (normalized_pred == expected)
        results.append({
            "id": item["id"],
            "subject": item["subject"],
            "question": item["question"],
            "student_answer": item["student_answer"],
            "expected": expected,
            "predicted": normalized_pred,
            "match": is_match,
            "feedback": eval_res.feedback
        })

    total = len(dataset)
    matches = sum(1 for r in results if r["match"])
    accuracy = (matches / total) * 100 if total > 0 else 0.0

    # Misconception class metrics
    misc_tp = confusion_matrix["misconception"]["misconception"]
    misc_fp = sum(confusion_matrix[cls]["misconception"] for cls in CLASSES if cls != "misconception")
    misc_fn = sum(confusion_matrix["misconception"][cls] for cls in CLASSES if cls != "misconception")

    precision = (misc_tp / (misc_tp + misc_fp) * 100) if (misc_tp + misc_fp) > 0 else 0.0
    recall = (misc_tp / (misc_tp + misc_fn) * 100) if (misc_tp + misc_fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    output_data = {
        "total_samples": total,
        "matched": matches,
        "overall_accuracy_percent": round(accuracy, 2),
        "misconception_metrics": {
            "true_positives": misc_tp,
            "false_positives": misc_fp,
            "false_negatives": misc_fn,
            "precision_percent": round(precision, 2),
            "recall_percent": round(recall, 2),
            "f1_score": round(f1, 2)
        },
        "confusion_matrix": confusion_matrix,
        "details": results
    }

    out_file = os.path.join(os.path.dirname(__file__), "misconception_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    print("\n" + "=" * 65)
    print("MISCONCEPTION CLASSIFICATION BENCHMARK COMPLETE")
    print("=" * 65)
    print(f"Total Samples:            {total}")
    print(f"Overall Accuracy:         {round(accuracy, 2)}%")
    print(f"Misconception Precision:  {round(precision, 2)}%")
    print(f"Misconception Recall:     {round(recall, 2)}%")
    print(f"Misconception F1-Score:   {round(f1, 2)}%")
    print("Confusion Matrix:")
    print(f"  Expected \\ Predicted | " + " | ".join([c[:7] for c in CLASSES]))
    for true_c in CLASSES:
        row = " | ".join([str(confusion_matrix[true_c][pred_c]).rjust(7) for pred_c in CLASSES])
        print(f"  {true_c.ljust(20)} | {row}")
    print("=" * 65 + "\n")

    db.close()
    return output_data

if __name__ == "__main__":
    asyncio.run(run_misconception_benchmark())
