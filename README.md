# Findrr

Findrr is an employment-search and application-preparation application designed to streamline:
- User profile management
- Job posting discovery and scraping
- Tailored CV and cover letter preparation
- End-to-end application tracking

## Status

Milestone 2 (additional CLI functionality). See [`docs/STATUS.md`](docs/STATUS.md).

## Typical CLI flow

```bash
findrr onboard                 # profile -> generalized title -> search configuration
findrr profile use <id>        # switch the active profile (multiple career paths)
findrr terms generate          # Model 1 expansion + Model 2 validation (needs verified artifacts)
findrr search run              # headful search: primary title + accepted terms (2-10 each)
findrr apply analyze <posting> # requirement gap analysis
findrr apply draft <posting>   # fact-grounded CV + cover letter (Markdown)
findrr apply status <app> APPLIED
findrr dashboard
```

## Development Setup

```bash
# Clone the repository
git clone git@github.com:Lebogang-G-Masia/Findrr.git
cd Findrr

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies in editable mode
pip install -e ".[dev]"          # add ",ml" for local ONNX inference: ".[dev,ml]"
cp .env.example .env              # optional overrides
```

## Documentation

Full project documentation is located in [`docs/`](docs/).
- [Project Plan](docs/project-plan.md)
- [Requirements (SRS)](docs/requirements/srs.md)
- [Software Architecture](docs/design/software-architecture.md)
- [Machine Learning Architecture](docs/ml/ml-architecture.md)
