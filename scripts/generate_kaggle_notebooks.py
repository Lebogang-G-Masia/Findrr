"""Generate the Kaggle training notebooks for ML-001 (title expander) and ML-002 (similarity).

Run from the repository root:  python scripts/generate_kaggle_notebooks.py

The notebooks implement docs/ml/models/title-expander.md and similarity-evaluator.md.
Cells tagged ``findrr-testable`` contain pure-Python data preparation, metric and manifest
code; tests/unit/test_kaggle_notebooks.py executes them against a synthetic O*NET fixture so
the dataset and manifest contracts are checked in CI without training anything.
"""

import json
import textwrap
from pathlib import Path

TESTABLE = "findrr-testable"


def _source(text: str) -> list:
    text = textwrap.dedent(text).strip("\n")
    lines = text.split("\n")
    return [line + "\n" for line in lines[:-1]] + [lines[-1]]


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": _source(text)}


def code(text: str, testable: bool = False) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {"tags": [TESTABLE]} if testable else {},
        "outputs": [],
        "source": _source(text),
    }


def notebook(cells: list) -> dict:
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
            "kaggle": {
                "accelerator": "gpu",
                "isGpuEnabled": True,
                "isInternetEnabled": True,
                "language": "python",
                "sourceType": "notebook",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


# --------------------------------------------------------------------------------------------
# Shared cells (both notebooks)
# --------------------------------------------------------------------------------------------

ENV_REPORT = code(
    r'''
    # Environment report. Reads package metadata only: importing transformers/torch here,
    # before the pip install below replaces them, would mix two versions in this kernel.
    import platform, sys
    from importlib import metadata
    print('Python', sys.version.split()[0], '|', platform.platform())
    for pkg in ('torch', 'transformers', 'tokenizers', 'datasets', 'sentence-transformers',
                'numpy', 'onnxruntime', 'huggingface-hub'):
        try:
            print(f'{pkg:>22} {metadata.version(pkg)}')
        except metadata.PackageNotFoundError:
            print(f'{pkg:>22} not installed')
    '''
)


def version_guard(pins: dict) -> str:
    """Code that fails clearly if the kernel still has pre-install library versions loaded."""
    checks = "\n".join(
        f"_check({module!r}, {version!r})" for module, version in pins.items()
    )
    return (
        "import importlib\n"
        "def _check(module, expected):\n"
        "    found = importlib.import_module(module).__version__\n"
        "    if found != expected:\n"
        "        raise RuntimeError(\n"
        "            f'{module} {found} is loaded but {expected} is pinned. The kernel imported it '\n"
        "            'before the pip install finished. Use Run > Restart & clear cell outputs, then '\n"
        "            'Run All again.')\n"
        + checks + "\n"
    )

ONET_CONFIG = code(
    r'''
    # O*NET database (CC BY 4.0, U.S. Department of Labor / ETA). Public occupational data only;
    # no real user data is used anywhere in this notebook.
    ONET_VERSION = '31_0'
    ONET_URL = f'https://www.onetcenter.org/dl_files/database/db_{ONET_VERSION}_text.zip'
    # SHA-256 of db_31_0_text.zip as downloaded on 2026-11-26. Change both values together.
    ONET_SHA256 = '6883548adf5fde64cf6f801b35d15519c9225f2732c3cab0e281c652d16b23a9'
    # Optional offline copy: attach the extracted folder as a Kaggle dataset at this path.
    ONET_OFFLINE_DIR = '/kaggle/input/onet-db'
    SEED = 42
    '''
)

ONET_DOWNLOAD = code(
    r'''
    import hashlib, io, os, zipfile, urllib.request
    from pathlib import Path

    def obtain_onet_dir() -> Path:
        """Return a directory with the O*NET text files; verify the archive checksum."""
        offline = Path(ONET_OFFLINE_DIR)
        if offline.exists():
            hits = list(offline.rglob('Occupation Data.txt'))
            if hits:
                print(f'Using attached O*NET dataset at {hits[0].parent}')
                return hits[0].parent
        print(f'Downloading {ONET_URL} ...')
        with urllib.request.urlopen(ONET_URL, timeout=120) as resp:
            blob = resp.read()
        digest = hashlib.sha256(blob).hexdigest()
        if digest != ONET_SHA256:
            raise RuntimeError(
                f'O*NET archive checksum mismatch: got {digest}, expected {ONET_SHA256}. '
                'Refusing to train on unverified data.'
            )
        target = Path('/kaggle/working/onet')
        with zipfile.ZipFile(io.BytesIO(blob)) as zf:
            zf.extractall(target)
        return next(target.rglob('Occupation Data.txt')).parent

    ONET_DIR = obtain_onet_dir()
    '''
)

ONET_LOADER = code(
    r'''
    import csv, re, random
    from collections import defaultdict
    from pathlib import Path

    def _find(root: Path, *names: str) -> Path:
        """Return the first existing file among names (O*NET renamed files across releases)."""
        for name in names:
            p = Path(root) / name
            if p.exists():
                return p
        raise FileNotFoundError(f'None of {names} found in {root}')

    def _rows(path: Path):
        with open(path, encoding='utf-8', newline='') as fh:
            yield from csv.DictReader(fh, delimiter='\t')

    _PAREN = re.compile(r'\s*\([^)]*\)')

    def clean_title(title: str, short: str = '') -> str:
        """Prefer the O*NET short title; drop parenthetical expansions; collapse whitespace."""
        base = short if short and short.strip().lower() not in ('n/a', '') else title
        base = _PAREN.sub('', base).replace('(', ' ').replace(')', ' ')
        return ' '.join(base.replace('/', ' / ').split()).strip(' ,;')

    def norm(title: str) -> str:
        return ' '.join(re.sub(r'[^\w\s]', ' ', title.lower()).split())

    def load_onet(root) -> dict:
        root = Path(root)
        occupations = {r['O*NET-SOC Code']: r['Title'] for r in _rows(_find(root, 'Occupation Data.txt'))}
        reported = defaultdict(list)
        for r in _rows(_find(root, 'Sample of Reported Titles.txt')):
            t = clean_title(r['Reported Job Title'])
            if t and t not in reported[r['O*NET-SOC Code']]:
                reported[r['O*NET-SOC Code']].append(t)
        job_titles = defaultdict(list)
        for r in _rows(_find(root, 'Job Titles.txt', 'Alternate Titles.txt')):
            title_col = 'Job Title' if 'Job Title' in r else 'Alternate Title'
            t = clean_title(r[title_col], r.get('Short Title', ''))
            if t and t not in job_titles[r['O*NET-SOC Code']]:
                job_titles[r['O*NET-SOC Code']].append(t)
        skills = defaultdict(list)
        for r in _rows(_find(root, 'Software Skills.txt', 'Technology Skills.txt')):
            ex = r.get('Workplace Example') or r.get('Example') or ''
            if ex:
                skills[r['O*NET-SOC Code']].append((ex.strip(), r.get('Hot Technology', 'N') == 'Y'))
        related = defaultdict(list)
        for r in _rows(_find(root, 'Related Occupations.txt')):
            related[r['O*NET-SOC Code']].append((r['Related O*NET-SOC Code'], r['Relatedness Tier']))
        return {
            'occupations': occupations,
            'reported': dict(reported),
            'job_titles': dict(job_titles),
            'skills': dict(skills),
            'related': dict(related),
        }

    def split_by_occupation(socs, seed: int = 42, fractions=(0.8, 0.1, 0.1)) -> dict:
        """Assign whole occupations to train/val/test, stratified by SOC major group.

        Every title of an occupation lands in exactly one split, so evaluation titles are
        never seen in training (spec: disjoint titles, stratified by occupational domain).
        """
        by_group = defaultdict(list)
        for soc in sorted(set(socs)):
            by_group[soc[:2]].append(soc)
        rng = random.Random(seed)
        assignment = {}
        for group in sorted(by_group):
            members = by_group[group]
            rng.shuffle(members)
            n = len(members)
            n_val = max(1, round(n * fractions[1])) if n >= 3 else 0
            n_test = max(1, round(n * fractions[2])) if n >= 3 else 0
            for i, soc in enumerate(members):
                if i < n_test:
                    assignment[soc] = 'test'
                elif i < n_test + n_val:
                    assignment[soc] = 'val'
                else:
                    assignment[soc] = 'train'
        return assignment
    ''',
    testable=True,
)

MANIFEST_CELL = code(
    r'''
    import hashlib, json
    from datetime import datetime, timezone
    from pathlib import Path

    def sha256_file(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, 'rb') as fh:
            while chunk := fh.read(65536):
                h.update(chunk)
        return h.hexdigest()

    def build_manifest(export_dir, model_id, model_name, version, architecture,
                       evaluation_summary, acceptance, metadata) -> dict:
        """Manifest in the exact schema of findrr.ml.manifest.ModelManifest.

        ``files`` maps every exported file (except manifest.json) to its SHA-256.
        ``evaluation_summary`` holds measured floats only; nothing is defaulted.
        """
        export_dir = Path(export_dir)
        files = {
            p.name: sha256_file(p)
            for p in sorted(export_dir.iterdir())
            if p.is_file() and p.name != 'manifest.json'
        }
        for key, value in evaluation_summary.items():
            if not isinstance(value, (int, float)) or value != value:  # reject None/NaN
                raise ValueError(f'Metric {key!r} was not measured: {value!r}')
        return {
            'model_id': model_id,
            'model_name': model_name,
            'version': version,
            'architecture': architecture,
            'export_date': datetime.now(timezone.utc).isoformat(),
            'files': files,
            'evaluation_summary': {k: float(v) for k, v in evaluation_summary.items()},
            'metadata': {**metadata, 'acceptance': acceptance},
        }

    def check_acceptance(measured: dict, criteria: dict) -> dict:
        """criteria: {metric: ('>=' | '<', threshold)} taken verbatim from the model spec."""
        results = {}
        for metric, (op, threshold) in criteria.items():
            value = measured[metric]
            ok = value >= threshold if op == '>=' else value < threshold
            results[metric] = {'value': float(value), 'op': op, 'threshold': threshold, 'passed': bool(ok)}
        return {'passed': all(r['passed'] for r in results.values()), 'criteria': results}
    ''',
    testable=True,
)


def gate_cell(model_label: str) -> dict:
    return code(
        rf'''
        # Acceptance gate. A model that fails the approved criteria is NOT exported unless you
        # deliberately set ALLOW_EXPORT_BELOW_ACCEPTANCE = True. In that case the manifest records
        # acceptance.passed = false and the Findrr app refuses to load the model.
        ALLOW_EXPORT_BELOW_ACCEPTANCE = False
        print(json.dumps(ACCEPTANCE, indent=2))
        if not ACCEPTANCE['passed'] and not ALLOW_EXPORT_BELOW_ACCEPTANCE:
            raise RuntimeError(
                '{model_label} did not meet its acceptance criteria. Not exporting. '
                'Report the metrics above; do not change thresholds without approval.'
            )
        '''
    )


def verify_cell(bundle: str) -> dict:
    return code(
        rf'''
        # Re-verify the bundle exactly as the Findrr app will (SHA-256 of every file).
        import tarfile, tempfile
        with tempfile.TemporaryDirectory() as tmp:
            with tarfile.open('{bundle}') as tar:
                tar.extractall(tmp)
            m = json.loads((Path(tmp) / 'manifest.json').read_text())
            for name, digest in m['files'].items():
                assert sha256_file(Path(tmp) / name) == digest, name
        print('[OK] Bundle verified:', len(m['files']), 'files;', 'acceptance passed =', m['metadata']['acceptance']['passed'])
        '''
    )


# --------------------------------------------------------------------------------------------
# ML-001: title expander
# --------------------------------------------------------------------------------------------

ML001_VERSION = "2.1.0"
# D-004: a v2.0.0 bundle (same training recipe, safetensors) can be re-exported without
# retraining; see REUSE_BUNDLE_DIR in the notebook.
ML001_REUSABLE_VERSION = "2.0.0"


SRC_ML = Path(__file__).resolve().parents[1] / "src/findrr/ml"


def embedded_module_cell(module: str, testable: bool) -> dict:
    """Embed src/findrr/ml/<module>.py verbatim so the notebook and the app run the same code."""
    source = (SRC_ML / f"{module}.py").read_text(encoding="utf-8")
    header = (
        f"# Copied verbatim from src/findrr/ml/{module}.py by\n"
        "# scripts/generate_kaggle_notebooks.py. Do not edit here.\n"
    )
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {"tags": [TESTABLE]} if testable else {},
        "outputs": [],
        "source": _source(header + source),
    }


