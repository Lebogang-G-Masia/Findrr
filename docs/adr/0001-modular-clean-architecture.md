# ADR 0001: Modular Clean Architecture for Findrr Core

- **Status:** Accepted
- **Date:** 2026-11-02
- **Deciders:** Lebogang Masia, Antigravity AI Pair

## Context and Problem Statement
Findrr must evolve across 5 major milestones, starting as a local CLI tool (Milestones 1–2), transitioning to desktop web and mobile interfaces with mock backends (Milestone 3), and finally integrating with a dedicated server (Milestone 4). The architecture must avoid tight coupling between user interfaces, web-scraping logic, local ML runtimes, and persistence layers.

## Decision Drivers
- Need for UI decoupling (CLI -> Web/Mobile UI -> Remote Server).
- Need to strictly isolate ML inference (Module 9) from domain logic.
- Maintainability, high testability, and strict adherence to project invariants.

## Considered Options
1. Monolithic Script-Based CLI: Rapid prototyping, but difficult to refactor for Web/Mobile UI and server integration.
2. Microservices Architecture: Premature complexity, network latency, and unnecessary overhead for a local solo developer application.
3. Modular Clean Architecture (Ports & Adapters): Strict separation of Domain, Application Services, and Infrastructure Adapters.

## Decision Outcome
Chosen option: **Modular Clean Architecture (Ports & Adapters)**.
- Domain models and business rules have zero external dependencies.
- Application services implement explicit use-case boundaries.
- Presentation layers (CLI, future REST APIs) consume services uniformly.

### Consequences
- **Positive:** Enables seamless transition from CLI to Web APIs in Milestone 4 without modifying business logic.
- **Negative:** Requires slightly more boilerplate interfaces and data transfer objects (DTOs).
