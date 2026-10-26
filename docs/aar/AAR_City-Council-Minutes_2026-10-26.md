# After-Action Report: City-Council-Minutes, 2026-10-25 → 2026-10-26

## 1. Summary

One Claude Code session built a data-liberation pipeline for Boulder's signed council
minutes (Laserfiche → Datalab OCR/extraction → tidy tables) and ran it on a quarterly
sample. That work merged as BoulderPublicData/City-Council-Minutes#1. The result is
sound: dates and attendance match the minutes in every meeting checked, and every
disagreement with the hand-typed reference turned out to be a reference error. Two harness gaps cost the most time
and money:

1. **The download route.** The fetcher used the portal's slowest download route for about
   80 minutes until you pointed out a faster one. The bulk ZIP export cut requests per
   record by about 10×.
2. **The order of paid work.** Paid jobs ran in an order that spent the Datalab budget
   before any reference meeting had been extracted, so accuracy couldn't be scored until
   the limit was raised.

A third gap, a stop-hook loop, produced 9 snapshot commits and about 20 needless wakeups.

The highest-leverage fixes:

- **(a)** The data-liberation skill's survey step should list every export or batch
  feature of a web interface before anyone writes a per-record fetcher.
- **(b)** Paid batch work should start with a check of the spend limit and run the
  items that inform the decision first.
- **(c)** The pipeline should be able to write long-run output outside the git working tree.

## 2. Scope reviewed

- **Window:** 2026-10-25 22:06 UTC → 2026-10-26 01:35 UTC. Refs `1658b04..ee8de19`.
- **Evidence:**
  - Git: 17 commits (+629k / −1.5k lines, mostly data), 15 files touched 3 or more
    times, 0 reverts, and 1 fix-up commit (`e2e40dc`).
  - Session: 1 Claude Code transcript, with 1 correction from you, 0 interrupts, 0 rejected
    tool uses, and 7 tool errors (no repeated pattern).
  - Not available: PR, CI, and review-comment data, because `gh` isn't authenticated. CI
    status comes from the GitHub tool calls instead: green on every push. There were no review comments.
- **Earlier AAR:** none (this is the first).
- **Rigor level:** `standard`. This is a public civic dataset with a single maintainer and
  paid API spend, but no protected data.
- **Intent baseline:**
  - The `data-liberation` skill (`SKILL.md`, `references/toolchain-scraping.md`,
    `references/data-modeling.md`, `references/discovery-and-audit.md`).
  - The `ask-me-anything` skill (AMA pre-flight).
  - The user's brief and AMA answers.
  - The harness's session rules (stop hook, PR rules).
  - The project's `AGENTS.md`, which was written during the session. It is a result of
    this session, not part of the baseline.

## 3. What the agent was supposed to do (Q1)

From your brief:

- Retrieve every signed set of minutes from 2000 to now from Laserfiche.
- Send them to Datalab for OCR and extraction.
- Build a harmonized dataset of meetings, attendance, agenda items, and votes.
- **Sample one meeting per quarter per year before building the full pipeline.**
- Use the textbook's PEM if needed.

From the AMA answers:

- Tidy tables plus nested JSON.
- Per-member votes for every motion, with inferred votes flagged.
- Include every meeting type.
- Use Datalab for both OCR and extraction.
- Store PDFs in Git LFS.
- Keep speaker names as printed.
- **Stop and report after the sample.**
- **Estimate the cost first, then ask before the full run.**

The data-liberation skill sets the method:

- Survey → scaffold → extract → tidy → audit.
- "Don't scrape what you can download" and "Bulk downloads first" (`toolchain-scraping.md`
  lines 16 and 191–193).
- "Find the JSON endpoint the page itself is calling" (line 140).
- Pandera as "the gate" (`data-modeling.md` lines 183–186).

## 4. What actually happened (Q2)

