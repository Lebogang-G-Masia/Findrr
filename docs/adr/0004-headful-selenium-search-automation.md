# ADR 0004: Headful Selenium WebDriver for Ethical Search Discovery

- **Status:** Accepted
- **Date:** 2026-11-02
- **Deciders:** Lebogang Masia, Antigravity AI Pair

## Context and Problem Statement
Findrr must discover job postings across Google Search and public employer career pages. Headless browser automation and automated bot scrapers frequently trigger immediate CAPTCHAs, IP bans, or Cloudflare blocks, which violate project invariants (never bypass CAPTCHAs or security restrictions).

## Decision Drivers
- Adherence to project rule: "Selenium runs headful by default."
- Anti-bot mitigation via polite scraping (random delays and human-like interaction).
- Transparency: The user can observe automated navigation on their screen.

## Considered Options
1. Raw HTTP Requests / Scrapy: Immediately blocked by Google Search and modern dynamic JavaScript single-page application career sites.
2. Headless Puppeteer / Selenium: Easily fingerprinted and flagged by bot detection heuristics.
3. Headful Selenium WebDriver with Randomized Delay Jitter: Standard browser execution, visible to the user, with 2.0s–5.0s randomized delays between requests.

## Decision Outcome
Chosen option: **Headful Selenium WebDriver with Randomized Delay Jitter**.
- Executes in standard visible browser window by default.
- Implements randomized polite delays between actions.
- Prioritizes direct employer application destinations over third-party boards.
