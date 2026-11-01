# Software Development Life Cycle (SDLC)

Generic reference for the six recurring phases. Workflows (`/bootstrap-*`, `/start-iteration`) point here for what each phase means. Phase 5 is summarised here and detailed in the `testing-and-qa` skill, and Phase 6 in `docs/process/release-deployment.md`.

The development process consists of six recurring phases:

1. Planning.
2. Requirements Analysis.
3. System Design.
4. Development (Implementation).
5. Testing and Quality Assurance.
6. Deployment (Release).

These phases are not strictly sequential or performed only once. They must be revisited during each development iteration according to its scope and complexity.

---

## Phase 1: Planning

### Objective

Establish the overall vision, objectives, feasibility, and direction of the project.

Determine whether developing the proposed functionality makes business and technical sense, establish the project scope, estimate resources and costs, and identify high-level risks.

### Activities

You must:

- Establish project objectives and expected outcomes.
- Identify the initial project scope.
- Identify major application modules.
- Conduct technical, operational, and financial feasibility assessments.
- Identify required software, hardware, infrastructure, and external services.
- Identify development constraints and dependencies.
- Estimate costs and resource requirements where sufficient information is available.
- Establish a high-level timeline and development roadmap.
- Identify technical and operational risks.
- Establish initial development priorities.
- Divide development into manageable iterations and milestones.
- Evaluate the feasibility of training and fine-tuning models on Kaggle.
- Evaluate the computational resources needed for server-side inference.
- Identify required datasets and model-development resources.

Planning must be revisited at the beginning of subsequent iterations.

### Primary Deliverable

An **Initial Project Plan and High-Level Roadmap**, supported by:

- Scope statement.
- Feasibility assessment.
- Risk register.
- Resource estimates.
- Development milestone roadmap.
- Initial product backlog.
- Estimated iteration schedule.
- Initial machine learning development and deployment plan.

Estimates must state assumptions, dependencies, and uncertainty. Do not present unsupported estimates as confirmed facts.

---

## Phase 2: Requirements Analysis

### Objective

Determine what the software needs to do by translating business objectives and user needs into clear, actionable, and testable requirements.

### Activities

You must:

- Identify functional requirements.
- Identify non-functional requirements.
- Identify relevant stakeholders and user categories.
- Identify user workflows and use cases.
- Identify business rules.
- Identify system constraints.
- Identify external dependencies and integrations.
- Identify data requirements.
- Define module inputs, outputs, and responsibilities.
- Define acceptance criteria.
- Identify dependencies between requirements.
- Prioritise requirements.
- Identify machine learning requirements.
- Identify the intended responsibilities of each model.
- Establish expected model inputs and outputs.
- Identify training and inference requirements.
- Identify required training data.
- Establish model evaluation criteria.
- Establish model integration and artifact-delivery requirements.

Functional requirements describe what the application must do. Non-functional requirements describe quality attributes and operational constraints, and should be measurable wherever possible. Examples of each are in `docs/templates/srs-outline.md`.

### Requirements Refinement

Requirements must be progressively refined.

At the beginning of each iteration, analyse selected requirements in sufficient detail to establish their expected functionality, inputs, outputs, constraints, dependencies, and acceptance criteria.

Stakeholder feedback and findings from previous iterations may result in requirements being revised or introduced.

### Primary Deliverables

1. An evolving **Software Requirements Specification (SRS)**.
2. A **Prioritised Product Backlog**.

The SRS is the authoritative source for approved application requirements.

The required SRS contents, requirement ID scheme, acceptance-criteria format, and backlog contents are in `docs/templates/srs-outline.md`.

---

## Phase 3: System Design

### Objective

Determine how the software will be designed and structured to satisfy the requirements selected for the current iteration.

### Activities

You must:

