"""Contract tests for the Kaggle training notebooks (ML-001, ML-002).

The cells tagged ``findrr-testable`` (O*NET loading, occupation-disjoint splits, dataset
construction, metrics and manifest building) are executed here against a tiny synthetic
O*NET fixture. Nothing is trained. The final tests check that a bundle described by the
notebook's manifest is accepted by the app's registry - and refused when acceptance failed.
"""

import json
from collections import defaultdict
from pathlib import Path

import pytest

from findrr.ml.manifest import ModelManifest
from findrr.ml.registry import CATALOG, ModelRegistry

NOTEBOOKS = Path(__file__).resolve().parents[2] / "notebooks"


def _testable_namespace(name: str) -> dict:
    nb = json.loads((NOTEBOOKS / name).read_text(encoding="utf-8"))
    ns: dict = {}
    for cell in nb["cells"]:
        if "findrr-testable" in cell["metadata"].get("tags", []):
            exec("".join(cell["source"]), ns)  # noqa: S102 - repository-owned notebook code
    return ns


def _write(path: Path, header: str, rows: list) -> None:
    path.write_text("\n".join([header] + ["\t".join(r) for r in rows]) + "\n", encoding="utf-8")


@pytest.fixture
def onet_dir(tmp_path):
    d = tmp_path / "onet"
    d.mkdir()
    occs = {
        "15-1252.00": (
            "Software Developers",
            ["Software Engineer", "Application Developer", "Programmer",
             "Software Architect", "Senior Software Engineer", "Lead Developer"],
        ),
        "15-1211.00": ("Computer Systems Analysts", ["Systems Analyst", "Business Systems Analyst",
                                                     "IT Analyst", "Systems Consultant"]),
        "29-2021.00": ("Dental Hygienists", ["Dental Hygienist", "Registered Dental Hygienist",
                                             "Hygienist", "Oral Health Educator"]),
        "29-1141.00": ("Registered Nurses", ["Staff Nurse", "Charge Nurse", "Clinical Nurse",
                                             "Nurse, Registered", "Senior Nurse"]),
        "47-2061.00": ("Construction Laborers", ["Laborer", "Construction Worker", "Site Labourer",
                                                 "General Laborer"]),
    }
    _write(d / "Occupation Data.txt", "O*NET-SOC Code\tTitle\tDescription",
           [(soc, t, "desc") for soc, (t, _) in occs.items()])
    _write(d / "Sample of Reported Titles.txt",
           "O*NET-SOC Code\tReported Job Title\tShown in My Next Move",
           [(soc, t, "Y") for soc, (_, ts) in occs.items() for t in ts])
    _write(d / "Job Titles.txt", "O*NET-SOC Code\tJob Title\tShort Title\tSource(s)",
           [(soc, t + " (Full Name)", "n/a", "08") for soc, (_, ts) in occs.items() for t in ts]
           + [("15-1252.00", "Senior Application Developer", "n/a", "08"),
              ("15-1252.00", "Senior Programmer", "n/a", "08"),
              ("15-1252.00", "Java Developer", "n/a", "08")])
    _write(d / "Software Skills.txt",
           "O*NET-SOC Code\tWorkplace Example\tElement ID\tElement Name\tHot Technology\tIn Demand",
           [("15-1252.00", "Python", "x", "y", "Y", "Y"),
            ("15-1252.00", "Git", "x", "y", "N", "N")])
    _write(d / "Related Occupations.txt",
           "O*NET-SOC Code\tRelated O*NET-SOC Code\tRelatedness Tier\tIndex",
           [("15-1252.00", "15-1211.00", "Primary-Short", "1"),
            ("29-2021.00", "29-1141.00", "Primary-Long", "1")])
    return d


def test_title_cleaning_and_loading(onet_dir):
    ns = _testable_namespace("01_train_title_expander.ipynb")
    full = "AI Specialist (Artificial Intelligence Specialist)"
    assert ns["clean_title"](full) == "AI Specialist"
    assert ns["clean_title"]("Long Title", "Short") == "Short"
    onet = ns["load_onet"](onet_dir)
    assert "Software Engineer" in onet["job_titles"]["15-1252.00"]  # parenthetical stripped
    assert onet["skills"]["15-1252.00"][0] == ("Python", True)


