# City Council Minutes

Every signed set of Boulder City Council minutes, 2000–present, liberated from the
city's [Laserfiche records portal](https://documents.bouldercolorado.gov/WebLink/Browse.aspx?id=10888&dbid=0&repo=LF8PROD2)
into a harmonized dataset: one row per meeting, per member's attendance, per agenda
item, per public speaker, per motion, and per member's vote on each motion.

> **Status: quarterly sample.** The pipeline has been run on one meeting per quarter
> per year (see `data/lookups/sample_quarterly.csv`) and scored against the 41
> hand-transcribed 2021–22 meetings. The full archive run waits on review of
> `data/audit/accuracy.md` and the cost projection in `data/audit/summary.md`.

## Why

Council minutes are the official record of how Boulder's elected officials vote, yet
they are published as ~700 separate PDFs — scanned images before ~2008 — behind a
portal with no bulk download. Questions like "how often did the council split 5–4?"
or "who seconded the most land-use ordinances?" need the record as data. This project
continues the Boulder Public Data volunteer effort (the hand-typed `minutes.json`)
with a reproducible pipeline.

## The data

| File | One row per |
|---|---|
| `data/processed/meetings.csv` | meeting (date, type, times, presiding officer, counts) |
| `data/processed/attendance.csv` | member × meeting (present / absent at roll call) |
| `data/processed/agenda_items.csv` | agenda item × meeting |
| `data/processed/speakers.csv` | public speaker (open comment or public hearing) |
| `data/processed/motions.csv` | motion (mover, seconder, vote sentence, result, tally) |
| `data/processed/member_votes.csv` | member × motion, with `vote_source = stated \| inferred` |
| `data/processed/meetings.json` | meeting, nested — the original format below, extended |
| `data/processed/provenance.csv` | meeting: PDF hash, fetch method, Datalab request ids |

Column definitions: [`docs/data-dictionary.md`](docs/data-dictionary.md).
Pivot recipes (pandas, R, spreadsheets): [`docs/filter-pivot-recipes.md`](docs/filter-pivot-recipes.md).

**About inferred votes.** Older minutes often record only a tally and the dissenters
("The motion carried 6:3, Havlick, Morzel and Riggle opposed"). The pipeline fills in
the unnamed present members as `yes` from that meeting's roll call and marks each such
row `vote_source = inferred`. It declines to infer when the counts don't reconcile
(someone left early, say). Filter to `vote_source == "stated"` for only what the
minutes literally say.

## How it works

```
Laserfiche WebLink ─▶ discover ─▶ fetch (PDFs, Git LFS) ─▶ Datalab /convert (OCR → markdown)
   ─▶ Datalab /extract (JSON schema) ─▶ tidy (tables + vote inference) ─▶ score + audit
```

- **Retrieval.** The portal's own JSON endpoint (`GetFolderListing2`) lists folders.
  Electronic PDFs download directly; scanned minutes are rendered to PDF by the
  portal's viewer. The city's server omits an intermediate TLS certificate, so requests
  verify against `certs/boulder-ca-bundle.pem` from the CU Info Science
  [*Web Data Science Book*, ch. 9](https://github.com/cuinfoscience/Web-Data-Science-Book/blob/main/ch-09-pdfs.qmd)
  — never `verify=False`. The client paces itself to the portal's rate limit.
- **OCR and extraction.** [Datalab](https://www.datalab.to) converts each PDF to
  markdown (committed under `data/interim/datalab/markdown/`), then fills the schema
  in `scripts/extraction_schema.py`, with per-field citations.
- **Tidy and validate.** `scripts/tidy.py` normalizes member names, infers votes,
  and validates every table against pandera contracts in `scripts/schema.py`.

## Reproduce

```bash
uv sync
export DATALAB_API_KEY=...            # https://www.datalab.to/app/keys
uv run python -m scripts discover     # slow: the portal is rate limited (cached, resumable)
uv run python -m scripts sample       # one meeting per quarter per year
uv run python -m scripts fetch        # --scope all for the whole archive
uv run python -m scripts convert
uv run python -m scripts extract --mode balanced
uv run python -m scripts tidy --mode balanced
uv run python -m scripts score
uv run python -m scripts audit
uv run pytest
```

PDFs are stored with [Git LFS](https://git-lfs.com); run `git lfs pull` after cloning
to get them. See [`AGENTS.md`](AGENTS.md) for architecture and gotchas.

## Legacy hand-transcribed format

`minutes.json` holds 41 meetings (2021-05 → 2022-12) typed by volunteers in an
[HJSON](https://hjson.github.io/) editor ([source](https://json.link/D6f2H0KntI),
[JSON](https://json.link/wGiTx3N5w2.json)). It is kept unchanged as a reference set; a
repaired strict-JSON copy is in `data/lookups/gold/`. `data/processed/meetings.json`
uses the same shape:

* `date` — ISO-8601 meeting date
* `minutes_url` — the signed minutes
* `attendees` — last names of council members present
* `open_comment` — list of `{name, topic}`
* `consent_agenda` — `{items, yeas, nays, absent}`
* `callup_checkin` — items called up from boards and commissions
* `public_hearings` — list of `{name, description, opened, closed, speakers, motion, seconded, yeas, nays, absent}`

and adds `entry_id`, `meeting_type`, `absent`, and `motions` (every motion with its votes).

## License

Code: MIT (see `LICENSE`). The minutes are public records of the City of Boulder.
