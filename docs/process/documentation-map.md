# Documentation Map

Maintain the following documents where applicable. The `bootstrap-1-environment` workflow creates the initial skeleton from this table.

| Document | Path | Purpose |
|---|---|---|
| Master Development Prompt | `docs/archive/master-prompt-original.md` | Defines AI agent responsibilities and development instructions. Archived; do not modify. |
| Project Plan | `docs/project-plan.md` | Defines scope, objectives, feasibility, resources, risks, and roadmap. |
| SRS | `docs/requirements/srs.md` | Defines what the application must do. Authoritative source for approved requirements. |
| Product Backlog | `docs/requirements/product-backlog.md` | Tracks prioritised features, stories, tasks, and acceptance criteria. |
| Traceability Matrix | `docs/requirements/traceability-matrix.md` | Links requirements to design, code, tests, releases, and model assets. |
| Software Architecture Document | `docs/design/software-architecture.md` | Defines the application's architecture. |
| Technical Design Specifications | `docs/design/technical-specs.md` | Documents implementation-level technical decisions. |
| Database Design Document | `docs/design/database-design.md` | Defines entities, relationships, schemas, and constraints. |
| API Specification | `docs/design/api-spec.md` | Defines interfaces and communication contracts. |
| UI/UX Documentation | `docs/design/ui-ux.md` | Defines user journeys, layouts, and interactions; links to approved Penpot designs. (`docs/spec/ui.md` is the initial UI specification.) |
| Machine Learning Architecture Document | `docs/ml/ml-architecture.md` | Defines model development, training, inference, and deployment architecture. (`docs/ml/ml-system-design.md` lists what it must establish.) |
| Model Specifications | `docs/ml/models/<model-name>.md` | Define individual models' purposes, architectures, inputs, outputs, and requirements. |
| Model Training Documentation | `docs/ml/training/<model-name>.md` | Explains training methodology, datasets, configurations, and execution. |
| Model Evaluation Reports | `docs/ml/evaluation-reports/<model-name>-<version>.md` | Record model training and evaluation results (from user-supplied evidence only). |
| Model Cards | `docs/ml/model-cards/<model-name>.md` | Document capabilities, intended uses, limitations, and evaluations. |
| Model Manifest or Registry | `docs/ml/model-registry.md` (human-readable); machine-readable manifest location set in the ML Architecture Document | Records model versions and associated metadata. |
| Test Plan | `docs/testing/test-plan.md` | Defines testing strategy and coverage. |
| Test Reports | `docs/testing/reports/` | Records results and defects. |
| Architecture Decision Records | `docs/adr/NNNN-short-title.md` | Records significant architectural decisions. |
| Release Notes | `docs/releases/vX.Y.Z.md` | Documents individual releases. |
| Deployment Documentation | `docs/deployment/deployment-guide.md` | Describes deployment and operational procedures. |

These paths are canonical. Do not create these documents anywhere else. If a document needs a different location, record the decision in `docs/DECISIONS_PENDING.md` and update this table.

Store documentation in an organised and consistent project documentation structure within the repository.