def test_split_is_occupation_disjoint_and_deterministic():
    ns = _testable_namespace("01_train_title_expander.ipynb")
    socs = [f"{g:02d}-{i:04d}.00" for g in (11, 15, 29) for i in range(30)]
    a = ns["split_by_occupation"](socs, seed=1)
    assert a == ns["split_by_occupation"](socs, seed=1)
    assert set(a.values()) == {"train", "val", "test"}
    assert sum(v == "train" for v in a.values()) > sum(v == "test" for v in a.values())


def test_title_split_is_by_input_title(onet_dir):
    """D-009: every occupation is trained on; an input wording never crosses splits."""
    ns = _testable_namespace("01_train_title_expander.ipynb")
    norm = ns["norm"]
    anchors = {
        "A": ["Software Developer", "Programmer", "Coder"],
        "B": ["Programmer", "Dental Assistant"],
        "C": ["Welder"],
    }
    for seed in range(20):
        split = ns["split_by_anchor"](anchors, seed=seed)
        assert split == ns["split_by_anchor"](anchors, seed=seed)
        # one split per wording
        assert set(split) == {norm(a) for lst in anchors.values() for a in lst}
        for lst in anchors.values():
            assert any(split[norm(a)] == "train" for a in lst)  # every occupation is learned
    onet = ns["load_onet"](onet_dir)
    ex = ns["build_title_examples"](onet, seed=3)
    train = {norm(r["anchor"]) for r in ex["train"]}
    assert not train & {norm(r["anchor"]) for r in ex["test"] + ex["val"]}
    assert {r["soc"] for r in ex["test"] + ex["val"]} <= {r["soc"] for r in ex["train"]}
    assert ns["novel_wording"](ex) <= {norm(r["anchor"]) for r in ex["test"]}

def test_extra_job_title_anchors_are_training_only(onet_dir):
    """D-010: O*NET job titles add level-ANY training inputs; val/test wording is never reused."""
    ns = _testable_namespace("01_train_title_expander.ipynb")
    norm = ns["norm"]
    onet = ns["load_onet"](onet_dir)
    ex = ns["build_title_examples"](onet, seed=3)
    anchors_by_soc = ns["occupation_anchors"](onet)
    regular = {norm(a) for anchors, _, _ in anchors_by_soc.values() for a in anchors}
    extra = [r for r in ex["train"] if norm(r["anchor"]) not in regular]
    assert "java developer" in {norm(r["anchor"]) for r in extra}
    held_out = {norm(r["anchor"]) for r in ex["val"] + ex["test"]}
    for r in extra:
        assert r["input_text"].endswith("| level: ANY")
        assert norm(r["anchor"]) not in held_out
        assert not ns["ANY_LEVEL"].search(r["anchor"])
        assert len(ns["parse_titles"](r["target_text"])) >= ns["MIN_TARGET_TITLES"]
    per_soc = {}
    for r in extra:
        per_soc[r["soc"]] = per_soc.get(r["soc"], 0) + 1
    assert max(per_soc.values()) <= ns["MAX_EXTRA_ANCHORS_PER_OCCUPATION"]


def test_title_examples_match_runner_prompt_and_levels(onet_dir):
    ns = _testable_namespace("01_train_title_expander.ipynb")
    onet = ns["load_onet"](onet_dir)
    split_of = defaultdict(lambda: "train")
    rows = ns["build_title_examples"](onet, split_of=split_of)["train"]
    assert rows
    levels = {r["input_text"].rsplit("level: ", 1)[1] for r in rows}
    assert levels == {"ANY", "ENTRY", "MID", "SENIOR", "LEAD"}  # == SeniorityLevel + ANY
    for r in rows:
        assert r["input_text"].startswith("expand titles: ")
        targets = ns["parse_titles"](r["target_text"])
        anchor = r["input_text"][len("expand titles: "):].split(" | ")[0]
        assert anchor not in targets and len(targets) >= 3
        assert all("," not in t for t in targets)  # no comma titles (comma is the separator)
    senior = [r for r in rows if r["input_text"].endswith("SENIOR") and r["soc"] == "15-1252.00"]
    assert senior and all("Senior" in r["target_text"] for r in senior)
    skill_text = rows[0]["input_text"].split(" | skills: ")[1].split(" | ")[0]
    assert skill_text  # 'general' when an occupation has no skills, as the runner sends


