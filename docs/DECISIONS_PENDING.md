# Findrr: Decisions Pending

> Read at the start of every session, together with `docs/STATUS.md`.
> Record every material ambiguity here, stop the affected work, and ask the user.
> Never present an assumption as an approved requirement.
> Keep the open-item count below equal to the number of entries under "Open decisions", and mirror it in `docs/STATUS.md`.

**Open items: 4**

## Open decisions

### D-002: Job-discovery source conflicts with robots.txt and site terms (BR-004)
- **Raised:** 2026-11-26, during the pre-Iteration-6 codebase audit
- **Area:** security / requirements / architecture
- **Ambiguity:** ADR-0004 and US-008 approve automated Google Search via Selenium. BR-004 and the AGENTS.md hard rules require respecting robots.txt and site terms. Google's robots.txt contains `Disallow: /search`, and Google's terms prohibit automated queries. Also:
  - the driver sets `--disable-blink-features=AutomationControlled` and a hard-coded Chrome 128 user agent, which hide automation from bot detection;
  - `--no-sandbox` weakens browser security;
  - posting pages are fetched without any robots.txt check.
- **Why it matters:** two approved sources conflict, so the agent must not resolve this silently. A live run on 2026-11-26 got a CAPTCHA on the first query from a fresh profile, so discovery cannot work unattended in practice. Hiding automation also comes close to the "never bypass access restrictions" rule.
- **Options:**
  1. **Official search API for discovery.** Google Programmable Search JSON API (free tier of 100 queries per day, needs an API key) or Bing or Brave Search APIs. Fetch only robots-permitted posting pages, with a plain browser identity. Trade-offs: needs an API key stored outside git and a new external integration (approval and dependency evaluation); most compliant and reliable.
  2. **Official job-board APIs** (for example Adzuna, Greenhouse or Lever public job-board APIs) as primary sources, with search as a fallback. Trade-offs: best data quality and terms compliance, but per-source adapters and coverage gaps outside supported boards and regions.
  3. **Keep Selenium on Google, made explicit.** Remove the evasion flags and `--no-sandbox`, add robots.txt checks for posting pages, and record your written acceptance of the Google terms risk. Trade-offs: least work, but still conflicts with BR-004 for the search step, and CAPTCHAs will stay frequent.
- **Recommendation:** Option 1 now (NFR-010 already provides an abstract search-provider interface), plus the clean-up from Option 3 (remove the evasion flags and `--no-sandbox`, check robots.txt for posting pages) in every case. Consider Option 2 adapters in Milestone 5.
- **Blocked work:** changes to the search driver, the discovery source and robots handling. Unattended live discovery is not possible until this is decided.
- **Status:** Open

### D-003: DOCX/PDF export (US-012) was marked done but is not implemented
- **Raised:** 2026-11-26, during the pre-Iteration-6 codebase audit
- **Area:** requirements / process
- **Ambiguity:** The backlog ticked "Integrate python-docx for DOCX generation", but no DOCX or PDF code exists and `python-docx` is not a dependency. `DocumentGenerator` writes Markdown only. The backlog entry has been corrected to unchecked. Implementing it needs a new dependency.
- **Why it matters:** US-012 is part of the Milestone 2 completion gate ("DOCX/PDF export verified"). Adding a library is a significant dependency that needs approval.
- **Options:**
  1. `python-docx` (MIT licence, about 1 MB, pure Python) for DOCX, and PDF via LibreOffice headless conversion if it is installed. Trade-offs: small dependency; PDF depends on a system tool.
  2. `python-docx` for DOCX plus `fpdf2` (LGPL, pure Python) for PDF. Trade-offs: two dependencies; PDF layout is basic but needs no system tools.
  3. DOCX only for now and defer PDF. Trade-offs: smallest scope; the milestone gate would need re-scoping.
- **Recommendation:** Option 2. Both libraries are pure Python and work offline, and the output stays fully deterministic and grounded.
- **Blocked work:** US-012 implementation.
- **Status:** Open