| Phase | Time | What happened |
|---|---|---|
| Survey + AMA | 22:06–22:16 | Three rounds of AMA questions. The survey found the TLS chain problem (and fixed it with the textbook bundle), the `GetFolderListing2` JSON endpoint, imaged vs. electronic records, and the 41-meeting hand-typed `minutes.json`. |
| Pilot | 22:16–22:24 | One 2003 scan ran end to end. It measured convert at $3 per 1K pages and balanced vs. fast extraction at 20¢ vs. 2.7¢ for 6 pages. Fast found 3 of 6 motions, so the run was set up to compare both modes on the sample. |
| Scaffold | 22:24–22:30 | 15 modules, 16 tests, docs. CI green. |
| Discovery crawl | 22:16–23:35 | 166 requests over about 80 minutes, paced by the portal's rate limit. |
| Fetch v1 | 23:36–00:13 | The per-document `GeneratePDF10` route at about 3 requests per scanned record, projected at about 2 hours. 22 of 99 documents done. |
| **Your correction** | 00:06 | "There should be a consistent download PDF link on each page instead of waiting for images to concat." |
| Probe + switch | 00:06–00:21 | Reading the browse-page JavaScript found `ZipEntriesHandler` StartExport. A probe that ran while the fetcher was active triggered a rate-limit block, which cost about 10 minutes. |
| Fetch v2 | 00:21–00:30 | The remaining 109 documents in 29 requests and 9 minutes. |
| Datalab | 23:40–00:58 | OCR on all 140 PDFs, and balanced extraction on 57 sample meetings. Then the key's 30-day billing limit was hit (HTTP 402). **0 of the 41 reference meetings had been extracted.** |
| Budget pause | 00:58–01:03 | You chose "raise about $13 and score first", then raised the limit. |
| Scoring + fixes | 01:03–01:35 | Scoring found 6 pipeline and scorer defects. All were fixed (`e2e40dc`), and checking against the minutes showed every remaining disagreement was a reference error. Report written, then merged. |

Throughout the session:

- **Stop hook:** fired 8 times while background jobs were writing into the working tree.
  Each firing produced a commit and push, then CI, then a notification wakeup.
  Moving the jobs to a scratch copy at 23:43 ended the loop.
- **Monitors:** restarted 3 times because their filters were too broad. `fetch:` matched
  the `scripts.fetch:` logger prefix on every log line.
- **Schema bound:** the pandera upper bound on `n_members_present` was edited three times
  (9 → 12 → 30) as real meetings went past it: a post-election transition meeting, and a
  joint meeting misread in fast mode.

## 5. Gap analysis (Q3)