def test_title_metrics(onet_dir):
    ns = _testable_namespace("01_train_title_expander.ipynb")
    d = ns["title_dictionary"](ns["load_onet"](onet_dir))
    assert ns["valid_title_ratio"](["Software Engineer, Made Up Title"], d) == 0.5
    assert ns["repetition_rate"](["A, A, B, C"]) == 0.25


def test_similarity_pairs_are_disjoint_and_graded(onet_dir):
    ns = _testable_namespace("02_train_similarity_evaluator.ipynb")
    onet = ns["load_onet"](onet_dir)
    split_of = {"15-1252.00": "train", "47-2061.00": "train", "15-1211.00": "test",
                "29-2021.00": "test", "29-1141.00": "test"}
    train = ns["build_training_pairs"](onet, split_of)
    train_titles = {t for p in train for t in (p["anchor"], p["positive"])}
    test = ns["build_graded_pairs"](onet, split_of, "test")
    test_titles = {t for a, b, _ in test for t in (a, b)}
    assert train and test and not (train_titles & test_titles)
    assert {lbl for *_, lbl in test} >= {0, 1, 3}


def test_similarity_metrics():
    ns = _testable_namespace("02_train_similarity_evaluator.ipynb")
    assert ns["pearson"]([1, 2, 3], [2, 4, 6]) == pytest.approx(1.0)
    assert ns["spearman"]([0.1, 0.5, 0.9], [0, 1, 3]) == pytest.approx(1.0)
    assert ns["precision_at"]([0.9, 0.8, 0.2], [3, 0, 3], 0.70) == 0.5


@pytest.mark.parametrize(
    "notebook, model_id, extra_files",
    [
        ("01_train_title_expander.ipynb", "ML-001", []),
        ("02_train_similarity_evaluator.ipynb", "ML-002", []),
    ],
)
def test_notebook_manifest_is_accepted_by_app_registry(tmp_path, notebook, model_id, extra_files):
    ns = _testable_namespace(notebook)
    reg = CATALOG[model_id]
    bundle = tmp_path / reg.relative_path
    bundle.mkdir(parents=True)
    for name in reg.required_files:
        if name != "manifest.json":
            (bundle / name).write_bytes(name.encode())

    def write_manifest(passed: bool) -> None:
        acceptance = ns["check_acceptance"]({"m": 1.0 if passed else 0.0}, {"m": (">=", 0.5)})
        manifest = ns["build_manifest"](bundle, model_id, reg.name, reg.active_version, "arch",
                                        {"m": 1.0 if passed else 0.0}, acceptance, {"seed": 42})
        ModelManifest(**manifest)  # exact app schema
        (bundle / "manifest.json").write_text(json.dumps(manifest))

    write_manifest(passed=True)
    status = ModelRegistry(base_models_dir=tmp_path).inspect_model_status(model_id)
    assert status["integrity_verified"] is True, status["error"]

    write_manifest(passed=False)
    status = ModelRegistry(base_models_dir=tmp_path).inspect_model_status(model_id)
    assert status["integrity_verified"] is False
    assert "acceptance" in status["error"]


def test_manifest_refuses_unmeasured_metrics(tmp_path):
    ns = _testable_namespace("01_train_title_expander.ipynb")
    (tmp_path / "f").write_text("x")
    with pytest.raises(ValueError, match="not measured"):
        ns["build_manifest"](tmp_path, "ML-001", "title-expander", "2.0.0", "a",
                             {"rougeL": None}, {"passed": True}, {})


def test_registry_rejects_wrong_model_or_version(tmp_path):
    ns = _testable_namespace("01_train_title_expander.ipynb")
    reg = CATALOG["ML-001"]
    bundle = tmp_path / reg.relative_path
    bundle.mkdir(parents=True)
    for name in reg.required_files:
        if name != "manifest.json":
            (bundle / name).write_bytes(b"x")
    manifest = ns["build_manifest"](
        bundle, "ML-001", reg.name, "1.0.0", "a", {}, {"passed": True}, {}
    )
    (bundle / "manifest.json").write_text(json.dumps(manifest))
    status = ModelRegistry(base_models_dir=tmp_path).inspect_model_status("ML-001")
    assert status["integrity_verified"] is False and "version" in status["error"]