def constraint_cell() -> dict:
    return embedded_module_cell("title_constraint", testable=True)


def title_expander_notebook() -> dict:
    return notebook(
        [
            md(
                f"""
                # Findrr ML-001: Title Expander - training and export (v{ML001_VERSION})

                Implements `docs/ml/models/title-expander.md`: fine-tune `google/flan-t5-small` to
                generate alternative job titles from a title, skills and a seniority level.

                **Data:** O*NET 31.0 (public, CC BY 4.0): reported titles, job titles, software skills.
                No real user data. Splits are by input title (D-009): every occupation is learned, and test
                inputs are titles never used as a training input.

                **Run on Kaggle:** Settings -> Accelerator **GPU T4**, **Internet on** -> Run All.
                Then download `title_expander_bundle.tar.gz` and extract it into
                `models/title-expander/v{ML001_VERSION}/` in your Findrr folder.

                **Export (D-004):** the model ships as ONNX fp32 with a KV cache (`encoder.onnx`,
                `decoder.onnx`, `embeddings.npy`), so the Findrr app runs it without PyTorch. The
                export is checked against the model's own logits, and **all metrics below are
                measured on the exported ONNX files** with the app's own decoding code
                (`findrr.ml.t5_onnx_decoding`, embedded below). This evaluation runs on the CPU and
                takes about 20-30 minutes.

                **No retraining needed for a v{ML001_REUSABLE_VERSION} model:** upload your accepted
                v{ML001_REUSABLE_VERSION} bundle as one archive (`.tar.gz` or `.zip`) to a private Kaggle
                dataset, attach it, and set `REUSE_BUNDLE_DIR` below to the dataset folder. The notebook verifies its checksums and acceptance, skips
                training and re-exports it.

                Decoding is constrained to real O*NET titles (D-007), and the bundle ships the
                title dictionary as `titles.json`. The notebook stops before export if the model
                fails its acceptance criteria: occupation precision >= the PROPOSED threshold,
                valid title ratio >= 0.85, repetition < 0.05, and >= 3 distinct titles for
                "Software Developer". ROUGE-L and BLEU-4 are reported only.
                """
            ),
            ENV_REPORT,
            code(
                """
                # Pure-Python libraries whose APIs this notebook uses are pinned exactly.
                # Compiled packages (torch, tokenizers, safetensors, numpy) come from the Kaggle
                # image: pinning old releases forces source builds on newer Python versions.
                # sentencepiece is not needed: flan-t5 loads its fast tokenizer from tokenizer.json.
                # onnx/onnxruntime get a minimum version so pip can pick a prebuilt wheel (D-004 export).
                !pip install -q --prefer-binary transformers==4.46.3 datasets==3.1.0 accelerate==1.1.1 \\
                    rouge-score==0.1.2 sacrebleu==2.4.3 "onnx>=1.17.0" "onnxruntime>=1.20.1"
                """
            ),
            ONET_CONFIG,
            ONET_DOWNLOAD,
            ONET_LOADER,
            constraint_cell(),
            embedded_module_cell("t5_onnx_decoding", testable=False),
            embedded_module_cell("t5_onnx_export", testable=False),
            code(
                r'''
                # Dataset construction parameters (dataset shape, not acceptance thresholds).
                LEVELS = ['ANY', 'ENTRY', 'MID', 'SENIOR', 'LEAD']  # == findrr SeniorityLevel + ANY
                LEVEL_PATTERNS = {
                    'ENTRY': r'\b(junior|jr|entry|associate|trainee|apprentice|intern|graduate)\b',
                    'SENIOR': r'\b(senior|sr)\b',
                    'LEAD': r'\b(lead|principal|chief|head)\b',
                }
                ANY_LEVEL = re.compile('|'.join(LEVEL_PATTERNS.values()), re.IGNORECASE)
                MAX_ANCHORS_PER_OCCUPATION = 6
                # D-010: extra training-only inputs from O*NET job titles, level ANY.
                MAX_EXTRA_ANCHORS_PER_OCCUPATION = 30
                MAX_TARGET_TITLES = 5
                MIN_TARGET_TITLES = 3
                MAX_SKILLS = 5

                def level_pool(level, neutral, all_titles):
                    if level in LEVEL_PATTERNS:
                        pat = re.compile(LEVEL_PATTERNS[level], re.IGNORECASE)
                        pool = sorted({t for t in all_titles if pat.search(t)}, key=str.lower)
                        if len(pool) >= MIN_TARGET_TITLES:
                            return pool
                    return neutral

                def skills_text(skill_rows, rng):
                    ranked = [s for s, hot in skill_rows if hot] + [s for s, hot in skill_rows if not hot]
                    ranked = list(dict.fromkeys(ranked))[:8]
                    if not ranked:
                        return 'general'  # what the Findrr runner sends when no skills exist
                    k = rng.randint(1, min(MAX_SKILLS, len(ranked)))
                    return ', '.join(ranked[:k])

                def occupation_anchors(onet):
                    """{soc: (anchors, neutral titles, all titles)} for occupations with enough targets."""
                    out = {}
                    for soc, occ_title in sorted(onet['occupations'].items()):
                        # ',' separates titles in the model output, so titles containing commas
                        # (e.g. 'Superintendent, Schools') are left out of inputs and targets.
                        base = [occ_title] if ',' not in occ_title else []
                        reported = [t for t in onet['reported'].get(soc, []) if ',' not in t]
                        all_titles = [t for t in dict.fromkeys(base + reported + onet['job_titles'].get(soc, []))
                                      if ',' not in t]
                        neutral = sorted({t for t in base + reported if not ANY_LEVEL.search(t)}, key=str.lower)
                        if len(neutral) < MIN_TARGET_TITLES + 1:
                            continue
                        anchors = base + [t for t in neutral if not base or norm(t) != norm(occ_title)]
                        out[soc] = (anchors[:MAX_ANCHORS_PER_OCCUPATION], neutral, all_titles)
                    return out

                def _anchor_hash(seed, key):
                    import hashlib
                    return int(hashlib.sha256(f'{seed}:{key}'.encode()).hexdigest()[:12], 16) / float(16 ** 12)

                def split_by_anchor(anchors_by_soc, seed=42, fractions=(0.8, 0.1, 0.1)):
                    """D-009: assign each normalised input title (anchor) to train/val/test.

                    Every occupation is learned, but evaluation inputs are wordings never used as a
                    training input: the same anchor text never crosses splits, in any occupation.
                    Each occupation keeps at least one training anchor.
                    """
                    def bucket(key):
                        h = _anchor_hash(seed, key)
                        return 'train' if h < fractions[0] else 'val' if h < fractions[0] + fractions[1] else 'test'
                    split = {}
                    for anchors in anchors_by_soc.values():
                        for a in anchors:
                            split.setdefault(norm(a), bucket(norm(a)))
                    for soc in sorted(anchors_by_soc):
                        keys = [norm(a) for a in anchors_by_soc[soc]]
                        if keys and not any(split[k] == 'train' for k in keys):
                            split[min(keys, key=lambda k: _anchor_hash(seed, k))] = 'train'
                    return split

                def build_title_examples(onet, seed=42, split_of=None):
                    """Return {split: [{'input_text', 'target_text', 'soc', 'anchor'}]} in the runner's
                    prompt format. ``split_of`` maps normalised anchors to splits (default: split_by_anchor)."""
                    rng = random.Random(seed)
                    anchors_by_soc = occupation_anchors(onet)
                    if split_of is None:
                        split_of = split_by_anchor({s: a for s, (a, _, _) in anchors_by_soc.items()}, seed=seed)
                    out = {'train': [], 'val': [], 'test': []}
                    for soc, (anchors, neutral, all_titles) in anchors_by_soc.items():
                        for level in LEVELS:
                            pool = level_pool(level, neutral, all_titles)
                            for anchor in anchors:
                                targets = [t for t in pool if norm(t) != norm(anchor)][:MAX_TARGET_TITLES]
                                if len(targets) < MIN_TARGET_TITLES:
                                    continue
                                out[split_of[norm(anchor)]].append({
                                    'input_text': f'expand titles: {anchor} | skills: '
                                                  f'{skills_text(onet["skills"].get(soc, []), rng)} | level: {level}',
                                    'target_text': ', '.join(targets),
                                    'soc': soc,
                                    'anchor': anchor,
                                })
                        out['train'] += extra_anchor_rows(onet, soc, neutral, all_titles, split_of, seed, rng)
                    return out

                def extra_anchor_rows(onet, soc, neutral, all_titles, split_of, seed, rng):
                    """D-010: more ways to say the same job, for training only.

                    Job titles that are not already anchors, carry no level word, and are not the
                    wording of any val/test anchor (in any occupation) become level-ANY inputs whose
                    targets are the occupation's neutral titles.
                    """
                    extra = [t for t in all_titles
                             if norm(t) not in split_of and not ANY_LEVEL.search(t)]
                    extra = sorted(dict.fromkeys(extra), key=lambda t: _anchor_hash(seed, norm(t)))
                    rows = []
                    for anchor in extra[:MAX_EXTRA_ANCHORS_PER_OCCUPATION]:
                        targets = [t for t in neutral if norm(t) != norm(anchor)][:MAX_TARGET_TITLES]
                        if len(targets) < MIN_TARGET_TITLES:
                            continue
                        rows.append({
                            'input_text': f'expand titles: {anchor} | skills: '
                                          f'{skills_text(onet["skills"].get(soc, []), rng)} | level: ANY',
                            'target_text': ', '.join(targets),
                            'soc': soc,
                            'anchor': anchor,
                        })
                    return rows

                def novel_wording(examples):
                    """Normalised test anchors never seen in training, as an input or as a target."""
                    seen = {norm(r['anchor']) for r in examples['train']}
                    seen |= {norm(t) for r in examples['train'] for t in parse_titles(r['target_text'])}
                    return {norm(r['anchor']) for r in examples['test']} - seen

                def title_dictionary(onet):
                    """Every known O*NET title, normalised: the 'approved occupational dictionary'."""
                    titles = set()
                    for soc, t in onet['occupations'].items():
                        titles.add(norm(t))
                    for table in (onet['reported'], onet['job_titles']):
                        for lst in table.values():
                            titles.update(norm(t) for t in lst)
                    return titles

                def dictionary_titles(onet):
                    """Comma-free O*NET titles: the constrained-decoding vocabulary (titles.json)."""
                    titles = [t for t in onet['occupations'].values() if ',' not in t]
                    for table in (onet['reported'], onet['job_titles']):
                        for lst in table.values():
                            titles += [t for t in lst if ',' not in t]
                    return sorted(dict.fromkeys(titles), key=str.lower)

                def title_occupations(onet):
                    """Normalised title -> set of O*NET-SOC codes that list it."""
                    index = defaultdict(set)
                    for soc, t in onet['occupations'].items():
                        index[norm(t)].add(soc)
                    for table in (onet['reported'], onet['job_titles']):
                        for soc, lst in table.items():
                            for t in lst:
                                index[norm(t)].add(soc)
                    return index

                def occupation_precision(soc_and_titles, onet, index):
                    """Share of generated titles belonging to the input occupation or to an O*NET
                    'Primary-Short' related occupation (D-007 metric, replaces ROUGE-L)."""
                    hit = total = 0
                    for soc, titles in soc_and_titles:
                        ok = {soc} | {r for r, tier in onet['related'].get(soc, []) if tier == 'Primary-Short'}
                        for t in titles:
                            total += 1
                            hit += bool(index.get(norm(t), set()) & ok)
                    return hit / total if total else 0.0

                def parse_titles(text):
                    return [t.strip() for t in text.split(',') if t.strip()]

                def valid_title_ratio(predictions, dictionary):
                    titles = [t for p in predictions for t in parse_titles(p)]
                    return sum(norm(t) in dictionary for t in titles) / len(titles) if titles else 0.0

                def repetition_rate(predictions):
                    rates = []
                    for p in predictions:
                        ts = [norm(t) for t in parse_titles(p)]
                        rates.append((len(ts) - len(set(ts))) / len(ts) if ts else 0.0)
                    return sum(rates) / len(rates) if rates else 0.0
                ''',
                testable=True,
            ),
            code(
                r'''
                onet = load_onet(ONET_DIR)
                examples = build_title_examples(onet, seed=SEED)
                DICTIONARY = title_dictionary(onet)
                for name, rows in examples.items():
                    print(f'{name}: {len(rows)} examples from {len({r["soc"] for r in rows})} occupations')
                # D-009: inputs are disjoint across splits; occupations are shared on purpose.
                overlap = {norm(r['anchor']) for r in examples['train']} & {norm(r['anchor']) for r in examples['test']}
                assert not overlap, 'input-title leakage between train and test'
                assert {r['soc'] for r in examples['test']} <= {r['soc'] for r in examples['train']}
                NOVEL = novel_wording(examples)
                print(f'Test anchors never seen in training (input or target): {len(NOVEL)}')
                print('Sample:', examples['train'][0])
                '''
            ),
            code(version_guard({'transformers': '4.46.3', 'datasets': '3.1.0'})),
            code(
                rf'''
                import json, shutil
                import numpy as np, torch
                from transformers import (AutoModelForSeq2SeqLM, AutoTokenizer, DataCollatorForSeq2Seq,
                                          Seq2SeqTrainer, Seq2SeqTrainingArguments, set_seed)
                set_seed(SEED)
                BASE_MODEL = 'google/flan-t5-small'
                MAX_INPUT_LEN, MAX_TARGET_LEN = 128, 64
                # D-004: to skip training and re-export an accepted v{ML001_REUSABLE_VERSION} model, upload its bundle
                # as ONE archive (title_expander_bundle.tar.gz or a .zip) to a private Kaggle dataset,
                # attach it, and set this to the dataset folder, e.g. '/kaggle/input/findrr-title-expander-v200'.
                REUSE_BUNDLE_DIR = None
                REUSED_BUNDLE = None
                if REUSE_BUNDLE_DIR:
                    import hashlib, tarfile, zipfile
                    src = Path(REUSE_BUNDLE_DIR)
                    hits = list(src.rglob('manifest.json')) if src.is_dir() else []
                    if not hits:
                        # Kaggle datasets hold files, not folders: accept the bundle as one archive
                        # (.tar.gz or .zip), whether or not Kaggle unpacked it on upload.
                        archives = [src] if src.is_file() else sorted(
                            p for p in src.rglob('*') if p.name.endswith(('.tar.gz', '.tgz', '.zip')))
                        if len(archives) != 1:
                            raise RuntimeError(f'Expected one bundle archive under {{src}}, found {{len(archives)}}.')
                        unpacked = Path('/kaggle/working/reused-bundle')
                        shutil.rmtree(unpacked, ignore_errors=True); unpacked.mkdir(parents=True)
                        if archives[0].name.endswith('.zip'):
                            with zipfile.ZipFile(archives[0]) as zf:
                                names = zf.namelist()
                                if any(n.startswith('/') or '..' in Path(n).parts for n in names):
                                    raise RuntimeError('Unsafe path in the bundle archive.')
                                zf.extractall(unpacked)
                        else:
                            with tarfile.open(archives[0]) as tar:
                                members = tar.getmembers()
                                if any(not (m.isfile() or m.isdir()) or m.name.startswith('/')
                                       or '..' in Path(m.name).parts for m in members):
                                    raise RuntimeError('Unsafe entry in the bundle archive.')
                                tar.extractall(unpacked, members=members)
                        hits = list(unpacked.rglob('manifest.json'))
                    if len(hits) != 1:
                        raise RuntimeError(f'Expected exactly one manifest.json under {{src}}, found {{len(hits)}}.')
                    src = hits[0].parent
                    src_manifest = json.loads(hits[0].read_text())
                    if (src_manifest.get('model_id'), src_manifest.get('version')) != ('ML-001', '{ML001_REUSABLE_VERSION}'):
                        raise RuntimeError(f'Not an ML-001 v{ML001_REUSABLE_VERSION} bundle: {{src_manifest.get("model_id")}} {{src_manifest.get("version")}}')
                    if not src_manifest['metadata']['acceptance']['passed']:
                        raise RuntimeError('The reused bundle did not pass acceptance; refusing to re-export it.')
                    for name, digest in src_manifest['files'].items():
                        if hashlib.sha256((src / name).read_bytes()).hexdigest() != digest:
                            raise RuntimeError(f'Checksum mismatch in the reused bundle: {{name}}')
                    REUSED_BUNDLE = {{'version': src_manifest['version'], 'export_date': src_manifest['export_date'],
                                     'manifest_sha256': hashlib.sha256(hits[0].read_bytes()).hexdigest()}}
                    print('Reusing verified bundle (no training):', REUSED_BUNDLE)
                    tokenizer = AutoTokenizer.from_pretrained(str(src))
                    model = AutoModelForSeq2SeqLM.from_pretrained(str(src))
                else:
                    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
                    model = AutoModelForSeq2SeqLM.from_pretrained(BASE_MODEL)

                if REUSED_BUNDLE is None:
                    from datasets import Dataset

                    def tokenize(batch):
                        enc = tokenizer(batch['input_text'], max_length=MAX_INPUT_LEN, truncation=True)
                        enc['labels'] = tokenizer(text_target=batch['target_text'], max_length=MAX_TARGET_LEN,
                                                  truncation=True)['input_ids']
                        return enc

                    ds = {{k: Dataset.from_list(v).map(tokenize, batched=True, remove_columns=['input_text', 'target_text', 'soc', 'anchor'])
                          for k, v in examples.items()}}

                    # FP16 is off: T5 checkpoints are known to overflow in fp16 and the T4 has no bf16.
                    # flan-t5-small trains comfortably in fp32 on a T4.
                    args = Seq2SeqTrainingArguments(
                        output_dir='/kaggle/working/ml001-checkpoints',
                        learning_rate=3e-4, lr_scheduler_type='cosine', warmup_ratio=0.1,
                        num_train_epochs=15, per_device_train_batch_size=32, per_device_eval_batch_size=64,
                        weight_decay=0.01, eval_strategy='epoch', save_strategy='epoch',
                        load_best_model_at_end=True, metric_for_best_model='eval_loss', save_total_limit=1,
                        fp16=False, logging_steps=50, seed=SEED, report_to='none',
                    )
                    trainer = Seq2SeqTrainer(model=model, args=args, train_dataset=ds['train'], eval_dataset=ds['val'],
                                             data_collator=DataCollatorForSeq2Seq(tokenizer, model=model),
                                             processing_class=tokenizer)
                    trainer.train()
                    model = trainer.model  # best checkpoint (load_best_model_at_end)
                '''
            ),
            md(
                """
                ## Export to ONNX (D-004), then evaluate the exported files

                The export writes `encoder.onnx`, a KV-cached one-step `decoder.onnx` and
                `embeddings.npy`, and stops if the ONNX logits differ from the model's own
                logits. Evaluation then uses only those files and the app's decoding code.
                """
            ),
            code(
                rf'''
                import shutil
                EXPORT_DIR = Path('/kaggle/working/title-expander-v{ML001_VERSION}')
                shutil.rmtree(EXPORT_DIR, ignore_errors=True); EXPORT_DIR.mkdir(parents=True)
                ONNX_PARITY = export_t5_bundle(model, EXPORT_DIR)
                print('ONNX parity:', ONNX_PARITY)
                model.config.save_pretrained(EXPORT_DIR)
                tokenizer.save_pretrained(EXPORT_DIR)
                for leftover in ('spiece.model', 'generation_config.json'):
                    (EXPORT_DIR / leftover).unlink(missing_ok=True)  # not used by the ONNX runner
                '''
            ),
            code(
                r'''
                from rouge_score import rouge_scorer
                import sacrebleu

                MAX_NEW_TOKENS = 64  # == MAX_TARGET_LEN, so 5 titles are not cut off
                NUM_BEAMS = 2
                # D-010: 1.0 (off). The constraint already prevents repeated titles, and a token
                # penalty works against correct sibling titles, which share words.
                REPETITION_PENALTY = 1.0
                # The app's own inference path: ONNX Runtime + tokenizers, no torch (D-004).
                onnx_tokenizer = TokenizersAdapter(EXPORT_DIR / 'tokenizer.json', max_length=MAX_INPUT_LEN)
                onnx_generator = T5OnnxGenerator(EXPORT_DIR)
                # D-007: decoding is constrained to real O*NET titles; repeats cannot be completed.
                DICTIONARY_TITLES = dictionary_titles(onet)
                constraint = TitleTrieConstraint(DICTIONARY_TITLES, onnx_tokenizer, max_titles=MAX_TARGET_TITLES)
                print(f'Constrained vocabulary: {len(constraint.titles)} titles ({len(constraint.skipped)} skipped)')

                def generate(texts):
                    """Returns (raw decoded text, complete distinct titles) per input, as the runner does."""
                    raw, titles = [], []
                    for text in texts:
                        out = onnx_generator.generate(onnx_tokenizer(text)['input_ids'], constraint.allowed_tokens,
                                                      num_beams=NUM_BEAMS, max_new_tokens=MAX_NEW_TOKENS)
                        raw.append(onnx_tokenizer.decode(out, skip_special_tokens=True))
                        titles.append(constraint.complete_titles(out, onnx_tokenizer))
                    return raw, titles

                test_rows = examples['test']
                raw_preds, title_preds = generate([r['input_text'] for r in test_rows])
                test_targets = [r['target_text'] for r in test_rows]
                INDEX = title_occupations(onet)
                scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
                measured = {
                    'occupation_precision': occupation_precision(
                        [(r['soc'], t) for r, t in zip(test_rows, title_preds)], onet, INDEX),
                    # Measured on the raw text, so a title cut off by max length counts as invalid.
                    'valid_title_ratio': valid_title_ratio(raw_preds, DICTIONARY),
                    'repetition_rate': repetition_rate(raw_preds),
                    'mean_distinct_titles': float(np.mean([len(t) for t in title_preds])),
                    # Reported only (D-009): inputs whose wording never appeared in training at all.
                    'occupation_precision_novel_wording': occupation_precision(
                        [(r['soc'], t) for r, t in zip(test_rows, title_preds) if norm(r['anchor']) in NOVEL],
                        onet, INDEX),
                    'novel_wording_examples': float(sum(norm(r['anchor']) in NOVEL for r in test_rows)),
                    # Reported only (D-007): agreement with one arbitrary 5-title reference.
                    'rougeL': float(np.mean([scorer.score(t, p)['rougeL'].fmeasure for t, p in zip(test_targets, raw_preds)])),
                    'bleu4': float(sacrebleu.corpus_bleu(raw_preds, [test_targets]).score / 100.0),
                    'test_examples': float(len(raw_preds)),
                }
                # Reported only (D-010): the same metric on seeded training inputs, to show under-fitting.
                train_sample = random.Random(SEED).sample(examples['train'], min(500, len(examples['train'])))
                _, train_titles = generate([r['input_text'] for r in train_sample])
                measured['occupation_precision_train_sample'] = occupation_precision(
                    [(r['soc'], t) for r, t in zip(train_sample, train_titles)], onet, INDEX)
                demo_raw, demo_titles = generate(['expand titles: Software Developer | skills: Python, SQL, Git | level: ANY'])
                measured['ac_ml_001_1_distinct_titles'] = float(len(demo_titles[0]))
                print('Software Developer ->', demo_titles[0])
                for r, t in list(zip(test_rows, title_preds))[:15]:
                    print(f"  {r['anchor']!r:40} -> {t}")
                print(json.dumps(measured, indent=2))
                '''
            ),
            MANIFEST_CELL,
            code(
                r'''
                # Criteria from docs/ml/models/title-expander.md as amended by D-007 (option 1).
                # OCCUPATION_PRECISION_THRESHOLD was approved by the owner (PR #27). D-009 moved the
                # split to held-out input titles, so every occupation's titles are learnable.
                # Reference points (O*NET 31.0): random dictionary title ~0.007, same SOC major
                # group ~0.12, same SOC broad group (e.g. 15-125x) ~0.74, gold references 1.0.
                OCCUPATION_PRECISION_THRESHOLD = 0.75
                ACCEPTANCE = check_acceptance(measured, {
                    'occupation_precision': ('>=', OCCUPATION_PRECISION_THRESHOLD),
                    'valid_title_ratio': ('>=', 0.85),
                    'repetition_rate': ('<', 0.05),
                    'ac_ml_001_1_distinct_titles': ('>=', 3),
                })
                '''
            ),
            gate_cell("ML-001"),
            code(
                rf'''
                import tarfile
                (EXPORT_DIR / 'preprocess_config.json').write_text(json.dumps({{
                    'max_input_length': MAX_INPUT_LEN, 'max_target_length': MAX_TARGET_LEN,
                    'input_template': 'expand titles: {{title}} | skills: {{skills}} | level: {{level}}',
                    'levels': LEVELS, 'num_beams': NUM_BEAMS, 'do_sample': False,
                    'repetition_penalty': REPETITION_PENALTY, 'max_new_tokens': MAX_NEW_TOKENS,
                    'constrained_decoding': True, 'max_titles': MAX_TARGET_TITLES,
                }}, indent=2))
                # Constrained-decoding dictionary, read by findrr TitleExpanderRunner (D-007).
                (EXPORT_DIR / 'titles.json').write_text(json.dumps(constraint.titles, ensure_ascii=False))
                import transformers, onnxruntime as ort
                manifest = build_manifest(
                    EXPORT_DIR, 'ML-001', 'title-expander', '{ML001_VERSION}', 'google/flan-t5-small (ONNX fp32, KV-cached decoder)',
                    evaluation_summary=measured, acceptance=ACCEPTANCE,
                    metadata={{'dataset': f'O*NET {{ONET_VERSION}} (CC BY 4.0)', 'dataset_sha256': ONET_SHA256,
                              'split': 'by input title (anchor), hashed 80/10/10; every occupation in training (D-009)',
                              'examples': {{k: len(v) for k, v in examples.items()}}, 'seed': SEED,
                              'transformers': transformers.__version__, 'torch': torch.__version__,
                              'onnxruntime': ort.__version__, 'onnx_parity': ONNX_PARITY,
                              'reused_bundle': REUSED_BUNDLE}},
                )
                (EXPORT_DIR / 'manifest.json').write_text(json.dumps(manifest, indent=2))
                BUNDLE = '/kaggle/working/title_expander_bundle.tar.gz'
                with tarfile.open(BUNDLE, 'w:gz') as tar:
                    for p in sorted(EXPORT_DIR.iterdir()):
                        tar.add(p, arcname=p.name)
                print(json.dumps(manifest, indent=2))
                '''
            ),
            verify_cell("/kaggle/working/title_expander_bundle.tar.gz"),
        ]
    )


