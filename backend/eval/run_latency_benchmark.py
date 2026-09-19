import os
import sys
import time
import json
import statistics
import asyncio
from typing import List, Dict, Any

# Ensure backend root is on sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.state_machine.teacher_agent import TeacherAgentStateMachine
from app.services.video import VideoService

def percentile(data: List[float], p: float) -> float:
    if not data:
        return 0.0
    k = (len(data) - 1) * p
    f = int(k)
    c = f + 1
    if c < len(data):
        return data[f] + (k - f) * (data[c] - data[f])
    return data[f]

async def run_latency_benchmarks():
    print("Running latency distribution benchmarks (10 iterations per pipeline)...")

    # 1. Lesson Planning Latency (Instruction Parsing + 3-segment Structured Plan)
    plan_latencies = []
    for i in range(10):
        t0 = time.perf_counter()
        parsed = await TeacherAgentStateMachine.parse_student_instruction(
            instruction="Teach me photosynthesis and cellular respiration in simple steps",
            filename="photosynthesis_chapter.pdf",
            available_chapters=["Chapter 1: Photosynthesis", "Chapter 2: Respiration"]
        )
        plan_latencies.append(time.perf_counter() - t0)

    plan_latencies.sort()
    p50_plan = percentile(plan_latencies, 0.50)
    p95_plan = percentile(plan_latencies, 0.95)

    # 2. Scene Visual Slide Generation Latency (Pillow image creation, antialiased text, layout composition)
    visual_latencies = []
    temp_img = os.path.join(os.path.dirname(__file__), "temp_slide.png")
    temp_chart = os.path.join(os.path.dirname(__file__), "temp_chart.png")

    for i in range(10):
        t0 = time.perf_counter()
        VideoService._render_chart(
            concept="Light Reactions & Photolysis",
            visual_spec={"type": "labeled-diagram"},
            output_path=temp_chart,
            stage_idx=i
        )
        VideoService._create_scene_slide(
            output_image_path=temp_img,
            concept=f"Photolysis of Water Iteration {i}",
            visual_spec={"type": "labeled-diagram"},
            bullet_points=[
                "Photolysis splits H2O into protons, electrons, and oxygen gas.",
                "Electron transport chain drives ATP synthase across thylakoid lumen.",
                "Chlorophyll reflects green light (500-550nm) to human eyes."
            ],
            active_bullet_idx=i % 3,
            scene_title="Bioenergetics of Life"
        )
        visual_latencies.append(time.perf_counter() - t0)

    for temp_f in [temp_img, temp_chart]:
        if os.path.exists(temp_f):
            os.remove(temp_f)

    visual_latencies.sort()
    p50_visual = percentile(visual_latencies, 0.50)
    p95_visual = percentile(visual_latencies, 0.95)

    results = {
        "iterations": 10,
        "lesson_planning": {
            "p50_seconds": round(p50_plan, 4),
            "p95_seconds": round(p95_plan, 4),
            "min_seconds": round(min(plan_latencies), 4),
            "max_seconds": round(max(plan_latencies), 4)
        },
        "scene_visual_generation": {
            "p50_seconds": round(p50_visual, 4),
            "p95_seconds": round(p95_visual, 4),
            "min_seconds": round(min(visual_latencies), 4),
            "max_seconds": round(max(visual_latencies), 4)
        }
    }

    out_file = os.path.join(os.path.dirname(__file__), "latency_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 65)
    print("LATENCY DISTRIBUTION BENCHMARK RESULTS")
    print("=" * 65)
    print(f"Lesson Planning Latency:       p50 = {round(p50_plan * 1000, 1)}ms | p95 = {round(p95_plan * 1000, 1)}ms")
    print(f"Scene Visual Slide Synthesis:  p50 = {round(p50_visual * 1000, 1)}ms | p95 = {round(p95_visual * 1000, 1)}ms")
    print("=" * 65 + "\n")
    return results

if __name__ == "__main__":
    asyncio.run(run_latency_benchmarks())
