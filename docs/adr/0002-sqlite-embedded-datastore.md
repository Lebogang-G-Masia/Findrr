# ADR 0002: SQLite as Embedded Relational Datastore

- **Status:** Accepted
- **Date:** 2026-11-02
- **Deciders:** Lebogang Masia, Antigravity AI Pair

## Context and Problem Statement
Findrr requires persistent storage for user profiles, search preferences, scraped job postings, and application tracking records during Milestones 1–3. Storage must run locally on the user's laptop without requiring background server daemons (e.g., PostgreSQL or MySQL).

## Decision Drivers
- Zero configuration, embedded execution on local developer workstations.
- Strict personal data privacy (data stays on local disk).
- Relational integrity, foreign keys, and ACID transaction support.

## Considered Options
1. Flat JSON files on disk: Simple, but lacks atomic transactions, query indexing, and relational integrity.
2. Local PostgreSQL daemon: Heavyweight, requires external service setup, and increases local resource consumption.
3. Embedded SQLite 3 with WAL Mode: Standard Python library, zero external dependencies, robust transactional support, and single-file portability.

## Decision Outcome
Chosen option: **Embedded SQLite 3 with Write-Ahead Logging (WAL)**.
- `PRAGMA foreign_keys = ON;` enforced on all connections.
- Access restricted to the user's filesystem permissions (`0600`).
- Seamless migration to PostgreSQL in Milestone 4 if required by the server deployment.
