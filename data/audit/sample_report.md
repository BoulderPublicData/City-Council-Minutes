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

Both modes sometimes put people who aren't on council on the roll call. `tidy` now
drops any roll-call name that nothing corroborates (no council title, no action in the
meeting, not on a roll call within 3 years) and lists it in
`data/processed/excluded_roll_call.csv`. In balanced mode that is 9 names in 4 meetings:
public speakers marked "did not show" or "withdrew" (2021-08-03, 2022-04-05,
2022-12-01) and the absentees of a Planning Board vote quoted in a call-up (2008-07-08).
This removed 81 spurious `absent` votes and changed no motion's inference. In fast mode
it drops the 7 Planning Board names at the 2016 joint meeting.

## Votes

- 88% of member-vote rows are `inferred`: the minutes state a tally plus dissenters,
  and the other present members are filled in from the roll call. The remaining 12% are named outright.
- 104 of 736 motions (14%) are split votes.
- 8% of motions (59) are `inconsistent_not_inferred`. The stated tally doesn't match the
  roll call, and nothing in the minutes says why. Only stated votes are kept.
- 3 motions are `inferred_from_attendance_note`: the tally was short by exactly the
  members noted as arriving late, so the rest were filled in (see limitation 1).
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

1. **Late arrivals — done, and smaller than expected.** Vote inference now reads
   `attendance.note` ("arrived at 6:45 p.m.", "left the meeting at 8:20 p.m.", a
   "Yates - Late" roll-call marker). It infers only when the notes account for exactly
   the gap between the tally and the roll call, and not when the noted member is seen
   moving, seconding, or voting by name around that motion. Rows are marked
   `inference_basis = attendance_note`. In balanced mode this recovered **3 of the 62**
   declined motions (2022-04-05 ×2, 2022-10-06; 24 member-vote rows), all checked against
   the minutes, and it fixed the 2022-04-05 consent vote against the reference. Fast mode
   gains 7 (also 2021-06-15 ×2, 2021-12-14, 2026-01-08), all correct. The 59 still declined are
   mostly **not** late arrivals the minutes record:
   - 21 are in two meetings whose roll call is wrong (2001-11-13 lists ten members at a
     transition meeting; 2005-03-15 found only six).
   - 18 have a tally one or two off the roll call with no note at all, e.g. a member
     absent at roll call who later moves a 9:0 motion (2011-09-20).
   - 11 are garbled or partial tallies (24-0, 6-6, 9/4; 4:0 with nine present where
     several members recused).
   - 5 give a nay count the named dissenters don't match (unnamed, or named only on
     individual consent items).
   - 4 (2003-08-05) have a note that contradicts the tally: Morzel "arrived at 7:10 p.m."
     but moved a 7:04 motion, and the consent vote was 5:0 with six present before she came.
   Recovering more would mean guessing who was out of the room; the remaining gaps are
   better handled by re-reading the roll call (first group) or not at all.
2. **Hearing ↔ motion linkage** in `meetings.json` is a heuristic (ordinance number,
   then agenda item). The tidy `motions` table is exact; the nested hearing view is approximate.
3. **Meeting type** has 17 `other` and 24 `special` in 98. This should be checked against the
   document names before relying on it.
4. **Open comment** recall (68%) hasn't been adjudicated. Some names are likely hearing
   speakers that the reference files under open comment, or the other way round.

## Recommendation

Run the full archive in **balanced** mode (≈ $150 more, raise the Datalab limit
accordingly). Limitation 1 is fixed. Limitations 2–4 can follow as table-level fixes
that don't need re-extraction.