# --------------------------------------------------------------------------------------------
# ML-002: similarity evaluator
# --------------------------------------------------------------------------------------------

ML002_VERSION = "1.1.0"


def similarity_evaluator_notebook() -> dict:
    return notebook(
        [
            md(
                f"""
                # Findrr ML-002: Similarity Evaluator - training and export (v{ML002_VERSION})

                Implements `docs/ml/models/similarity-evaluator.md`: contrastive fine-tuning of
                `sentence-transformers/all-MiniLM-L6-v2` with MultipleNegativesSymmetricRankingLoss,
                exported to INT8 ONNX for the Findrr CPU runner.

                **Data:** O*NET 31.0 (public, CC BY 4.0). Positives are titles of the same occupation.
                Splits keep every occupation in exactly one of train/val/test.

                **Evaluation labels are a proxy:** no human-labelled title-similarity benchmark is
                available, so graded labels come from O*NET structure (same occupation = 3,
                Primary-Short related = 2, Primary-Long related = 1, different major group = 0).
                All metrics are computed with the exported INT8 ONNX model, using the same pooling
                as the Findrr runner.

                **Run on Kaggle:** GPU T4, Internet on, Run All. Extract
                `similarity_evaluator_bundle.tar.gz` into `models/similarity-evaluator/v{ML002_VERSION}/`.
                """
            ),
            ENV_REPORT,
            code(
                """
                # Pure-Python libraries are pinned exactly; compiled ones (onnx, onnxruntime) get a
                # minimum version so pip can choose a prebuilt wheel for Kaggle's Python version.
                # The versions actually used are recorded in the manifest metadata.
                !pip install -q --prefer-binary sentence-transformers==3.3.1 transformers==4.46.3 \\
                    datasets==3.1.0 accelerate==1.1.1 "onnx>=1.17.0" "onnxruntime>=1.20.1"
                """
            ),
            ONET_CONFIG,
            ONET_DOWNLOAD,
            ONET_LOADER,
            code(
                r'''
                MAX_TITLES_PER_OCCUPATION = 20
                MAX_PAIRS_PER_OCCUPATION = 50
                EVAL_PAIRS_PER_TIER = 600
                SAMPLES_PER_OCCUPATION = 3
                TIER_LABEL = {'same': 3, 'Primary-Short': 2, 'Primary-Long': 1, 'unrelated': 0}

                def occupation_titles(onet, soc):
                    titles = [onet['occupations'][soc]] + onet['reported'].get(soc, []) + onet['job_titles'].get(soc, [])
                    seen, out = set(), []
                    for t in titles:
                        if norm(t) not in seen:
                            seen.add(norm(t)); out.append(t)
                    return out[:MAX_TITLES_PER_OCCUPATION]

                def build_training_pairs(onet, split_of, seed=42):
                    rng = random.Random(seed)
                    pairs = []
                    for soc in sorted(s for s, sp in split_of.items() if sp == 'train'):
                        titles = occupation_titles(onet, soc)
                        combos = [(a, b) for i, a in enumerate(titles) for b in titles[i + 1:]]
                        rng.shuffle(combos)
                        pairs += [{'anchor': a, 'positive': b} for a, b in combos[:MAX_PAIRS_PER_OCCUPATION]]
                    rng.shuffle(pairs)
                    return pairs

                def build_graded_pairs(onet, split_of, split, seed=42):
                    """Graded (text_a, text_b, label) pairs; both occupations outside the train split."""
                    rng = random.Random(seed)
                    socs = sorted(s for s, sp in split_of.items() if sp == split)
                    held_out = {s for s, sp in split_of.items() if sp != 'train'}
                    tiers = {k: [] for k in TIER_LABEL}
                    for soc in socs:
                        titles = occupation_titles(onet, soc)
                        for _ in range(SAMPLES_PER_OCCUPATION if len(titles) >= 2 else 0):
                            a, b = rng.sample(titles, 2)
                            tiers['same'].append((a, b, TIER_LABEL['same']))
                        for other, tier in onet['related'].get(soc, []):
                            if tier in TIER_LABEL and other in held_out and other in onet['occupations']:
                                tiers[tier].append((rng.choice(titles), rng.choice(occupation_titles(onet, other)), TIER_LABEL[tier]))
                        far = [s for s in socs if s[:2] != soc[:2]]
                        for _ in range(SAMPLES_PER_OCCUPATION if far else 0):
                            other = rng.choice(far)
                            tiers['unrelated'].append((rng.choice(titles), rng.choice(occupation_titles(onet, other)), 0))
                    out = []
                    for rows in tiers.values():
                        rng.shuffle(rows)
                        out += rows[:EVAL_PAIRS_PER_TIER]
                    return out

                def _ranks(values):
                    order = sorted(range(len(values)), key=lambda i: values[i])
                    ranks = [0.0] * len(values)
                    i = 0
                    while i < len(order):
                        j = i
                        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
                            j += 1
                        for k in range(i, j + 1):
                            ranks[order[k]] = (i + j) / 2.0
                        i = j + 1
                    return ranks

                def pearson(x, y):
                    n = len(x); mx = sum(x) / n; my = sum(y) / n
                    cov = sum((a - mx) * (b - my) for a, b in zip(x, y))
                    vx = sum((a - mx) ** 2 for a in x) ** 0.5; vy = sum((b - my) ** 2 for b in y) ** 0.5
                    return cov / (vx * vy) if vx and vy else 0.0

                def spearman(x, y):
                    return pearson(_ranks(list(x)), _ranks(list(y)))

                def precision_at(scores, labels, threshold, relevant_min_label=2):
                    """Share of pairs scored >= threshold that are relevant (same occupation or Primary-Short)."""
                    picked = [l for s, l in zip(scores, labels) if s >= threshold]
                    return sum(l >= relevant_min_label for l in picked) / len(picked) if picked else 0.0
                ''',
                testable=True,
            ),
            code(
                r'''
                onet = load_onet(ONET_DIR)
                split_of = split_by_occupation(onet['occupations'], seed=SEED)
                train_pairs = build_training_pairs(onet, split_of, seed=SEED)
                val_pairs = build_graded_pairs(onet, split_of, 'val', seed=SEED)
                test_pairs = build_graded_pairs(onet, split_of, 'test', seed=SEED + 1)
                print(f'train pairs: {len(train_pairs)}, val graded: {len(val_pairs)}, test graded: {len(test_pairs)}')
                '''
            ),
            code(version_guard({'transformers': '4.46.3', 'datasets': '3.1.0',
                                'sentence_transformers': '3.3.1'})),
            code(
                r'''
                import numpy as np, torch
                from datasets import Dataset
                from sentence_transformers import (SentenceTransformer, SentenceTransformerTrainer,
                                                   SentenceTransformerTrainingArguments, losses)
                from sentence_transformers.evaluation import EmbeddingSimilarityEvaluator
                from sentence_transformers.training_args import BatchSamplers
                from transformers import set_seed
                set_seed(SEED)
                BASE_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
                model = SentenceTransformer(BASE_MODEL)
                model.max_seq_length = 128
                loss = losses.MultipleNegativesSymmetricRankingLoss(model)
                val_eval = EmbeddingSimilarityEvaluator([a for a, _, _ in val_pairs], [b for _, b, _ in val_pairs],
                                                        [l / 3.0 for _, _, l in val_pairs], name='onet-val')
                args = SentenceTransformerTrainingArguments(
                    output_dir='/kaggle/working/ml002-checkpoints', num_train_epochs=4,
                    per_device_train_batch_size=64, learning_rate=2e-5, warmup_ratio=0.1,
                    fp16=torch.cuda.is_available(), batch_sampler=BatchSamplers.NO_DUPLICATES,
                    eval_strategy='epoch', save_strategy='epoch', save_total_limit=1,
                    load_best_model_at_end=True, metric_for_best_model='eval_onet-val_spearman_cosine',
                    seed=SEED, report_to='none',
                )
                trainer = SentenceTransformerTrainer(model=model, args=args, train_dataset=Dataset.from_list(train_pairs),
                                                     loss=loss, evaluator=val_eval)
                trainer.train()
                '''
            ),
            md("## Export to ONNX, quantise to INT8, then evaluate the shipped model"),
            code(
                rf'''
                import shutil
                import onnxruntime as ort
                from onnxruntime.quantization import QuantType, quantize_dynamic
                EXPORT_DIR = Path('/kaggle/working/similarity-evaluator-v{ML002_VERSION}')
                shutil.rmtree(EXPORT_DIR, ignore_errors=True); EXPORT_DIR.mkdir(parents=True)
                hf_model = model[0].auto_model.cpu().eval()
                tok = model.tokenizer
                dummy = tok(['Software Engineer', 'Registered Nurse'], return_tensors='pt', padding=True)
                fp32_path = Path('/kaggle/working/ml002-fp32.onnx')
                torch.onnx.export(
                    hf_model, (dummy['input_ids'], dummy['attention_mask'], dummy['token_type_ids']), str(fp32_path),
                    input_names=['input_ids', 'attention_mask', 'token_type_ids'], output_names=['last_hidden_state'],
                    dynamic_axes={{n: {{0: 'batch', 1: 'seq'}} for n in ['input_ids', 'attention_mask', 'token_type_ids', 'last_hidden_state']}},
                    opset_version=17,
                )
                quantize_dynamic(str(fp32_path), str(EXPORT_DIR / 'model.onnx'), weight_type=QuantType.QInt8)
                tok.save_pretrained(EXPORT_DIR)
                (EXPORT_DIR / 'config.json').write_text(json.dumps({{
                    'embedding_dimension': 384, 'max_seq_length': 128, 'pooling': 'mean', 'normalize': True}}, indent=2))
                (EXPORT_DIR / 'preprocess_config.json').write_text(json.dumps({{'lowercase': True, 'strip_accents': True}}, indent=2))

                session = ort.InferenceSession(str(EXPORT_DIR / 'model.onnx'), providers=['CPUExecutionProvider'])

                def onnx_embed(text):
                    """Identical to findrr SimilarityEvaluatorRunner._embed_text."""
                    enc = tok(text, truncation=True, max_length=128, return_tensors='np')
                    feeds = {{'input_ids': enc['input_ids'], 'attention_mask': enc['attention_mask']}}
                    if 'token_type_ids' in [i.name for i in session.get_inputs()]:
                        feeds['token_type_ids'] = enc.get('token_type_ids', np.zeros_like(enc['input_ids']))
                    tokens = session.run(None, feeds)[0]
                    mask = np.expand_dims(enc['attention_mask'], -1)
                    emb = (tokens * mask).sum(1) / np.clip(mask.sum(1), 1e-9, None)
                    emb = emb / np.clip(np.linalg.norm(emb, axis=1, keepdims=True), 1e-9, None)
                    return emb[0]

                def onnx_sim(a, b):
                    return float(np.clip(np.dot(onnx_embed(a), onnx_embed(b)), 0.0, 1.0))
                '''
            ),
            code(
                r'''
                scores = [onnx_sim(a, b) for a, b, _ in test_pairs]
                labels = [l for _, _, l in test_pairs]
                st = model.to('cpu')
                parity = float(np.mean([np.dot(onnx_embed(t), st.encode(t, normalize_embeddings=True))
                                        for t, _, _ in test_pairs[:200]]))
                measured = {
                    'pearson_r': pearson(scores, labels),
                    'spearman_rho': spearman(scores, labels),
                    'precision_at_0_70': precision_at(scores, labels, 0.70),
                    'ac_ml_002_1_synonym_similarity': onnx_sim('Software Developer', 'Software Engineer'),
                    'ac_ml_002_2_distinct_similarity': onnx_sim('Software Developer', 'Dental Assistant'),
                    'onnx_int8_vs_pytorch_cosine': parity,
                    'test_pairs': float(len(test_pairs)),
                }
                print(json.dumps(measured, indent=2))
                '''
            ),
            MANIFEST_CELL,
            code(
                r'''
                # Thresholds copied verbatim from docs/ml/models/similarity-evaluator.md (approved).
                # Pearson r and Spearman rho are reported in `measured` but do not gate the
                # export (D-008): the O*NET proxy labels cap them.
                ACCEPTANCE = check_acceptance(measured, {
                    'precision_at_0_70': ('>=', 0.90),
                    'ac_ml_002_1_synonym_similarity': ('>=', 0.85),
                    'ac_ml_002_2_distinct_similarity': ('<', 0.30),
                })
                '''
            ),
            gate_cell("ML-002"),
            code(
                rf'''
                import tarfile, sentence_transformers, transformers
                manifest = build_manifest(
                    EXPORT_DIR, 'ML-002', 'similarity-evaluator', '{ML002_VERSION}',
                    'sentence-transformers/all-MiniLM-L6-v2 (ONNX INT8, mean pooling)',
                    evaluation_summary=measured, acceptance=ACCEPTANCE,
                    metadata={{'dataset': f'O*NET {{ONET_VERSION}} (CC BY 4.0)', 'dataset_sha256': ONET_SHA256,
                              'evaluation_labels': 'proxy graded labels from O*NET structure (0-3)',
                              'split': 'by occupation, stratified by SOC major group (80/10/10)',
                              'train_pairs': len(train_pairs), 'seed': SEED,
                              'sentence_transformers': sentence_transformers.__version__,
                              'transformers': transformers.__version__, 'onnxruntime': ort.__version__}},
                )
                (EXPORT_DIR / 'manifest.json').write_text(json.dumps(manifest, indent=2))
                BUNDLE = '/kaggle/working/similarity_evaluator_bundle.tar.gz'
                with tarfile.open(BUNDLE, 'w:gz') as tar:
                    for p in sorted(EXPORT_DIR.iterdir()):
                        tar.add(p, arcname=p.name)
                print(json.dumps(manifest, indent=2))
                '''
            ),
            verify_cell("/kaggle/working/similarity_evaluator_bundle.tar.gz"),
        ]
    )


def main() -> None:
    outputs = {
        Path("notebooks/01_train_title_expander.ipynb"): title_expander_notebook(),
        Path("notebooks/02_train_similarity_evaluator.ipynb"): similarity_evaluator_notebook(),
    }
    for path, nb in outputs.items():
        path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Generated {path}")


if __name__ == "__main__":
    main()