### 5.1 The per-record download route was built before the interface's export features were listed
- **Observation:** the fetcher was built on the per-document viewer flow from the textbook
  chapter. The browse page's "Download selected" ZIP export cuts requests per record by
  about 10×: 25 records in about 7 requests, against about 75 before. It was found only
  after you corrected course (the session's single correction). It had cost about 80 minutes
  of fetch time and about 37 minutes of the first fetch, and it would have cost about 2 hours
  for the sample and roughly 10 for the full archive.
- **Root cause: ambiguous.** The skill already says "Bulk downloads first," but it defines
  bulk as *files the publisher releases*: "annual bulk dumps", "the Secretary of State's
  annual election archive ZIP". Its endpoint advice ("watch the Network tab") points at the
  one request behind the page in front of you. Nothing says to list the interface's own
  batch features: multi-select download, export-as-ZIP, "download folder". The survey read
  only the doc-viewer bundle and never the browse bundle.
- **Why it mattered:** the portal's rate limit (~12 requests per 6 minutes) makes requests
  per record the throughput bottleneck. For any rate-limited portal this is the most
  important number in the survey.

### 5.2 The paid run started without a spend-limit check, and the decision set ran last
- **Observation:** the sample spend was estimated (about $35–40), but the account's 30-day
  limit was never checked. Jobs then ran in sample order with the 41 reference meetings
  last. When the limit hit at about $20, no reference meeting had been extracted. So the
  one output the stop-and-report gate needed, an accuracy score, couldn't be produced.
  The run stalled until you made a budget decision.
- **Root cause: missing.** Searched the data-liberation skill for budget, billing, cost,
  spend, and paid. It has no guidance on paid extraction APIs. Your AMA answer, "Estimate
  first, then ask", covered the full run, and nothing turned it into an ordering rule for the
  sample.
- **Why it mattered:** whenever a paid run has a decision gate, the items that inform the
  decision should be bought first. A billing limit then degrades the run gracefully instead of
  blocking the gate.

### 5.3 Long-running jobs wrote into a repo watched by a commit-on-stop hook
- **Observation:** 9 of 17 commits are "Add … so far" snapshots. Each pushed partial data,
  started 2 CI runs, and woke the session again. That was about 20 extra turns and noise in
  the history and the PR.
- **Root cause: genuinely novel, the first time.** It comes from the harness's stop hook
  meeting the skill's layout, where every stage writes into `data/` in the working tree.
  The next long run will hit the same thing, though, and the pipeline has no way to write
  somewhere else.
- **Why it mattered:** the workaround (a copy of the repo with `tar`, plus syncing back by
  hand) works but is easy to get wrong. A configuration option fixes it permanently.

### 5.4 Plausibility checks were written as hard contracts
- **Observation:** the members-present bound was edited 3 times. Each time it failed the
  whole build on data that was real but unusual: ten members at a post-election transition,
  and Planning Board members at a joint meeting in fast mode. Each failure blocked scoring
  until it was edited. The fix that worked was a loose contract bound plus an audit flag for
  more than 9.
- **Root cause: ambiguous.** `data-modeling.md` lists "value out of declared range" as part
  of "the gate". It doesn't separate *impossible* values, which belong in the contract, from
  *implausible* ones, which belong in the audit.

### 5.5 Smaller items, each happening once
- A probe shared the portal's rate limit with the running crawler and set off a block, at a
  cost of about 10 minutes. It is now noted in `AGENTS.md`, so it needs nothing more.
- The Monitor filter matched logger prefixes. This is a one-off with a harness tool, so no
  rule is needed.
- Datalab pacing started at 7 seconds between requests, chosen from the documentation, with
  zero 429s seen. It was tuned to 3 seconds plus backoff after measuring. Already fixed in
  `config.py`.

## 6. Recommended revisions (Q4)

### [P0-1] List an interface's batch and export features before writing a per-record fetcher
- **Target:** `data-liberation/references/toolchain-scraping.md` → extend "Bulk downloads
  first". Also `data-liberation/SKILL.md` → the Survey checklist.
- **Root cause:** ambiguous
- **Medium:** skill body. This is a survey step that needs judgment, so prose is the right medium.
- **Evidence:** §5.1. Your one correction; 37 minutes at about 3 requests per record against
  0.28 after the switch; the skill's "bulk" wording.
- **Change:** append to `toolchain-scraping.md` under "### Bulk downloads first":
  > **Bulk features of the interface itself count too.** Before writing a per-record
  > fetcher, list every way the *interface* moves many records at once: "download
  > selected", "export folder", ZIP/CSV export, print-to-PDF of a result set. Document
  > portals (Laserfiche WebLink, Granicus, Legistar, CivicPlus) almost always have one.
  > Find them by reading **every** JavaScript bundle the site loads — browse/search pages,
  > not just the record viewer — for endpoints named `export`, `zip`, `download`,
  > `batch`. On a rate-limited portal, requests per record is the throughput number that
  > matters; record it in the Survey note for each route you find.

  And add to the Survey checklist in `SKILL.md` §1:
  > - **What is the cheapest route per record?** For web interfaces, list the per-record
  >   and the batch/export routes and the requests each costs per record. Pick the
  >   cheapest before writing `fetch.py`.
- **Why it works:** the existing rule assumes bulk data is a separate release. This edit
  points the survey at the interface's own batch tools, and asks for a number (requests per
  record) that makes the slow route look slow before any code depends on it.
