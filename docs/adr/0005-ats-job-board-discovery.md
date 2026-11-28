# ADR 0005: Official ATS Job-Board Endpoints for Job Discovery

- **Status:** Accepted
- **Date:** 2026-11-28
- **Deciders:** Lebogang Masia, Claude Code
- **Supersedes:** ADR 0004, for the discovery source only. ADR 0004's headful-by-default rule still applies to any browser automation.
- **Decision record:** D-002 in `docs/DECISIONS_PENDING.md`

## Context and Problem Statement

ADR 0004 discovered postings by running Google Search through Selenium. Google's robots.txt disallows `/search` and its terms prohibit automated queries, so this conflicts with BR-004 (respect robots.txt and site terms). In practice it also failed: a live run on 2026-11-26 got a CAPTCHA on the first query. The driver hid automation (`--disable-blink-features=AutomationControlled`, a hard-coded user agent) and weakened security (`--no-sandbox`), and posting pages were fetched without a robots.txt check.

The owner requires completely free sources and a target market of South Africa. No free web-search API permits this use, and the South African job boards have no public APIs (research in D-002).

## Decision Drivers

- BR-004 and the AGENTS.md hard rules: respect site terms, never bypass CAPTCHAs or access restrictions, prefer official APIs.
- The owner's requirement for completely free sources.
- Reliability: results that are accurate and current, and requests that keep working.
- Works on the owner's laptop now (Milestones 1-3), with no fixed IP or keys.

## Considered Options

1. Keep Selenium on Google, with the evasion flags removed.
2. A web-search API (Google Programmable Search, Vertex AI Search, Tavily, Brave, Marginalia).
3. Careerjet's publisher API plus ATS adapters (D-002 option F1).
4. ATS job-board endpoints only, over a curated employer list (D-002 option F2).

## Decision Outcome

Chosen option: **4, ATS job-board endpoints only**. It is the most reliable option, it is free and keyless, and the endpoints are published for third parties to read.

- Providers: Greenhouse, Lever, Workable and Recruitee public job-board endpoints, each an adapter behind the NFR-010 search-provider interface. SmartRecruiters is excluded until its authentication is confirmed.
- The employer list is configuration, not code. Where it comes from is D-013.
- Discovery no longer uses a browser. Selenium stays headful by default wherever it is still used (for example, a posting page that needs one).
- In every case: remove the automation-hiding flags, the hard-coded user agent and `--no-sandbox`; check robots.txt before fetching any posting page; identify the client plainly.
- Search result limits stay as defined in `docs/spec/modules/04-find-postings.md` (FR-013, FR-017). Fewer than 2 results are recorded as found, never padded.

### Positive Consequences
- Postings come from the employer's own hiring system, so they are current, and a posting removed from the board is evidence that it has closed.
- No CAPTCHAs, keys, accounts or IP registration, so nothing can be suspended and discovery runs unattended.
- Structured JSON instead of parsed search pages.
- Employer-direct application links by construction (FR-014).

### Negative Consequences / Trade-offs
- Coverage is limited to listed employers that use these four systems. Discovery becomes "jobs at these employers", not the whole market.
- The employer list has to be built, verified and maintained.
- One adapter per ATS, and each ATS can change its endpoint.

## Pros and Cons of the Options

### Option 1: Selenium on Google
- Good, because it is already built.
- Bad, because it still breaks Google's terms and BR-004, and CAPTCHAs stop unattended runs.

### Option 2: Web-search API
- Good, because it covers the open web.
- Bad, because Google's JSON API is closed to new customers and ends on 2027-01-01, Vertex needs billing, Tavily and Brave are capped trials of paid services, and Marginalia's free key is non-commercial.

### Option 3: Careerjet plus ATS
- Good, because it is the only free source with market-wide South African coverage.
- Bad, because it needs a declared fixed IP (unavailable on the laptop), forbids building a job database and any ML training or evaluation on its data, and results are aggregated, so some are stale or duplicated. It may be raised again for Milestone 4 as a new decision.

### Option 4: ATS only
- Good, because it is the most reliable, compliant and free option, and works today.
- Bad, because coverage depends on the employer list.
