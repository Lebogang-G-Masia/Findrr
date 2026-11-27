# Model dashboard data tool

A developer tool that builds the data behind the **Findrr Model Observatory**, a private claude.ai dashboard about Findrr's ML models (ML-001, ML-002, ML-003). It is not part of the Findrr app: nothing in `src/` imports it, and it never trains a model. Decision: D-011.

## What it produces

Ten JSON files, each shaped `{rows, meta}`, one per dashboard dataset:

| File | Contents | Source |
|---|---|---|
| `models.json` | Spec, runtime, bundle size, lifecycle, integrity, acceptance | Model specs, registry, bundle manifests, `ModelRegistry.inspect_model_status` |
| `criteria.json` | Gated and reported metrics of the installed bundles | Bundle manifests |
| `runs.json` | Metrics per Kaggle run | `RUN_HISTORY` in `build.py` (from `docs/DECISIONS_PENDING.md`) and the manifests |
| `baselines.json` | ML-001 occupation-precision reference points | `docs/ml/training/title-expander.md` |
| `benchmark.json` | Per-request CPU latency | `bench.py` |
| `resources.json` | Load time, peak process memory, batch latency | `bench.py` |
| `samples.json` | Real outputs for hand-picked inputs | `bench.py` (the app's own runners) |
| `splits.json` | Train, validation and test sizes, evaluation subsets, title dictionary | Manifests, `titles.json`, training docs |
| `labelmix.json` | ML-002 test-pair label mix | D-008 |
| `decisions.json` | ML decisions, open and resolved | `DECISIONS` in `build.py` (from `docs/DECISIONS_PENDING.md`) |

Output goes to `build/model-dashboard/`, which `.gitignore` excludes. Never commit it.

## Page source

- `page.html` is the dashboard page: its HTML, CSS and drawing scripts. On claude.ai it is stored as `files/index.html` of a Data (dashboard) artifact.
- `dashboard.json` lists the dashboard's title and its datasets: each one's id, title, description and data file.

Together with the data files, they recreate the whole dashboard from this repo. If the page is edited on claude.ai, copy it back here.

## Refresh after a Kaggle run or a decision

1. Install the new bundle and run `findrr model inspect ML-00x`. It must report `Integrity Verified: Yes`.
2. If a run or decision is new, add it to `RUN_HISTORY` or `DECISIONS` in `build.py` (with the number of the run the installed bundle came from in `CURRENT_RUN`).
3. With the virtual environment active and the machine otherwise idle, run:

   ```bash
   python scripts/model_dashboard/bench.py
   python scripts/model_dashboard/build.py
   ```

4. Upload the changed files from `build/model-dashboard/data/` to the dashboard (ask Claude to do it).

## Caveats

- `bench.py` runs real CPU inference and needs both bundles installed, plus `torch` for ML-001 (see D-004).
- Latency depends on what else the machine is doing. `bench.py` records the load average and warns when the machine is busy, and `build.py` refuses such a benchmark unless you pass `--allow-busy`. The 0.5 load-per-CPU limit is provisional.
- Peak memory is the whole Python process, runtime included, so it is not directly comparable with the specs' model RAM budgets.
- The samples illustrate behaviour. They are not an evaluation.
