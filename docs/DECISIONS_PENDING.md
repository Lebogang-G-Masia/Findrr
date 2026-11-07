# Findrr: Decisions Pending

> Read at the start of every session, together with `docs/STATUS.md`.
> Record every material ambiguity here, stop the affected work, and ask the user.
> Never present an assumption as an approved requirement.
> Keep the open-item count below equal to the number of entries under "Open decisions", and mirror it in `docs/STATUS.md`.

**Open items: 0**

## Open decisions

(none)

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