COMPILED_PACKAGES = ("sentencepiece", "torch", "tokenizers", "safetensors", "numpy", "onnx",
                     "onnxruntime", "scipy")


@pytest.mark.parametrize(
    "notebook", ["01_train_title_expander.ipynb", "02_train_similarity_evaluator.ipynb"]
)
def test_notebooks_do_not_pin_compiled_packages_exactly(notebook):
    """Exact pins on compiled packages force source builds on newer Kaggle Python versions."""
    nb = json.loads((NOTEBOOKS / notebook).read_text(encoding="utf-8"))
    installs = " ".join(
        "".join(c["source"]) for c in nb["cells"] if "pip install" in "".join(c["source"])
    )
    for pkg in COMPILED_PACKAGES:
        assert f" {pkg}==" not in installs and f'"{pkg}==' not in installs, pkg


@pytest.mark.parametrize(
    "notebook", ["01_train_title_expander.ipynb", "02_train_similarity_evaluator.ipynb"]
)
def test_no_library_import_before_pinned_install(notebook):
    """Importing transformers before `pip install transformers==X` mixes two versions in the
    kernel (seen on Kaggle: 'cannot import name is_flax_available')."""
    nb = json.loads((NOTEBOOKS / notebook).read_text(encoding="utf-8"))
    srcs = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
    pip_i = next(i for i, s in enumerate(srcs) if "!pip install" in s)
    for s in srcs[:pip_i]:
        assert "__import__" not in s and "import torch" not in s and "import transformers" not in s
    guard_i = next(i for i, s in enumerate(srcs) if "def _check(" in s)
    first_lib = next(
        i for i, s in enumerate(srcs)
        if "from transformers" in s or "from sentence_transformers" in s
    )
    assert pip_i < guard_i < first_lib


def test_notebook_embeds_constraint_module_verbatim():
    nb = json.loads((NOTEBOOKS / "01_train_title_expander.ipynb").read_text(encoding="utf-8"))
    module = (NOTEBOOKS.parent / "src/findrr/ml/title_constraint.py").read_text(encoding="utf-8")
    sources = ["".join(c["source"]) for c in nb["cells"]]
    embedded = [src for src in sources if "class TitleTrieConstraint" in src]
    assert len(embedded) == 1
    hint = "regenerate notebooks: python scripts/generate_kaggle_notebooks.py"
    assert module.strip() in embedded[0], hint


def test_occupation_precision_and_dictionary(onet_dir):
    ns = _testable_namespace("01_train_title_expander.ipynb")
    onet = ns["load_onet"](onet_dir)
    index = ns["title_occupations"](onet)
    titles = ns["dictionary_titles"](onet)
    assert titles and all("," not in t for t in titles)
    assert "Nurse, Registered" not in titles
    rows = [("15-1252.00", ["Software Engineer", "Systems Analyst", "Staff Nurse"])]
    # Software Engineer: same occupation; Systems Analyst: Primary-Short related; Staff Nurse: no.
    assert ns["occupation_precision"](rows, onet, index) == 2 / 3
    stray = "Registered Radiologic Technologist)"
    assert ns["clean_title"](stray) == "Registered Radiologic Technologist"


def test_ml002_reports_pearson_but_does_not_gate_on_it():
    """D-008 (owner decision 2026-11-26): Pearson r is reported, not an acceptance gate."""
    nb = json.loads((NOTEBOOKS / "02_train_similarity_evaluator.ipynb").read_text())
    sources = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
    gate = next(s for s in sources if "ACCEPTANCE = check_acceptance(" in s)
    measured = next(s for s in sources if "measured = {" in s)
    assert "'pearson_r'" in measured and "'spearman_rho'" in measured
    assert "pearson" not in gate.split("check_acceptance(", 1)[1].lower().split("})")[0]
    gated = (
        "precision_at_0_70",
        "ac_ml_002_1_synonym_similarity",
        "ac_ml_002_2_distinct_similarity",
    )
    for key in gated:
        assert f"'{key}'" in gate
