# Quarterly sample: findings and full-run recommendation

*Written 2026-10-26. Generated reports this summarizes: `accuracy.md`, `summary.md`,
`mode_agreement.csv`, `accuracy_balanced.csv`, `accuracy_fast.csv`.*

## What ran

| Stage | Result |
|---|---|
| Discovery | 771 documents in 27 year folders (2000–2026), ~5,450 pages; everything before 2013 is scanned page images |
| Sample | one meeting per (year, quarter): 106 meetings, 811 pages (`data/lookups/sample_quarterly.csv`) |
| Reference set | the 41 hand-transcribed 2021–22 meetings, fetched in addition, so accuracy can be scored |
| Fetch | 140 PDFs, 0 errors. The portal's bulk ZIP export fetches 25 records in ~7 requests |
| OCR (Datalab convert) | 140 / 140 |
| Balanced extraction | 98: the 41 reference meetings + 57 more sample meetings. 42 sample meetings are not yet extracted in balanced mode (the agreed budget cut) |
| Fast extraction | 140 / 140 |
| Tables (`data/processed/`, balanced) | 98 meetings · 882 attendance rows · 2,538 agenda items · 3,182 speakers · 736 motions · 5,063 member votes |

## Accuracy against the hand-transcribed meetings (41, balanced)

| Field | Raw agreement | After checking disagreements against the minutes |
|---|---|---|
| Meeting date | 90% | **100%**: all 4 mismatches are reference errors (e.g. the 2022-09-14 record is really 2021-09-14) |
| Attendance (exact set) | 85% (recall 100%) | **100%**: the reference omits the presiding mayor (4), members attending virtually (2), and once reads "Yates - Late" as a name |
| Consent-agenda nays | 90% | — |
| Consent-agenda yeas | 66% | Mostly the same missing-mayor slip, plus votes the pipeline declines to infer (below) |
| Public-hearing nays | 96% | — |
| Public-hearing yeas / mover | 57% / 50% | The reference names hearings by ordinance number and lists one vote per hearing; the minutes often have several motions per hearing. The linkage is approximate |
| Open-comment speaker recall | 68% | Not adjudicated |

Every disagreement checked so far was an error in the hand transcription, not in the
extraction (`data/lookups/adjudications.csv`). The raw yeas and mover numbers mostly
measure how differently the two sources model hearings, so they understate accuracy.

## Balanced vs. fast extraction

On the 41 reference meetings the two modes score about the same. Across all 98
meetings both modes extracted, balanced finds 10% more motions (736 vs 668) and 25%
more in 2005–09. To see which mode is right, motion counts were compared with the
number of vote sentences in the OCR text:

| Meeting | Balanced | Fast | Vote sentences in text |
|---|---|---|---|
| 2008-07-08 | 27 | 13 | ~30 |
| 2004-11-30 | 19 | 12 | ~13 |
| 2005-03-15 | 12 | 7 | ~13 |
| 2000-06-20 | 6 | 18 | ~7 |
| 2013-12-03 | 4 | 13 | ~2 |

Balanced tracks the text. Fast both misses motions in long narrative minutes and
invents them in others (likely splitting consent sub-items). Fast also counted six
Planning Board members as council members at a 2016 joint meeting.

## Votes

- 88% of member-vote rows are `inferred`: the minutes state a tally plus dissenters,
  and the other present members are filled in from the roll call. The remaining 12% are named outright.
- 104 of 736 motions (14%) are split votes.
- 8% of motions are `inconsistent_not_inferred`. The stated tally doesn't match the roll
  call, usually because someone arrived late or left early. Only stated votes are kept.
- 2% are `inferred_with_item_exceptions`: a recusal or nay on one consent item, beside a
  tally for the whole agenda ("Carried 9:0; NAY: Nagle on Item F").

## Cost

| | Spent so far | Rest of archive (631 docs, ~4,430 pages) |
|---|---|---|
| OCR (convert) | $3.01 | ≈ $13 |
| Balanced extraction | $22.46 | ≈ $135 |
| Fast extraction | $4.95 | ≈ $21 |

Total spent, including tests: ~$31. **Finishing the archive in balanced mode: ≈ $150 more.**
Fast-only would be ≈ $35 but is not recommended, given the motion counts above.

Time: about 2 hours to fetch (the portal's rate limit) and 5–6 hours of Datalab on the
free-tier rate limits (5 concurrent jobs). Git LFS storage for all PDFs: ~1.8 GB.

## Known limitations to decide on before the full run

1. **Late arrivals.** When the tally is lower than the roll call (8:0 with 9 present),
   votes stay uninferred. Using `attendance.note` ("arrived 6:45") could recover many.
2. **Hearing ↔ motion linkage** in `meetings.json` is a heuristic (ordinance number,
   then agenda item). The tidy `motions` table is exact; the nested hearing view is approximate.
3. **Meeting type** has 17 `other` and 24 `special` in 98. This should be checked against the
   document names before relying on it.
4. **Open comment** recall (68%) hasn't been adjudicated. Some names are likely hearing
   speakers that the reference files under open comment, or the other way round.

## Recommendation

Run the full archive in **balanced** mode (≈ $150 more, raise the Datalab limit
accordingly), after fixing limitation 1. Limitations 2–4 can follow as table-level fixes
that don't need re-extraction.