- **Owner:** maintainer review (skill edit)
- **Status:** Proposed

### [P0-2] Paid batch runs: check the spend limit first, and buy the decision set first
- **Target:** `data-liberation/SKILL.md` → §3 Extract, new paragraph. Plus this project's
  `AGENTS.md` → "How to…".
- **Root cause:** missing
- **Medium:** skill body (judgment about what "decision set" means). The clean stop on
  HTTP 402 is already code (`BillingLimitError`).
- **Evidence:** §5.2. 0 of 41 reference meetings extracted when the limit hit at about $20,
  and a stalled gate.
- **Change:** add to `SKILL.md` §3:
  > **Paid extraction APIs (Datalab, Textract, LLM extraction).** Before a batch: (1) run
  > one document end-to-end and record its cost per page; (2) check the account's spend
  > limit or credit balance and compare it with the projected batch cost; (3) order the
  > batch so the items that answer the current decision run first — usually the
  > validation set you will score against — then the rest; (4) make the client stop
  > cleanly on the provider's billing error (HTTP 402) instead of failing every remaining
  > item. A limit hit then costs you coverage, not the decision.

  And add to `AGENTS.md` under "How to…":
  > - **Run paid extraction in decision order:** `extract --scope gold` before
  >   `--scope sample`/`all`, so accuracy can always be scored even if the Datalab limit
  >   is reached mid-run.
- **Why it works:** a decision gate needs one specific output. Buying that output first
  turns a billing limit into a smaller sample instead of a blocked review.
- **Owner:** maintainer review (skill). `AGENTS.md` line: auto-applyable.
- **Status:** Proposed

### [P1-1] Let pipeline output go outside the working tree for long runs
- **Target:** `scripts/config.py` and `AGENTS.md` → Gotchas
- **Root cause:** novel → recurring (it will hit every full-archive run)
- **Medium:** tool config. The rule is mechanical.
- **Evidence:** §5.3. 9 snapshot commits and about 20 wakeups.
- **Change:** in `scripts/config.py`:
  ```diff
  -DATA = ROOT / "data"
  +# Long runs (hours) can write elsewhere so a commit-on-stop hook or editor doesn't
  +# churn on partial output; copy `data/` back and commit once when the run finishes.
  +DATA = Path(os.environ.get("CCM_DATA_DIR", ROOT / "data"))
  ```
  Add a gotcha to `AGENTS.md`:
  > 10. **Long runs.** Fetch and Datalab runs take hours. Run them with
  >     `CCM_DATA_DIR=/path/outside/repo/data` (copy `data/` there first), then copy the
  >     results back and commit once — partial output in the working tree triggers
  >     snapshot commits and CI on every turn.
- **Why it works:** it replaces this session's improvised `tar` copy with one supported
  setting, so the next agent doesn't have to rediscover the loop.
- **Owner:** auto-applyable
- **Status:** Proposed

### [P1-2] Separate impossible values (contract) from implausible ones (audit flag)
- **Target:** `data-liberation/references/data-modeling.md` → after the pandera paragraph
  (around line 186)
- **Root cause:** ambiguous
- **Medium:** skill body
- **Evidence:** §5.4. 3 edits to one bound, and each one blocked scoring.
- **Change:** add:
  > **Contract vs. plausibility.** Put only *impossible* values in the pandera contract
  > (negative counts, malformed dates, unknown enum values). Put *implausible-but-real*
  > values — ten council members at a transition meeting, a 40-page set of minutes — in
  > the audit as flags for hand review. A contract that rejects real data blocks the
  > pipeline on exactly the cases you most need to look at.
- **Why it works:** it gives a test for where a bound belongs, so the first bound written is
  the right one.
- **Owner:** maintainer review
- **Status:** Proposed

