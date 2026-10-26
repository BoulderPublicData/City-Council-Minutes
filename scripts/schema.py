"""Canonical tables and their pandera contracts.

Six linked tables, all keyed on `entry_id` (the Laserfiche document id, which is
stable and resolvable: `DocView.aspx?id=<entry_id>`):

    meetings      one row per signed-minutes document
    attendance    one row per member × meeting (present / absent at roll call)
    agenda_items  one row per agenda item × meeting
    speakers      one row per public speaker (open comment or public hearing)
    motions       one row per motion × meeting
    member_votes  one row per member × motion, with vote_source = stated | inferred
                  and, for inferred rows, inference_basis = roll_call | attendance_note

See docs/data-dictionary.md for column definitions.
"""

from __future__ import annotations

import pandera.pandas as pa

from scripts.extraction_schema import ACTION_TYPES, MEETING_TYPES, MOTION_RESULTS

VOTES = ["yes", "no", "abstain", "absent"]
VOTE_SOURCES = ["stated", "inferred"]
INFERENCE_BASES = ["roll_call", "attendance_note"]
VOTE_INFERENCE = ["complete_as_stated", "inferred_from_roll_call", "inferred_with_item_exceptions",
                  "inferred_from_attendance_note", "partial_stated_only",
                  "inconsistent_not_inferred", "no_vote_recorded"]

_nullable_str = pa.Column(str, nullable=True)

meetings = pa.DataFrameSchema({
    "entry_id": pa.Column(int, unique=True),
    "meeting_date": pa.Column(str, pa.Check.str_matches(r"^\d{4}-\d{2}-\d{2}$")),
    "date_source": pa.Column(str, pa.Check.isin(["extracted", "document_name"])),
    "date_disagrees_with_name": pa.Column(bool),
    "meeting_type": pa.Column(str, pa.Check.isin(MEETING_TYPES)),
    "meeting_title": _nullable_str,
    "document_name": pa.Column(str),
    "location": _nullable_str,
    "called_to_order_time": _nullable_str,
    "adjourned_time": _nullable_str,
    "presiding_officer": _nullable_str,
    # Nine seats, but transition meetings after an election can list outgoing and
    # incoming members together (2001-11-13 lists ten), and joint meetings tempt the
    # extractor to count the other board's members. The audit flags > 9 for review
    # rather than failing the build, so mode comparisons can see the error.
    "n_members_present": pa.Column(int, pa.Check.in_range(0, 30)),
    "n_members_absent": pa.Column(int, pa.Check.in_range(0, 30)),
    "n_agenda_items": pa.Column(int),
    "n_motions": pa.Column(int),
    "page_count": pa.Column(float, nullable=True),
    "source_url": pa.Column(str),
    "extraction_mode": pa.Column(str),
    "schema_version": pa.Column(str),
}, strict=True)

attendance = pa.DataFrameSchema({
    "entry_id": pa.Column(int),
    "meeting_date": pa.Column(str),
    "member": pa.Column(str),
    "name_as_printed": pa.Column(str),
    "title": _nullable_str,
    "status": pa.Column(str, pa.Check.isin(["present", "absent"])),
    "note": _nullable_str,
}, strict=True, unique=["entry_id", "member"])

agenda_items = pa.DataFrameSchema({
    "entry_id": pa.Column(int),
    "item_seq": pa.Column(int),
    "item_number": _nullable_str,
    "item_key": _nullable_str,
    "section": _nullable_str,
    "title": _nullable_str,
    "ordinance_or_resolution_numbers": _nullable_str,
    "is_public_hearing": pa.Column(bool),
    "hearing_opened_time": _nullable_str,
    "hearing_closed_time": _nullable_str,
    "n_hearing_speakers": pa.Column(int),
    "outcome_summary": _nullable_str,
}, strict=True, unique=["entry_id", "item_seq"])

speakers = pa.DataFrameSchema({
    "entry_id": pa.Column(int),
    "context": pa.Column(str, pa.Check.isin(["open_comment", "public_hearing"])),
    "item_number": _nullable_str,
    "speaker_seq": pa.Column(int),
    "name": pa.Column(str),
    "topic": _nullable_str,
    "position": _nullable_str,
}, strict=True)

motions = pa.DataFrameSchema({
    "entry_id": pa.Column(int),
    "motion_seq": pa.Column(int),
    "agenda_item_number": _nullable_str,
    "item_key": _nullable_str,
    "motion_text": _nullable_str,
    "action_type": pa.Column(str, pa.Check.isin(ACTION_TYPES)),
    "ordinance_or_resolution_numbers": _nullable_str,
    "moved_by": _nullable_str,
    "seconded_by": _nullable_str,
    "vote_text": _nullable_str,
    "result": pa.Column(str, pa.Check.isin(MOTION_RESULTS)),
    "yes_count": pa.Column("Int64", nullable=True),
    "no_count": pa.Column("Int64", nullable=True),
    "stated_unanimous": pa.Column(bool),
    "vote_inference": pa.Column(str, pa.Check.isin(VOTE_INFERENCE)),
    "item_level_exceptions": _nullable_str,
    "n_yes": pa.Column(int),
    "n_no": pa.Column(int),
    "n_abstain": pa.Column(int),
    "n_absent": pa.Column(int),
}, strict=True, unique=["entry_id", "motion_seq"])

member_votes = pa.DataFrameSchema({
    "entry_id": pa.Column(int),
    "motion_seq": pa.Column(int),
    "member": pa.Column(str),
    "vote": pa.Column(str, pa.Check.isin(VOTES)),
    "vote_source": pa.Column(str, pa.Check.isin(VOTE_SOURCES)),
    "inference_basis": pa.Column(str, pa.Check.isin(INFERENCE_BASES), nullable=True),
}, strict=True, unique=["entry_id", "motion_seq", "member"],
    # An inferred row always says what it was inferred from; a stated row never does.
    checks=pa.Check(lambda df: (df["vote_source"] == "inferred") == df["inference_basis"].notna(),
                    name="inference_basis_iff_inferred"))

TABLES = {"meetings": meetings, "attendance": attendance, "agenda_items": agenda_items,
          "speakers": speakers, "motions": motions, "member_votes": member_votes}
