# Model dashboard

Source and data for the **Findrr Model Observatory**, a private claude.ai dashboard about Findrr's ML models (ML-001, ML-002, ML-003). It is a developer tool, not part of the Findrr app: nothing in `src/` imports it, and it never trains a model. Decisions: D-011 (it lives here) and D-012 (its data stays current).

| Path | What it is |
|---|---|
| `page.html` | The dashboard page, with a Models tab and a Development tab: HTML, CSS and drawing scripts (stored on claude.ai as `files/index.html` of a Data artifact) |
| `dashboard.json` | The dashboard's title and datasets: each one's id, title, description and data file |
| `data/` | The dashboard's data, committed so the dashboard can read it from GitHub |
| `build.py` | Rebuilds every file in `data/` except `bench.json` |
| `bench.py` | Measures the installed bundles on this machine and writes `data/bench.json` |
| `hooks/pre-commit` | Runs `build.py` before each commit and adds any data change to the commit |

## How the numbers stay current (D-012)

1. **Before each commit**, the hook rebuilds `data/` from its sources and adds any change to the commit. Install it once per clone:

   ```bash
   git config core.hooksPath scripts/model_dashboard/hooks
   ```

   The hook never blocks a commit. Without `.venv/`, the installed bundles or `data/bench.json`, it does nothing, so CI and fresh clones are unaffected.
2. **When a pull request is merged into `main`**, the cloud scheduled task "Findrr dashboard sync" (claude.ai, Code → Routines) checks out `main`, lists the dashboard files the merge changed, and uploads only those. A merge that touches no dashboard file costs one `git diff`. claude.ai's GitHub integration gives cloud sessions access to the repo, but it is not a connector the page can read from, so a direct live read is not possible (D-012).

What updates by itself, and what doesn't:

| Data | Source | Updates when |
|---|---|---|
| Active versions, architectures, runtimes | The app's registry (`src/findrr/ml/registry.py`) | The commit that changes the registry |
| Metrics, integrity, bundle size, dataset sizes | The active bundle in `models/`. If it is not installed yet, the newest intact earlier bundle, labelled as such | The next commit after a bundle is installed |
| Decisions | `docs/DECISIONS_PENDING.md`, parsed (ML-area entries only) | The commit that edits the log |
| Latency, memory, sample outputs | `data/bench.json` | You re-run `bench.py` on an idle machine and commit |
| Earlier Kaggle runs, model descriptions, budgets, baselines | Typed into `build.py` from the docs | Someone edits `build.py` |

After a new Kaggle run, add the previous current run to `RUN_HISTORY` in `build.py`, bump `CURRENT_RUN`, and add the version to `INTEGRATION_VERIFIED` once real inference is verified. `bench.py` measures only the registry's active bundles, and refuses to run if they are not installed.

## Data files

Each data file is shaped `{rows, meta}`, and `meta` names its sources.

| File | Contents |
|---|---|
| `models.json` | Spec, runtime, bundle size, lifecycle, integrity (checked with `ModelRegistry`), acceptance |
| `criteria.json` | Gated and reported metrics of the installed bundles |
| `runs.json` | Metrics per Kaggle run |
| `baselines.json` | ML-001 occupation-precision reference points |
| `splits.json` | Train, validation and test sizes, evaluation subsets, the title dictionary |
| `labelmix.json` | ML-002 test-pair label mix (D-008) |
| `benchmark.json`, `resources.json`, `samples.json` | Latency, load time and memory, and real outputs, from `bench.json` |
| `decisions.json` | ML decisions from the decision log |
| `provenance.json` | Seed, dataset checksum, split, library versions and notebook of each installed bundle (Development page) |
| `bundlefiles.json` | Each bundle file's size and SHA-256 (Development page) |
| `benchrun.json` | When and how the benchmark ran (Development page) |

## Caveats

- `bench.py` runs real CPU inference. It needs both bundles installed, plus `torch` for ML-001 (see D-004). It refuses to save results from a busy machine (load above 0.5 per CPU, a provisional limit) unless you pass `--allow-busy`.
- Peak memory is the whole Python process, runtime included, so it is not directly comparable with the specs' model RAM budgets.
- The samples illustrate behaviour. They are not an evaluation.
- The repo is public, so everything in `data/` is published. It holds metrics, timings and public O*NET titles only. Never put personal data in it.