### [P2-1] Codify checking disagreements against the source
- **Target:** `data-liberation/references/discovery-and-audit.md` → Reconciliation section
- **Root cause:** none (a strength to codify, §7)
- **Medium:** skill body
- **Evidence:** every disagreement checked was a reference error (11 rows in
  `data/lookups/adjudications.csv`). The mode choice was settled by counting vote sentences
  in the source.
- **Change:** add:
  > **A hand-made reference is a claim, not truth.** When scoring against volunteer
  > transcriptions or an earlier dataset, read each disagreement in the original
  > document and record the verdict (reference error / extraction error / both) in a
  > `data/lookups/adjudications.csv`. Report raw and adjudicated agreement side by side.
- **Owner:** maintainer review
- **Status:** Proposed

## 7. Strengths to sustain

- **The AMA pre-flight held up.** Three rounds settled the shape of the tables, how inferred
  votes are labeled, storage, the review gate, and the budget rule. None of those was
  revisited later, which shows the questions targeted the forks that mattered.
- **Survey before code.** The TLS chain, the JSON listing endpoint, imaged vs. electronic
  records, and the existing reference file were all found before the scaffold. Each would
  have caused rework later. This is the skill's §1 working as written.
- **A one-document pilot before any batch.** It measured the cost split and showed that fast
  mode drops motions. That turned "which extraction mode?" into a measured comparison instead
  of a guess. Worth stating explicitly in the skill's Extract step; P0-2 does this.
- **Checking against the primary source.** Disagreements were read in the minutes, and fast
  mode's motion counts were checked against vote sentences in the text. This emergent habit
  turned "66% yeas agreement" into an accurate picture. Codified in P2-1.
- **Idempotent, resumable stages.** Six or more restarts (moving to the scratch copy, the ZIP
  switch, re-pacing, the 402 stop) each cost nothing. This is the skill's "immutable originals
  + manifest" convention paying off.
- **Gotchas recorded as they were found.** `AGENTS.md` captured the TLS chain, the
  rate limit, imaged records, the ZIP export, and checkpoints during the session.

## 8. Revision actions — tracking table

Applied in the follow-up PR (2026-10-26): P1-1, and P0-2's project part. The ordering
rule is enforced in code (`datalab._targets` sorts reference meetings first), which is a
stronger medium than the proposed `AGENTS.md` line. Project versions of P0-1 and P1-2
were added to `AGENTS.md` (gotchas 3 and 12). The data-liberation skill edits are outside
this repo and remain proposed.


| ID | Pri | Target | Medium | Change | Owner | Status | Check next time |
|---|---|---|---|---|---|---|---|
| P0-1 | P0 | data-liberation `toolchain-scraping.md`, `SKILL.md` | skill body | List batch/export routes and requests per record before writing a fetcher | maintainer | Proposed | Your corrections about the access route: 1 → 0. Requests per record in the first fetcher: 3 → ≤ 0.5 |
| P0-2 | P0 | data-liberation `SKILL.md` §3; `AGENTS.md` | skill body + definition | Check the spend limit; extract the decision set first; stop cleanly on 402 | maintainer / auto | Project part applied (gold-first ordering in `datalab._targets`, AGENTS gotcha 11); skill part proposed | Reference items extracted when a limit is hit: 0/41 → 41/41. Gate stalls on budget: 1 → 0 |
| P1-1 | P1 | `scripts/config.py`; `AGENTS.md` | tool config | `CCM_DATA_DIR` output override for long runs | auto | Applied (project) | Snapshot "…so far" commits per run: 9 → 0 |
| P1-2 | P1 | data-liberation `data-modeling.md` | skill body | Impossible values in the contract, implausible ones as audit flags | maintainer | Proposed | Edits to one schema bound in a run: 3 → ≤ 1 |
| P2-1 | P2 | data-liberation `discovery-and-audit.md` | skill body | Check reference disagreements against the source and record verdicts | maintainer | Proposed | Accuracy reports with an adjudicated column: 1 of 1 → keep 1 of 1 |
