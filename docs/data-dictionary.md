# Data dictionary

All tables live in `data/processed/` and join on `entry_id` — the Laserfiche document id
of the signed minutes (one document = one meeting). Text fields are as printed in the
minutes unless noted. Times are strings as printed (e.g. `6:03 p.m.`).

## meetings.csv — one row per meeting

| Column | Type | Description |
|---|---|---|
| entry_id | int | Laserfiche document id; resolves via `source_url` |
| meeting_date | YYYY-MM-DD | From the minutes heading; falls back to the document name |
| date_source | enum | `extracted` (heading) or `document_name` |
| date_disagrees_with_name | bool | Heading date ≠ date in the document name — check by hand |
| meeting_type | enum | regular, special, study_session, retreat, joint, continued, adjourned, executive_session, other |
| meeting_title | str | Heading as printed |
| document_name | str | Laserfiche document name |
| location | str | Where held, as printed |
| called_to_order_time, adjourned_time | str | As printed |
| presiding_officer | str | Who called the meeting to order |
| n_members_present, n_members_absent | int | From roll call |
| n_agenda_items, n_motions | int | Rows in the child tables |
| page_count | float | Pages in the signed minutes |
| source_url | str | Laserfiche viewer URL |
| extraction_mode, schema_version | str | Which Datalab mode and schema produced the row |

## attendance.csv — one row per member × meeting

| Column | Type | Description |
|---|---|---|
| member | str | Canonical last name (titles removed; typos snapped to the meeting's roll call; see `data/lookups/member_aliases.csv`) |
| name_as_printed | str | Exactly as in the minutes |
| title | str | Mayor / Mayor Pro Tem / Council Member, as printed |
| status | enum | `present` or `absent` at roll call |
| note | str | e.g. "arrived at 6:45 p.m.", "excused", "participated remotely" |

Caveat: roll call is taken at the start. Members who arrive late or leave early are
noted in `note` when the minutes say so; motion-level presence is in `member_votes`.

## agenda_items.csv — one row per agenda item × meeting

| Column | Type | Description |
|---|---|---|
| item_seq | int | Order within the minutes |
| item_number | str | As printed (`3`, `5.A`, `B`) |
| item_key | str | `item_number` with punctuation removed, upper-cased; joins to `motions.item_key` |
| section | str | Heading the item falls under (`CONSENT AGENDA`, `PUBLIC HEARINGS`, …) |
| title | str | Item title as printed |
| ordinance_or_resolution_numbers | str | `; `-separated |
| is_public_hearing | bool | |
| hearing_opened_time, hearing_closed_time | str | As printed |
| n_hearing_speakers | int | Rows in `speakers` for this item |
| outcome_summary | str | One-sentence summary written by the extractor (not verbatim) |

Caveat: section names are not harmonized across eras (the agenda template changed
several times). Filter on `section` with a case-insensitive substring, e.g. `consent`.

## speakers.csv — one row per public speaker

| Column | Type | Description |
|---|---|---|
| context | enum | `open_comment` or `public_hearing` |
| item_number | str | For hearings, the agenda item |
| speaker_seq | int | Order within the context |
| name | str | As printed in the signed minutes (public record) |
| topic | str | Open comment: short summary written by the extractor |
| position | str | Hearings: for / against / neutral / unstated — only when the minutes say |

Responsible-data note: speakers are mostly private residents. Their names appear in the
city's published minutes and are kept as printed; downstream publishers who don't need
them can drop this table without affecting any other.

## motions.csv — one row per motion × meeting

| Column | Type | Description |
|---|---|---|
| motion_seq | int | Order within the minutes |
| agenda_item_number, item_key | str | Item the motion belongs to |
| motion_text | str | As written |
| action_type | enum | consent_agenda, approve_agenda, approve_minutes, ordinance, resolution, amendment, appointment, call_up, continue_or_postpone, executive_session, adjourn, direction_to_staff, other |
| ordinance_or_resolution_numbers | str | `; `-separated |
| moved_by, seconded_by | str | Canonical last name |
| vote_text | str | The vote sentence, verbatim |
| result | enum | passed, failed, withdrawn, tabled, no_vote_recorded |
| yes_count, no_count | int? | Only if the minutes state a count |
| stated_unanimous | bool | The minutes say unanimous / all present / N:0 |
| vote_inference | enum | How `member_votes` rows were obtained — see below |
| item_level_exceptions | str | e.g. `Nagle: no; Speer: abstain` — votes the minutes name on individual items of this motion (usually the consent agenda) |
| n_yes, n_no, n_abstain, n_absent | int | Counts of `member_votes` rows |

`vote_inference`:

- `complete_as_stated` — every present member's vote is named in the minutes
- `inferred_from_roll_call` — unnamed present members filled in as `yes` from roll call
  (counts, where stated, reconcile)
- `inferred_with_item_exceptions` — the tally covers every present member with no nays,
  but the minutes name a nay, recusal, or abstention: those are on individual items
  ("Carried 9:0; NAY: Nagle on Item F"). The motion row gets all-yes, inferred; the
  item-level votes are in `item_level_exceptions`
- `partial_stated_only` — the minutes list yes votes but omit some present members
  (likely left the dais); only stated votes kept
- `inconsistent_not_inferred` — filling in would contradict a stated count; only stated votes kept
- `no_vote_recorded` — e.g. "by motion regularly adopted, the meeting adjourned"

## member_votes.csv — one row per member × motion

| Column | Type | Description |
|---|---|---|
| motion_seq | int | Joins to `motions` with `entry_id` |
| member | str | Canonical last name |
| vote | enum | yes, no, abstain, absent |
| vote_source | enum | `stated` (named in the vote sentence) or `inferred` (from roll call) |

## meetings.json — nested, one object per meeting

The original `README.md` per-meeting format (`date`, `minutes_url`, `attendees`,
`open_comment`, `consent_agenda`, `callup_checkin`, `public_hearings`) extended with
`entry_id`, `meeting_type`, `absent`, and the full `motions` list with `yeas`/`nays`/`absent`.
In `consent_agenda` and `public_hearings`, `absent` includes abstentions, as in the
original format.

## provenance.csv — one row per meeting

PDF path, fetch method (`electronic_file` or `generate_pdf10`), SHA-256, fetch time,
Datalab request ids for convert and extract, modes, parse quality score, schema version.