### D-004: ML-001 runtime uses PyTorch, but ADR-0003 approved ONNX Runtime only
- **Raised:** 2026-11-26, during the pre-Iteration-6 codebase audit
- **Area:** ML / architecture
- **Ambiguity:** `TitleExpanderRunner` loads Flan-T5 via `torch` + `transformers`. ADR-0003 rejected the PyTorch CPU engine and chose ONNX Runtime. `STATUS.md` lists "needs torch in .venv". `torch` is installed in `.venv` but declared nowhere. The `ml` extra added on 2026-11-26 declares only ADR-0003 packages (onnxruntime, transformers, numpy).
- **Why it matters:** this is a model compatibility and inference-architecture contract (approval gate), and `torch` is a large dependency (about 700 MB+ on CPU).
- **Options:**
  1. Export ML-001 to ONNX (seq2seq encoder/decoder, for example via `optimum`) in the Kaggle notebook, and run it with ONNX Runtime. Trade-offs: matches ADR-0003 and uses less memory; needs a notebook change, which you would run.
  2. Accept PyTorch for ML-001 only: amend ADR-0003 and declare `torch` in the `ml` extra. Trade-offs: no retraining needed; larger install and memory use.
- **Recommendation:** Option 2 short term, since it unblocks the artifacts that are already trained. Plan Option 1 for Milestone 5 optimisation.
- **Blocked work:** declaring `torch`; real ML-001 integration claims.
- **Status:** Open

### D-005: Company research (US-014): sources and how summaries are produced
- **Raised:** 2026-11-26, during Iteration 6 requirements analysis
- **Area:** requirements / architecture / ML / security
- **Ambiguity:** FR-022 and Module 5 §C require company research "with source attribution" from "reliable sources", but no source is approved. Open points:
  - which sources to use;
  - how to find the employer's website (web search is blocked by D-002);
  - whether summaries are generated by a model (no approved model) or extracted;
  - how to cover "recent developments" (needs a news source).
- **Why it matters:** this involves external integrations, scraping compliance and the no-fabrication rule for company information. A wrong choice risks invented company facts or breaches of site terms.
- **Options:**
  1. **Deterministic, extractive research, no new model.** Use three sources:
     - the stored posting text;
     - the employer's own site, only when a posting URL is employer-direct (homepage and about page, fetched once with a robots.txt check);
     - Wikipedia's official REST summary API (CC BY-SA, with attribution).

     Each fact is stored with its source URL and retrieval date. Missing fields are marked "Not found". Skip "recent developments" until a news source is approved. Trade-offs: no fabrication risk; summaries are excerpts, not prose; adds Wikipedia as an external integration.
  2. Option 1 plus a news API (for example GNews or NewsAPI) for recent developments. Trade-offs: an API key and terms; a free tier is limited.
  3. Generative summaries with a new fine-tuned model (Kaggle). Trade-offs: needs a model spec, dataset and evaluation approval; fabrication risk must be controlled.
- **Recommendation:** Option 1 now, Option 2 later if wanted. Option 3 is not recommended: extraction meets FR-022 without fabrication risk.
- **Blocked work:** US-014 implementation.
- **Status:** Open

## Entry template

Copy this block for each new decision. Number entries `D-001`, `D-002`, and so on, and never reuse a number.

```markdown
### D-NNN: Short title
- **Raised:** YYYY-MM-DD, during <workflow, iteration or document>
- **Area:** requirements | architecture | security | UX | ML | process
- **Ambiguity:** What is unclear or undecided.
- **Why it matters:** What depends on it, and what a wrong guess would cost.
- **Options:**
  1. Option A. Trade-offs.
  2. Option B. Trade-offs.
- **Recommendation:** Which option, and why.
- **Blocked work:** What has been paused until this is decided.
- **Status:** Open
```

## Resolved decisions

Move an entry here when the user decides. Change its status to Resolved, and add the decision, the date, and the document updated to reflect it.

### D-001: Handling CAPTCHA Interception and Browser Session Persistence in Job Discovery
- **Decision:** Option A: Human-in-the-loop manual completion prompt in headful CLI + persistent Chrome profile directory (`chrome_profile/`).
- **Decided:** 2026-11-07
- **Recorded in:** `src/findrr/search/driver.py`, `src/findrr/search/engine.py`, `docs/spec/modules/04-find-postings.md`
- **Summary:** When Google redirects to `google.com/sorry/index` or displays a bot challenge, Findrr halts execution, alerts the user in the CLI, and keeps the headful Chrome window open for the user to solve the challenge manually. Using a persistent `chrome_profile/` ensures solved tokens and session cookies are remembered across searches.