- Design or extend the system architecture.
- Identify application components and their responsibilities.
- Define component communication.
- Design or extend database schemas.
- Define API contracts.
- Select appropriate technologies and frameworks.
- Design user interfaces and user experiences.
- Establish data-processing workflows.
- Design external integrations.
- Design the machine learning architecture.
- Define model training and inference workflows.
- Define model artifact transfer and storage.
- Define model loading and management.
- Consider security and privacy.
- Consider scalability and performance.
- Consider maintainability and extensibility.
- Identify architectural constraints and dependencies.

System design must evolve progressively.

Significant design decisions must be documented with their rationale and relevant alternatives (see Architecture Decision Records in `docs/templates/design-docs.md`).

### Machine Learning System Design

The architecture must explicitly distinguish between the training and inference environments. Training takes place on Kaggle; inference takes place on the server hosting Findrr. The environments must be independent but compatible, and the application must not depend on Kaggle being available during normal operation.

The full list of what the ML design must establish is in `docs/ml/ml-system-design.md`.

### Primary Deliverable

An evolving **Software Design Documentation Set**. The checklist of documents is in `docs/templates/design-docs.md`.

---

## Phase 4: Development (Implementation)

### Objective

Transform the requirements and designs selected for the current iteration into a functioning software increment.

### Activities

You must:

- Implement approved requirements.
- Create and extend application components.
- Implement database structures and migrations.
- Develop APIs where required.
- Integrate external services.
- Develop user interfaces.
- Follow coding standards and the approved architecture.
- Maintain separation of concerns.
- Implement error handling and logging.
- Maintain appropriate security controls.
- Write automated tests.
- Review and document significant implementation decisions.

For machine learning functionality, additionally:

- Develop the required Kaggle training notebooks.
- Implement training and evaluation pipelines.
- Prepare model configurations.
- Prepare preprocessing and post-processing pipelines.
- Implement model artifact export.
- Implement application-side model loading.
- Implement inference interfaces and services.
- Ensure artifact compatibility.
- Document notebook execution and artifact transfer.

The training notebooks must be complete enough for the user to transfer to Kaggle and execute themselves. Do not assume that training artifacts are available before the user has supplied them. See the `kaggle-notebook` and `model-inference` skills.

Each iteration must produce a functioning software increment that integrates with previously developed functionality.

### Primary Deliverable

A **Working Software Increment**, including relevant documentation, tests, and model development assets where applicable.

---

## Phase 5: Testing and Quality Assurance

### Objective

Continuously verify that each software increment functions correctly, integrates successfully with existing components, and satisfies its requirements.

### Testing Activities

Perform relevant:

- Unit testing.
- Integration testing.
- System testing.
- Regression testing.
- User acceptance testing.
- Performance testing.
- Security testing.
- Compatibility testing.
- Usability testing.

Identified defects must be documented, prioritised, investigated, and retested after resolution.

At the end of each iteration, evaluate the increment against its acceptance criteria.

Code generation alone does not constitute completion.

### Machine Learning Testing

Distinguish between:

1. Training and evaluation testing performed on Kaggle.
2. Model artifact validation.
3. Application-side inference testing.
4. End-to-end testing using the trained models.

Test that:

- Required model artifacts can be located.
- Model artifacts can be loaded.
- Tokenizers and configurations are available.
- Input preprocessing is compatible with training.
- Inference executes successfully.
- Output post-processing works.
- Outputs conform to expected interfaces.
- Inference failures are handled appropriately.
- Model performance satisfies requirements.

Where actual trained artifacts have not been provided, use mocks or controlled fixtures and clearly identify the integration as unverified.

Do not claim actual model integration has succeeded when only mocked inference has been tested.

### Primary Deliverable

A **Tested and Validated Software Increment**, supported by:

- Test plans.
- Test cases.
- Automated test suites.
- Test execution results.
- Defect reports.
- Regression results.
- Acceptance assessments.
- Model evaluation reports.
- Model inference test results.

Detailed test procedures, the four ML test categories and per-increment deliverables are in the `testing-and-qa` skill.

---

## Phase 6: Deployment (Release)

See `docs/process/release-deployment.md`.
