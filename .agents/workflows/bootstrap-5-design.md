---
name: bootstrap-5-design
description: Use after bootstrap-4 is approved to design the initial architecture and obtain final approval to begin implementation.
---

# Initial System Design & Approval Governance

Establish the comprehensive application architecture and technical design, and enforce the mandatory review and approval gates before any substantial implementation work begins.

## When to Use

* Following requirements analysis and machine learning planning (`/bootstrap-1-environment` to `/bootstrap-4-ml-plan`).
* When designing the initial application architecture, module boundaries, data flows, and database schemas.
* When defining integration layers for AI/ML, web automation (Selenium headful), and document processing.
* When compiling the complete review package and securing explicit user approvals before starting development.

---

## 1. Initial System Design Scope

Once requirements are sufficiently analyzed, design and document the application architecture covering:

* **Application Structure & Boundaries:** Overall system layout and strict module boundaries.
* **Data Flow & Database Design:** Inter-module data movement, database entity relationships, and schemas.
* **Core Integrations & Capabilities:**
  * **AI/ML Integration:** Architecture linking server components to ML models.
  * **Web-Automation Architecture:** Selenium headful browser automation setup.
  * **Document-Processing Approach:** CV and cover letter generation pipelines.
* **Supporting Infrastructure:** Shared supporting services, configuration approach, and artifact storage/deployment.
* **Machine Learning Architecture:**
  * **Model-Training Architecture:** Kaggle notebook training pipelines.
  * **Model-Inference Architecture:** Module 9 server-side inference, artifact registry, and SHA-256 integrity checks.
* **Testing Strategy:** Multi-layered testing plan across unit, integration, regression, and E2E verification.
* **Decision Documentation:** Record all significant technical decisions and architectural trade-offs.

---

## 2. Mandatory Approval Gate & Review Package

Present the following comprehensive review package for explicit user review:

1. **Initial Project Plan** (Scope, roadmap, resources, risks, feasibility)
2. **Initial Software Requirements Specification (SRS)** (Authoritative requirements, use cases, ML reqs)
3. **Prioritized Product Backlog** (Prioritized features, user stories, dependencies)
4. **Machine Learning Development Plan** (13-point model specifications and compute/dataset plans)
5. **Proposed Software Architecture** (System design, module boundaries, and technical decisions)

### Core Governance Rules
* **Explicit Decisions:** Clearly identify all technical and scope decisions requiring user approval.
* **Implementation Gate:** **Do not begin substantial implementation work until the relevant project scope, requirements, and architectural decisions have been sufficiently established and explicitly approved.**

---

## 3. Approval Gate and Final Approval to Begin Implementation

When the architecture and design documents are drafted and the review package above is complete, update `docs/STATUS.md`:
- Set gate "5. Initial Architecture and Design" to **Presented for review**.
- List every technical and scope decision awaiting user approval, and record each in `docs/DECISIONS_PENDING.md`. Update the open-item count.
- Set "Next step" to: user reviews the full package and gives (or withholds) final approval.

Then **stop and wait for the user.** Do not begin implementation, create feature branches, or run `/start-iteration`.

Only after the user explicitly approves, update `docs/STATUS.md`:
- Set gate 5 to **Approved**, and set "Approved by user" to **Yes** for each gate the user approved.
- Set "Final approval to begin implementation" to **Approved**, with "Approved by user" **Yes**.
- Set "Current phase" to ready for Iteration 1, and "Next step" to `/start-iteration`.

If the user approves only some items, record exactly which were approved. Leave the others as **Changes requested** or **Presented for review**, and leave the final approval row as **Not started**. Never mark an approval the user has not given.
