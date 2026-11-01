# Design Documentation Checklist

The Software Design Documentation Set evolves progressively with the application. It is not written all at once. For each iteration, create or extend only the documents the iteration's scope requires, and record which ones in `docs/STATUS.md`.

Significant design decisions must be documented with their rationale and relevant alternatives. Material changes need user approval (see `docs/process/approval-gates.md`).

---

## Document set

| Document | Purpose | Created or updated when |
|---|---|---|
| Software Architecture Document | Defines the application's architecture, components, responsibilities, and communication | Initial design; whenever architecture changes |
| Architecture diagrams | Visual overview of the system | With the architecture document |
| Component diagrams | Components and their relationships | With the architecture document |
| Database Design Document | Entities, relationships, schemas, and constraints | Before implementing data structures; on schema changes |
| Entity-Relationship Diagrams | Visual data model | With the database design document |
| API specifications | Interfaces and communication contracts | Before implementing or integrating APIs |
| Data-flow diagrams | How data moves through processing workflows | When workflows are designed or changed |
| Technical design specifications | Implementation-level technical decisions and contracts | Per feature or iteration |
| Machine Learning Architecture Document | Model development, training, inference, and deployment architecture | ML planning; on ML architecture changes |
| Model specifications | Each model's purpose, architecture, inputs, outputs, and requirements | Per model, before its notebook is written |
| Model inference specifications | Inference interfaces, loading, and failure handling | With the ML architecture |
| UI/UX designs | User journeys, layouts, and interactions (see `ui-design-penpot` skill) | Before any UI implementation; needs explicit approval |
| Architecture Decision Records (ADRs) | Significant decisions, rationale, alternatives | Whenever a significant decision is made |

---

## Design activity checklist

For the requirements selected for the current iteration:

- [ ] Design or extend the system architecture.
- [ ] Identify application components and their responsibilities.
- [ ] Define component communication.
- [ ] Design or extend database schemas.
- [ ] Define API contracts.
- [ ] Select appropriate technologies and frameworks (evaluate per `docs/process/dependency-policy.md`).
- [ ] Design user interfaces and user experiences.
- [ ] Establish data-processing workflows.
- [ ] Design external integrations.
- [ ] Design the machine learning architecture.
- [ ] Define model training and inference workflows.
- [ ] Define model artifact transfer and storage.
- [ ] Define model loading and management.
- [ ] Consider security and privacy.
- [ ] Consider scalability and performance.
- [ ] Consider maintainability and extensibility.
- [ ] Identify architectural constraints and dependencies.

---

## ADR template

Store as `docs/adr/NNNN-short-title.md`.

```markdown
# ADR NNNN: <decision title>

- **Status:** proposed / approved / superseded by ADR NNNN
- **Date:** YYYY-MM-DD
- **Requirements addressed:** <FR/NFR/ML IDs>

## Context
<What problem or constraint prompted the decision>

## Options considered
1. <Option A>: advantages, disadvantages
2. <Option B>: advantages, disadvantages

## Decision
<What was chosen, and the rationale>

## Consequences
<Effects on architecture, risk, cost, maintenance, and follow-up work>
```

---

## Consistency checks before requesting approval

- [ ] Every design element traces to an approved requirement, or is flagged as a proposal.
- [ ] Conflicts with existing documents are reported, not silently resolved.
- [ ] Training and inference environments are kept independent but compatible.
- [ ] The design does not depend on Kaggle being available during normal operation.
- [ ] Unresolved questions are in `docs/DECISIONS_PENDING.md`, not buried in the design.
