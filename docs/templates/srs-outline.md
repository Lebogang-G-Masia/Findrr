# SRS Outline and Requirements Conventions

Template and conventions for the Software Requirements Specification (SRS). The SRS is the authoritative source for approved application requirements and business rules. Use it with the `srs-and-traceability` skill.

Until a requirement is written into the SRS **and approved**, it is only a proposal. Content in `docs/spec/` is the initial specification, not approved requirements.

---

## 1. Required SRS contents

Include each of the following where applicable:

1. Introduction and project purpose.
2. Scope and objectives.
3. Intended users and user characteristics.
4. Product overview.
5. System context.
6. Functional requirements.
7. Non-functional requirements.
8. Use cases and user workflows.
9. User stories.
10. Acceptance criteria.
11. Business rules.
12. Data requirements.
13. Interface requirements.
14. Integration requirements.
15. Security and privacy requirements.
16. Machine learning requirements.
17. Model inference requirements.
18. System constraints.
19. Assumptions and dependencies.
20. Known limitations.
21. Glossary.

Machine learning requirements must establish each model's intended purpose, required inputs, expected outputs, integration requirements, and acceptance criteria.

---

## 2. Requirement identifiers

Every requirement has a unique, stable identifier.

| Prefix | Meaning | Example |
|---|---|---|
| FR- | Functional requirement | FR-001 |
| NFR- | Non-functional requirement | NFR-001 |
| BR- | Business rule | BR-001 |
| ML- | Machine learning requirement | ML-001 |
| AC- | Acceptance criterion | AC-001 |

Never reuse or renumber an identifier. If a requirement is withdrawn, mark it withdrawn.

---

## 3. Requirement entry template

```markdown
### FR-000: <short title>

- **Description:** <what the application must do>
- **Priority:** <Must / Should / Could>
- **Status:** <proposed / approved / implemented / verified / withdrawn>
- **Source:** <user need, business objective, or module>
- **Depends on:** <requirement IDs>
- **Inputs:** <...>
- **Outputs:** <...>
- **Constraints / business rules:** <BR-IDs>
- **Acceptance criteria:** <AC-IDs>
- **Open questions:** <link to docs/DECISIONS_PENDING.md entries>
```

For ML requirements (ML-xxx), also record: model purpose, required inputs, expected outputs, training and inference requirements, required training data, evaluation criteria and thresholds (provisional until evaluated and approved), artifact requirements, and integration requirements.

---

## 4. Acceptance criteria

Acceptance criteria must describe observable and testable outcomes. Use Given/When/Then structures where appropriate.

```markdown
### AC-000 (verifies FR-000)

- **Given** <initial context or precondition>
- **When** <action or event>
- **Then** <observable, testable outcome>
```

Each important requirement must be traceable through design, implementation, and verification (see the traceability section of the `srs-and-traceability` skill).

---

## 5. Examples

Examples only. They are not approved requirements.

**Functional requirements describe what the application must do.**

- Users must be able to create and manage a User Profile.
- Users must be able to generate alternative job-search titles.
- The application must discover job postings.
- The application must load trained models from its server.
- The application must use trained models for inference.
- Users must be able to prepare CVs and cover letters.

**Non-functional requirements describe quality attributes and operational constraints.** They should be measurable wherever possible.

- The application must protect user information.
- The application must handle external-service failures.
- The application must maintain acceptable performance.
- The application must be maintainable and extensible.
- Model inference must satisfy established performance expectations.
- Missing or incompatible model artifacts must be handled appropriately.

---

## 6. Product backlog contents

The Prioritised Product Backlog must contain:

- Prioritised features.
- User stories.
- Implementation tasks.
- Acceptance criteria.
- Relevant dependencies.

It is the authoritative source for development priorities and work tracking.

---

## 7. Requirements refinement checklist (per iteration)

At the start of each iteration, for each selected requirement establish:

- [ ] Expected functionality
- [ ] Inputs and outputs
- [ ] Constraints
- [ ] Dependencies
- [ ] Acceptance criteria
- [ ] Edge cases and missing information (record questions in `docs/DECISIONS_PENDING.md`)
- [ ] For ML requirements: purpose, inputs and outputs, training data, evaluation methodology, inference and artifact requirements, deployment constraints
