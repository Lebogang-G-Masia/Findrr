"""Benchmark the installed ML-001 and ML-002 bundles on this machine (CPU inference only).

Writes ``bench.json`` (latencies, load times, peak memory and sample outputs) to the output
directory. It runs real inference with the app's own runners and never trains anything.
Run it from the repo root with the project's virtual environment active:

    python scripts/model_dashboard/bench.py [--out build/model-dashboard] [--models-dir models]
"""

from __future__ import annotations

import argparse
import json
import os
import resource
import statistics
import time
from pathlib import Path

from findrr.ml.similarity_evaluator_runner import SimilarityEvaluatorRunner
from findrr.ml.title_expander_runner import TitleExpanderRunner

REPO = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
TE_REL = "title-expander/v2.0.0"
SE_REL = "similarity-evaluator/v1.1.0"

# Hand-picked public job titles: illustrations, not an evaluation set.
TE_CASES = [
    ("Software Developer", ["Python", "SQL", "Docker"], "ANY"),
    ("Registered Nurse", [], "ANY"),
    ("Data Analyst", ["Excel", "Tableau"], "ENTRY"),
    ("Electrician", [], "SENIOR"),
    ("Accountant", ["Excel"], "ANY"),
    ("Graphic Designer", ["Adobe Photoshop"], "ANY"),
    ("Truck Driver", [], "ANY"),
    ("Teacher", [], "ANY"),
    ("Chef", [], "LEAD"),
    ("Mechanical Engineer", ["AutoCAD"], "MID"),
]
SE_PAIRS = [
    ("Software Developer", "Software Engineer"),
    ("Software Developer", "Dental Assistant"),
    ("Data Analyst", "Business Intelligence Analyst"),
    ("Registered Nurse", "Staff Nurse"),
    ("Registered Nurse", "Truck Driver"),
    ("Accountant", "Bookkeeper"),
    ("Chef", "Line Cook"),
    ("Electrician", "Software Engineer"),
    ("Graphic Designer", "Visual Designer"),
    ("Teacher", "Mechanical Engineer"),
    ("Backend Engineer", "Python Developer"),
    ("Data Scientist", "Machine Learning Engineer"),
]
TE_REQUESTS = 50  # AC-ML-001.2: average over 50 benchmark requests
SE_REQUESTS = 100
BATCH_SIZE = 20  # spec: batch of 20 candidate pairs
BATCH_RUNS = 10
# Above this 1-minute load per CPU, other processes are competing and latencies are not
# representative. Provisional value: it only triggers a warning, never a pass or fail.
BUSY_LOAD_PER_CPU = 0.5


def stats(values: list[float]) -> dict:
    ordered = sorted(values)
    return {
        "mean_ms": round(statistics.mean(values), 1),
        "p50_ms": round(statistics.median(values), 1),
        "p95_ms": round(ordered[int(len(ordered) * 0.95) - 1], 1),
        "max_ms": round(max(values), 1),
    }


def peak_rss_mb() -> int:
    return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=HERE / "data")
    parser.add_argument("--models-dir", type=Path, default=REPO / "models")
    parser.add_argument(
        "--allow-busy", action="store_true", help="save the results even on a busy machine"
    )
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    cpus = os.cpu_count() or 1
    load_before = os.getloadavg()[0]

    te = TitleExpanderRunner(args.models_dir / TE_REL, "2.0.0")
    start = time.perf_counter()
    te.load()
    te_load = time.perf_counter() - start
    te_lat, te_samples = [], []
    for i in range(TE_REQUESTS):
        title, skills, level = TE_CASES[i % len(TE_CASES)]
        start = time.perf_counter()
        titles = te.expand(title, skills, level)
        ms = (time.perf_counter() - start) * 1000
        te_lat.append(ms)
        if i < len(TE_CASES):
            te_samples.append(
                {
                    "input_title": title,
                    "skills": ", ".join(skills) or "general",
                    "level": level,
                    "output": ", ".join(titles),
                    "n_titles": len(titles),
                    "latency_ms": round(ms, 1),
                }
            )
    rss_te = peak_rss_mb()

    se = SimilarityEvaluatorRunner(args.models_dir / SE_REL, "1.1.0")
    start = time.perf_counter()
    se.load()
    se_load = time.perf_counter() - start
    se_lat, se_samples = [], []
    for i in range(SE_REQUESTS):
        a, b = SE_PAIRS[i % len(SE_PAIRS)]
        start = time.perf_counter()
        score = se.evaluate_pair(a, b)
        se_lat.append((time.perf_counter() - start) * 1000)
        if i < len(SE_PAIRS):
            se_samples.append({"title_a": a, "title_b": b, "score": round(float(score), 4)})
    batch = [SE_PAIRS[i % len(SE_PAIRS)] for i in range(BATCH_SIZE)]
    batch_lat = []
    for _ in range(BATCH_RUNS):
        start = time.perf_counter()
        se.evaluate_batch(batch)
        batch_lat.append((time.perf_counter() - start) * 1000)

    load_after = os.getloadavg()[0]
    busy = max(load_before, load_after) / cpus > BUSY_LOAD_PER_CPU
    result = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cpu_count": cpus,
        "load_avg_1m": [round(load_before, 2), round(load_after, 2)],
        "machine_busy": busy,
        "title_expander": {
            "load_s": round(te_load, 2),
            "requests": TE_REQUESTS,
            **stats(te_lat),
            "latencies": [round(v, 1) for v in te_lat],
        },
        "similarity_pair": {
            "load_s": round(se_load, 2),
            "requests": SE_REQUESTS,
            **stats(se_lat),
            "latencies": [round(v, 2) for v in se_lat],
        },
        "similarity_batch20": {"runs": BATCH_RUNS, **stats(batch_lat)},
        "peak_rss_mb_after_ml001": rss_te,
        "peak_rss_mb_both": peak_rss_mb(),
        "te_samples": te_samples,
        "pair_samples": se_samples,
    }
    summary = (
        f"ML-001 mean {result['title_expander']['mean_ms']} ms, "
        f"ML-002 mean {result['similarity_pair']['mean_ms']} ms, "
        f"peak RSS {result['peak_rss_mb_both']} MB"
    )
    if busy and not args.allow_busy:
        raise SystemExit(
            f"NOT SAVED ({summary}): load average {result['load_avg_1m']} on {cpus} CPUs. "
            "Other processes were competing, so these latencies are not representative. "
            "Re-run when the machine is idle, or pass --allow-busy."
        )
    text = json.dumps(result, indent=1, ensure_ascii=False) + "\n"
    (args.out / "bench.json").write_text(text)
    print(f"{summary} -> {args.out / 'bench.json'}")


if __name__ == "__main__":
    main()
