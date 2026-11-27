"""Build the Findrr Model Observatory's data files.

Reads the app's model registry, the installed bundles, ``data/bench.json`` (from ``bench.py``),
the decision log, and the facts below, which are transcribed from ``docs/ml/``. Writes one JSON
file per dashboard dataset, each shaped ``{rows, meta}``, to ``data/``. Run from the repo root:

    python scripts/model_dashboard/build.py [--out DIR] [--models-dir models]

The pre-commit hook in ``hooks/`` runs it before each commit (D-012). Nothing here is
fabricated: every value comes from the registry, a bundle manifest, the benchmark, or the cited
document.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from findrr.ml.manifest import load_manifest, verify_artifact_integrity
from findrr.ml.registry import ModelRegistry

REPO = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
# Versions whose real inference in the app was verified (docs/STATUS.md, model status table).
INTEGRATION_VERIFIED = {("ML-001", "2.0.0"), ("ML-002", "1.1.0")}
# (latency ms, memory MB) budgets, spec section 12. ML-001 memory: < 550 MB RSS (D-004, PROPOSED).
BUDGETS = {"ML-001": (1500, 550), "ML-002": (50, 100), "ML-003": (3000, 450)}
LAPTOP = "bench.py on the Findrr laptop (Intel i5-1235U, CPU only)"

# Kaggle runs before the current bundles, from the decision log. The latest run of each model
# is read from its bundle manifest instead. Each metric is (value, threshold, op); a threshold of
# None means reported only, and a value of None means not recorded.
RUN_HISTORY = [
    (
        "ML-001",
        1,
        "2026-11-26",
        "Unconstrained decoding, split by occupation",
        "D-007",
        {
            "rougeL": (0.194, 0.75, ">="),
            "valid_title_ratio": (0.554, 0.85, ">="),
            "repetition_rate": (0.580, 0.05, "<"),
        },
        "Kaggle output, D-007",
    ),
    (
        "ML-001",
        2,
        "2026-11-26",
        "Constrained decoding over O*NET titles",
        "PR #31",
        {
            "occupation_precision": (0.521, 0.75, ">="),
            "valid_title_ratio": (1.0, 0.85, ">="),
            "repetition_rate": (0.280, 0.05, "<"),
        },
        "Kaggle output, STATUS.md session log (constraint bug fixed in PR #31)",
    ),
    (
        "ML-001",
        3,
        "2026-11-26",
        "Constraint fixed, split by occupation",
        "D-009",
        {
            "occupation_precision": (0.478, 0.75, ">="),
            "valid_title_ratio": (1.0, 0.85, ">="),
            "repetition_rate": (0.0001, 0.05, "<"),
        },
        "Kaggle output, D-009",
    ),
    (
        "ML-001",
        4,
        "2026-11-27",
        "Split by input title, 5 epochs",
        "D-010",
        {
            "occupation_precision": (0.603, 0.75, ">="),
            "valid_title_ratio": (1.0, 0.85, ">="),
            "repetition_rate": (0.0, 0.05, "<"),
            "precision_novel": (0.561, None, ">="),
            "precision_train": (0.727, None, ">="),
            "rougeL": (0.366, None, ">="),
            "bleu4": (0.278, None, ">="),
        },
        "Kaggle output and local training-input check, D-010",
    ),
    (
        "ML-002",
        1,
        "2026-11-26",
        "First fine-tune, Pearson gated",
        "D-008",
        {
            "pearson_r": (0.745, 0.85, ">="),
            "precision_at_0_70": (0.963, 0.90, ">="),
            "synonym": (0.894, 0.85, ">="),
            "distinct": (0.248, 0.30, "<"),
        },
        "Kaggle output, D-008",
    ),
]
CURRENT_RUN = {
    "ML-001": (5, "More input titles, 15 epochs"),
    "ML-002": (2, "Pearson reported, not gated"),
}

DECISIONS_DOC = REPO / "docs/DECISIONS_PENDING.md"

# docs/ml/training/title-expander.md, reference points for the input-title split (D-009).
BASELINES = [
    ("Random dictionary title", 0.007),
    ("Same SOC major group", 0.114),
    ("Same SOC broad group", 0.732),
    ("Same detailed SOC code", 0.929),
    ("Gold references", 1.0),
]


def passed(value, threshold, op):
    if value is None or threshold is None:
        return None
    return value >= threshold if op == ">=" else value < threshold


def first_sentence(text: str) -> str:
    text = re.sub(r"[*`]", "", text).strip()
    match = re.match(r"(.+?[.;])(\s|$)", text)
    return (match.group(1) if match else text).rstrip(".;")


def parse_decisions(markdown: str) -> list[dict]:
    """ML decisions from the decision log, in document order (open first, then resolved)."""
    rows = []
    for block in re.split(r"^### ", markdown, flags=re.M)[1:]:
        head = re.match(r"(D-\d{3}): (.+)", block)
        if not head:
            continue  # the template's D-NNN

        def field(name, text=block):
            found = re.search(rf"^- \*\*{name}:\*\* (.+)$", text, flags=re.M)
            return found.group(1).strip() if found else ""

        if "ML" not in field("Area").split(" / ") and "ML" != field("Area"):
            continue
        status = field("Status") or "Open"
        raised = re.search(r"\d{4}-\d{2}-\d{2}", field("Raised"))
        models = re.findall(r"ML-00\d", head.group(2)) or re.findall(r"ML-00\d", block)
        options = {
            m.group(1): re.sub(r"\s*\(recommended\)", "", m.group(2), flags=re.I).rstrip(".")
            for m in re.finditer(r"^\s+(\d)\. \*\*(.+?)\*\*", block, flags=re.M)
        }

        def named(text):
            chosen = re.search(r"Option (\d)", text)
            if chosen and chosen.group(1) in options:
                return f"Option {chosen.group(1)}: {options[chosen.group(1)]}"
            return first_sentence(text)

        if status == "Resolved" and field("Decision"):
            outcome = named(field("Decision"))
        else:
            outcome = "Recommended: " + named(field("Recommendation"))
        rows.append(
            {
                "id": head.group(1),
                "model_id": models[0] if models else "General",
                "date": raised.group(0) if raised else None,
                "status": status,
                "title": head.group(2).strip(),
                "outcome": outcome,
            }
        )
    return rows


def version_key(path: Path) -> tuple:
    return tuple(int(x) for x in re.findall(r"\d+", path.name))


def installed_bundle(models_dir: Path, reg) -> Path | None:
    """The active bundle if installed and intact, else the newest intact installed version."""
    active = models_dir / reg.relative_path
    others = sorted((models_dir / reg.name).glob("v*"), key=version_key, reverse=True)
    for d in [active] + [o for o in others if o != active]:
        if not (d / "manifest.json").exists():
            continue
        try:
            verify_artifact_integrity(load_manifest(d / "manifest.json"), d)
        except Exception:  # corrupt or incomplete: never use it
            continue
        return d
    return None


def bundle_mb(path: Path) -> float:
    return round(sum(f.stat().st_size for f in path.iterdir() if f.is_file()) / 1e6, 1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=HERE / "data")
    parser.add_argument("--models-dir", type=Path, default=REPO / "models")
    parser.add_argument(
        "--allow-busy",
        action="store_true",
        help="build even if bench.json was measured on a busy machine",
    )
    args = parser.parse_args()
    data_dir = args.out
    data_dir.mkdir(parents=True, exist_ok=True)
    bench = json.loads((args.out / "bench.json").read_text())
    if bench.get("machine_busy") and not args.allow_busy:
        raise SystemExit(
            "bench.json was measured on a busy machine (load average "
            f"{bench.get('load_avg_1m')}). Re-run bench.py when the machine is "
            "idle, or pass --allow-busy to build anyway."
        )
    measured = bench.get("measured_at", "")[:10]
    # A bench.json without "versions" predates PR #40: it measured ML-001 2.0.0 and ML-002 1.1.0.
    measured_v = bench.get("versions", {"ML-001": "2.0.0", "ML-002": "1.1.0"})
    registry = ModelRegistry(base_models_dir=args.models_dir)
    regs = {r.model_id: r for r in registry.list_registrations()}
    te_dir = installed_bundle(args.models_dir, regs["ML-001"])
    se_dir = installed_bundle(args.models_dir, regs["ML-002"])
    if te_dir is None or se_dir is None:
        raise SystemExit(
            "No intact ML-001 or ML-002 bundle is installed under " + str(args.models_dir)
        )
    m1 = json.loads((te_dir / "manifest.json").read_text())
    m2 = json.loads((se_dir / "manifest.json").read_text())
    e1, e2 = m1["evaluation_summary"], m2["evaluation_summary"]
    decisions = parse_decisions(DECISIONS_DOC.read_text())

    def write(name, rows, sources):
        meta = [
            {"label": "Built from", "value": "; ".join(sources)},
            {"label": "Built by", "value": "scripts/model_dashboard/build.py"},
        ]
        if any(LAPTOP in s for s in sources):
            meta.append({"label": "Measured by", "value": "scripts/model_dashboard/bench.py"})
        text = json.dumps({"rows": rows, "meta": meta}, indent=1, ensure_ascii=False) + "\n"
        (data_dir / f"{name}.json").write_text(text)

    def model_row(model_id, manifest, bundle_dir, **facts):
        reg = regs[model_id]
        active, used = reg.active_version, manifest["version"]
        current = used == active
        if current and (model_id, used) in INTEGRATION_VERIFIED:
            stage, label = 5, "Real inference verified in the app"
        elif current:
            stage, label = 4, "Bundle verified"
        else:
            stage, label = 2, f"v{active} awaiting its Kaggle run; metrics are from v{used}"
        passed_ = manifest["metadata"]["acceptance"]["passed"]
        open_ = [d["id"] for d in decisions if d["model_id"] == model_id and d["status"] == "Open"]
        return {
            "model_id": model_id,
            "name": reg.name,
            "version": active,
            "metrics_version": used,
            "architecture": reg.architecture,
            "runtime": "ONNX Runtime CPU"
            if any(f.endswith(".onnx") for f in reg.required_files)
            else "PyTorch CPU",
            "bundle_mb": bundle_mb(bundle_dir),
            "export_date": manifest["export_date"][:10],
            "stage": stage,
            "stage_label": label,
            "integrity": "Verified" if current else f"v{active} not installed",
            "acceptance": ("Passed" if passed_ else "Failed") if current else "Awaiting run",
            "latency_budget_ms": BUDGETS[model_id][0],
            "memory_budget_mb": BUDGETS[model_id][1],
            "open_decision": ", ".join(open_),
            **facts,
        }

    ml3 = regs["ML-003"]
    write(
        "models",
        [
            model_row(
                "ML-001",
                m1,
                te_dir,
                display="Job Title Expander",
                task="Turns a job title into up to 5 related, real O*NET job titles for search",
                feeds="Module 3 (Search Terms)",
                base="google/flan-t5-small",
                params_m=80,
                training="Full fine-tune, 15 epochs, lr 3e-4, batch 32, FP32",
                dataset="O*NET 31.0 (CC BY 4.0)",
                train_size=m1["metadata"]["examples"]["train"],
                test_size=m1["metadata"]["examples"]["test"],
            ),
            model_row(
                "ML-002",
                m2,
                se_dir,
                display="Similarity Evaluator",
                task="Scores how alike two job titles are, to filter search terms and remove "
                "duplicate postings",
                feeds="Module 3 (Search Terms), Module 4 (Find Postings)",
                base="sentence-transformers/all-MiniLM-L6-v2",
                params_m=22,
                training="Contrastive fine-tune (MNRL), 4 epochs, lr 2e-5, batch 64, FP16",
                dataset="O*NET 31.0 (CC BY 4.0)",
                train_size=m2["metadata"]["train_pairs"],
                test_size=int(e2["test_pairs"]),
            ),
            {
                "model_id": "ML-003",
                "name": ml3.name,
                "display": "Application Tailor",
                "version": ml3.active_version,
                "metrics_version": None,
                "task": "Phrases CV and cover-letter sentences from verified profile facts only",
                "feeds": "Module 5 (Application Prep)",
                "architecture": ml3.architecture,
                "base": "Qwen/Qwen2.5-0.5B-Instruct (proposed)",
                "params_m": 500,
                "runtime": "ONNX Runtime CPU (planned)",
                "training": "LoRA, 3 epochs, lr 1e-4 (proposed)",
                "dataset": "Not decided (D-006)",
                "train_size": None,
                "test_size": None,
                "bundle_mb": None,
                "export_date": None,
                "stage": 1,
                "stage_label": "Spec approved, notebook on hold",
                "integrity": "No bundle",
                "acceptance": "Not trained",
                "latency_budget_ms": BUDGETS["ML-003"][0],
                "memory_budget_mb": BUDGETS["ML-003"][1],
                "open_decision": ", ".join(
                    d["id"]
                    for d in decisions
                    if d["model_id"] == "ML-003" and d["status"] == "Open"
                ),
            },
        ],
        [
            "src/findrr/ml/registry.py (active versions, architectures, runtimes)",
            "installed bundles in models/ (manifests, SHA-256 checks)",
            "docs/ml/models/*.md (budgets, section 12)",
            "docs/DECISIONS_PENDING.md (open decisions)",
            "docs/STATUS.md (verified integrations)",
        ],
    )

    def crit(model, key, label, value, op, thr, gated, note=""):
        return {
            "model_id": model,
            "metric": key,
            "label": label,
            "value": value,
            "op": op,
            "threshold": thr,
            "gated": gated,
            "passed": passed(value, thr, op),
            "note": note,
        }

    write(
        "criteria",
        [
            crit(
                "ML-001",
                "occupation_precision",
                "Occupation precision",
                e1["occupation_precision"],
                ">=",
                0.75,
                True,
                "Share of generated titles in the input's occupation or a closely related one",
            ),
            crit(
                "ML-001",
                "valid_title_ratio",
                "Valid title ratio",
                e1["valid_title_ratio"],
                ">=",
                0.85,
                True,
                "Share of generated titles that are real O*NET titles",
            ),
            crit(
                "ML-001",
                "repetition_rate",
                "Repetition rate",
                e1["repetition_rate"],
                "<",
                0.05,
                True,
                "Share of titles repeated within one answer",
            ),
            crit(
                "ML-001",
                "distinct_titles",
                'Distinct titles for "Software Developer"',
                e1["ac_ml_001_1_distinct_titles"],
                ">=",
                3,
                True,
                "AC-ML-001.1",
            ),
            crit(
                "ML-001",
                "precision_novel",
                "Precision on never-seen wording",
                e1["occupation_precision_novel_wording"],
                ">=",
                None,
                False,
                "110 test examples whose wording never appears in training",
            ),
            crit(
                "ML-001",
                "precision_train",
                "Precision on training inputs",
                e1["occupation_precision_train_sample"],
                ">=",
                None,
                False,
                "500 seeded training inputs; checks for under-fitting (D-010)",
            ),
            crit(
                "ML-001",
                "rougeL",
                "ROUGE-L",
                e1["rougeL"],
                ">=",
                None,
                False,
                "Reported only since D-007",
            ),
            crit("ML-001", "bleu4", "BLEU-4", e1["bleu4"], ">=", None, False, "Reported only"),
            crit(
                "ML-002",
                "precision_at_0_70",
                "Precision at 0.70",
                e2["precision_at_0_70"],
                ">=",
                0.90,
                True,
                "Share of pairs scored 0.70 or more that really are the same or a "
                "closely related occupation",
            ),
            crit(
                "ML-002",
                "synonym",
                '"Software Developer" vs "Software Engineer"',
                e2["ac_ml_002_1_synonym_similarity"],
                ">=",
                0.85,
                True,
                "AC-ML-002.1",
            ),
            crit(
                "ML-002",
                "distinct",
                '"Software Developer" vs "Dental Assistant"',
                e2["ac_ml_002_2_distinct_similarity"],
                "<",
                0.30,
                True,
                "AC-ML-002.2",
            ),
            crit(
                "ML-002",
                "pearson_r",
                "Pearson r vs proxy labels",
                e2["pearson_r"],
                ">=",
                None,
                False,
                "Was gated at 0.85; reported only since D-008",
            ),
            crit(
                "ML-002",
                "spearman_rho",
                "Spearman rho vs proxy labels",
                e2["spearman_rho"],
                ">=",
                None,
                False,
                "Reported only",
            ),
            crit(
                "ML-002",
                "onnx_parity",
                "INT8 ONNX vs PyTorch cosine",
                e2["onnx_int8_vs_pytorch_cosine"],
                ">=",
                None,
                False,
                "How closely the shipped INT8 model matches the full-precision one",
            ),
            crit(
                "ML-003",
                "fact_precision",
                "Factual precision",
                None,
                ">=",
                1.0,
                True,
                "Zero invented entities. Not trained yet",
            ),
            crit(
                "ML-003",
                "json_compliance",
                "JSON schema compliance",
                None,
                ">=",
                0.99,
                True,
                "Not trained yet",
            ),
        ],
        ["models/*/manifest.json", "docs/ml/models/application-tailor.md §8"],
    )

    history = list(RUN_HISTORY)
    n1, label1 = CURRENT_RUN["ML-001"]
    history.append(
        (
            "ML-001",
            n1,
            m1["export_date"][:10],
            label1,
            "",
            {
                "occupation_precision": (e1["occupation_precision"], 0.75, ">="),
                "valid_title_ratio": (e1["valid_title_ratio"], 0.85, ">="),
                "repetition_rate": (e1["repetition_rate"], 0.05, "<"),
                "precision_novel": (e1["occupation_precision_novel_wording"], None, ">="),
                "precision_train": (e1["occupation_precision_train_sample"], None, ">="),
                "rougeL": (e1["rougeL"], None, ">="),
                "bleu4": (e1["bleu4"], None, ">="),
            },
            "Bundle manifest, integrity verified",
        )
    )
    n2, label2 = CURRENT_RUN["ML-002"]
    history.append(
        (
            "ML-002",
            n2,
            m2["export_date"][:10],
            label2,
            "",
            {
                "pearson_r": (e2["pearson_r"], None, ">="),
                "precision_at_0_70": (e2["precision_at_0_70"], 0.90, ">="),
                "synonym": (e2["ac_ml_002_1_synonym_similarity"], 0.85, ">="),
                "distinct": (e2["ac_ml_002_2_distinct_similarity"], 0.30, "<"),
                "spearman_rho": (e2["spearman_rho"], None, ">="),
            },
            "Bundle manifest, integrity verified",
        )
    )
    runs = [
        {
            "model_id": model,
            "run": n,
            "run_label": f"Run {n}",
            "date": date,
            "change": change,
            "decision": decision,
            "metric": key,
            "value": v,
            "threshold": thr,
            "op": op,
            "passed": passed(v, thr, op),
            "evidence": evidence,
        }
        for model, n, date, change, decision, metrics, evidence in history
        for key, (v, thr, op) in metrics.items()
    ]
    write("runs", runs, ["docs/DECISIONS_PENDING.md (D-007 to D-010)", "models/*/manifest.json"])

    write(
        "baselines",
        [{"baseline": b, "occupation_precision": v} for b, v in BASELINES],
        ["docs/ml/training/title-expander.md (reference points, input-title split)"],
    )

    bench_rows = [
        {
            "model_id": "ML-001",
            "scenario": "One expansion request",
            "version": measured_v["ML-001"],
            "request": i + 1,
            "latency_ms": v,
        }
        for i, v in enumerate(bench["title_expander"]["latencies"])
    ] + [
        {
            "model_id": "ML-002",
            "scenario": "One title pair",
            "version": measured_v["ML-002"],
            "request": i + 1,
            "latency_ms": v,
        }
        for i, v in enumerate(bench["similarity_pair"]["latencies"])
    ]
    write("benchmark", bench_rows, [f"{LAPTOP}, {measured}"])

    write(
        "resources",
        [
            {
                "model_id": "ML-001",
                "load_s": bench["title_expander"]["load_s"],
                "peak_rss_mb": bench["peak_rss_mb_after_ml001"],
                "batch20_mean_ms": None,
                "note": f"Whole Python process after loading ML-001 v{measured_v['ML-001']}",
            },
            {
                "model_id": "ML-002",
                "load_s": bench["similarity_pair"]["load_s"],
                "peak_rss_mb": bench["peak_rss_mb_both"] - bench["peak_rss_mb_after_ml001"],
                "batch20_mean_ms": bench["similarity_batch20"]["mean_ms"],
                "note": "Extra process memory after also loading ML-002",
            },
        ],
        [f"{LAPTOP}, {measured}"],
    )

    samples = [
        {
            "model_id": "ML-001",
            "input": s["input_title"],
            "context": f"skills: {s['skills']} · level: {s['level']}",
            "output": s["output"],
            "n_titles": s["n_titles"],
            "score": None,
        }
        for s in bench["te_samples"]
    ] + [
        {
            "model_id": "ML-002",
            "input": s["title_a"],
            "context": s["title_b"],
            "output": "",
            "n_titles": None,
            "score": s["score"],
        }
        for s in bench["pair_samples"]
    ]
    write("samples", samples, [f"Real inference with the app's runners via {LAPTOP}, {measured}"])

    write("decisions", decisions, ["docs/DECISIONS_PENDING.md"])

    # Dataset sizes. Split counts come from the manifests where they record them; occupation and
    # input-title counts are the local data-preparation measurements in the training docs.
    ex1 = m1["metadata"]["examples"]
    dictionary = len(json.loads((te_dir / "titles.json").read_text()))

    def split(model, name, kind, unit, count, occupations, inputs, source):
        return {
            "model_id": model,
            "split": name,
            "kind": kind,
            "unit": unit,
            "count": count,
            "occupations": occupations,
            "distinct_inputs": inputs,
            "source": source,
        }

    te_doc = "docs/ml/training/title-expander.md"
    se_doc = "docs/ml/training/similarity-evaluator.md"
    write(
        "splits",
        [
            split(
                "ML-001",
                "Train",
                "split",
                "examples",
                ex1["train"],
                894,
                22967,
                "manifest; occupations and inputs: " + te_doc,
            ),
            split(
                "ML-001",
                "Validation",
                "split",
                "examples",
                ex1["val"],
                432,
                483,
                "manifest; occupations and inputs: " + te_doc,
            ),
            split(
                "ML-001",
                "Test",
                "split",
                "examples",
                ex1["test"],
                403,
                459,
                "manifest; occupations and inputs: " + te_doc,
            ),
            split(
                "ML-001",
                "Test inputs never seen in training",
                "subset",
                "examples",
                int(e1["novel_wording_examples"]),
                None,
                22,
                "manifest; inputs: " + te_doc,
            ),
            split(
                "ML-001",
                "Training-input sample (under-fit check)",
                "subset",
                "examples",
                500,
                None,
                None,
                "D-010",
            ),
            split(
                "ML-001",
                "Constrained-decoding dictionary",
                "vocabulary",
                "titles",
                dictionary,
                None,
                None,
                "titles.json in the bundle",
            ),
            split(
                "ML-002",
                "Train",
                "split",
                "pairs",
                m2["metadata"]["train_pairs"],
                None,
                None,
                "manifest",
            ),
            split(
                "ML-002",
                "Validation",
                "split",
                "pairs",
                None,
                None,
                None,
                "not recorded in the manifest",
            ),
            split(
                "ML-002",
                "Test",
                "split",
                "pairs",
                int(e2["test_pairs"]),
                102,
                None,
                "manifest; occupations: D-008",
            ),
        ],
        [
            "models/*/manifest.json",
            "titles.json in the installed ML-001 bundle",
            te_doc,
            se_doc,
            "docs/DECISIONS_PENDING.md (D-008, D-010)",
        ],
    )

    # D-008: the 800 test pairs rebuilt locally with the notebook's own code.
    write(
        "labelmix",
        [
            {"model_id": "ML-002", "label": 3, "meaning": "Same occupation", "pairs": 306},
            {
                "model_id": "ML-002",
                "label": 2,
                "meaning": "Closely related (Primary-Short)",
                "pairs": 99,
            },
            {
                "model_id": "ML-002",
                "label": 1,
                "meaning": "Loosely related (Primary-Long)",
                "pairs": 89,
            },
            {"model_id": "ML-002", "label": 0, "meaning": "Different major group", "pairs": 306},
        ],
        ["docs/DECISIONS_PENDING.md (D-008)", se_doc],
    )

    print("Wrote", ", ".join(sorted(p.name for p in data_dir.glob("*.json"))), "to", data_dir)


if __name__ == "__main__":
    main()
