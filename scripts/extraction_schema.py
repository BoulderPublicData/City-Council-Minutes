"""The JSON schema Datalab fills for each set of signed minutes.

One schema covers every era. The minutes changed a lot between 2000 (typed
narrative, typed votes like "The motion carried 8-1, Council Member Ageton
dissenting") and the 2020s (templated sections with roll-call lists), so the
descriptions tell the extractor to record *what the minutes actually state*
and leave a field empty rather than guess. Filling in unstated per-member votes
is done later, deterministically, in `scripts/tidy.py`, where each inferred vote
is flagged — never by the extractor.

Bump SCHEMA_VERSION whenever a field or description changes; it is stored with
every extraction so results from different schema versions are never mixed
unknowingly.
"""

from __future__ import annotations

import json
from typing import Any

SCHEMA_VERSION = "2026-10-25.1"

MEETING_TYPES = ["regular", "special", "study_session", "retreat", "joint",
                 "continued", "adjourned", "executive_session", "other"]
MOTION_RESULTS = ["passed", "failed", "withdrawn", "tabled", "no_vote_recorded"]
ACTION_TYPES = ["consent_agenda", "approve_agenda", "approve_minutes", "ordinance", "resolution",
                "amendment", "appointment", "call_up", "continue_or_postpone",
                "executive_session", "adjourn", "direction_to_staff", "other"]

_names = {"type": "array", "items": {"type": "string"}}


def _s(desc: str) -> dict[str, Any]:
    return {"type": "string", "description": desc}


def _names_desc(desc: str) -> dict[str, Any]:
    return {**_names, "description": desc}


SCHEMA: dict[str, Any] = {
    "type": "object",
    "description": (
        "Signed minutes of one Boulder, Colorado City Council meeting. Record only what the "
        "minutes state. Write member names exactly as printed (usually last names). Leave a "
        "field empty or null when the minutes do not say; never infer votes that are not written."
    ),
    "properties": {
        "meeting_date": _s("Date of the meeting from the minutes heading, as YYYY-MM-DD."),
        "meeting_title": _s("The heading as printed, e.g. 'REGULAR MEETING' or "
                            "'SPECIAL MEETING / STUDY SESSION'."),
        "meeting_type": {"type": "string", "enum": MEETING_TYPES,
                         "description": "Kind of meeting, from the heading."},
        "location": _s("Where the meeting was held, e.g. 'Council Chambers, 1777 Broadway' or 'virtual'."),
        "called_to_order_time": _s("Time the meeting was called to order, as printed, e.g. '6:03 p.m.'."),
        "adjourned_time": _s("Time the meeting adjourned, as printed."),
        "presiding_officer": _s("Name of the person who called the meeting to order or presided."),
        "members_present": {
            "type": "array",
            "description": "Council members recorded as present at roll call (including the mayor). "
                           "Include members noted as arriving late.",
            "items": {"type": "object", "properties": {
                "name": _s("Member name as printed."),
                "title": _s("Mayor, Mayor Pro Tem, or Council Member, as printed."),
                "attendance_note": _s("Any note such as 'arrived at 6:45 p.m.', 'left at 9:30 p.m.', "
                                      "or 'participated remotely'. Empty if none."),
            }},
        },
        "members_absent": {
            "type": "array",
            "description": "Council members recorded as absent at roll call.",
            "items": {"type": "object", "properties": {
                "name": _s("Member name as printed."),
                "note": _s("Any note such as 'excused'."),
            }},
        },
        "open_comment_speakers": {
            "type": "array",
            "description": "Members of the public who spoke during open comment (not at a "
                           "public hearing), in order.",
            "items": {"type": "object", "properties": {
                "name": _s("Speaker name as printed."),
                "topic": _s("Short summary of what they spoke about."),
            }},
        },
        "agenda_items": {
            "type": "array",
            "description": "Every numbered or lettered agenda item in the minutes, in order, "
                           "including consent agenda sub-items.",
            "items": {"type": "object", "properties": {
                "item_number": _s("Item number as printed, e.g. '3', '5.A', 'B'."),
                "section": _s("Section heading the item falls under, as printed, e.g. "
                              "'CONSENT AGENDA', 'PUBLIC HEARINGS', 'MATTERS FROM THE CITY MANAGER', "
                              "'CALL-UPS', 'ORDINANCES - FIRST READING'."),
                "title": _s("Item title or description as printed (may be long)."),
                "ordinance_or_resolution_numbers": _names_desc(
                    "Ordinance or resolution numbers named in the item, e.g. ['8523'] or ['Res. 1295']."),
                "is_public_hearing": {"type": "boolean",
                                      "description": "True if the item was a public hearing."},
                "hearing_opened_time": _s("Time the public hearing opened, if stated."),
                "hearing_closed_time": _s("Time the public hearing closed, if stated."),
                "hearing_speakers": {
                    "type": "array",
                    "description": "Members of the public who spoke at this item's public hearing.",
                    "items": {"type": "object", "properties": {
                        "name": _s("Speaker name as printed."),
                        "position": {"type": "string", "enum": ["for", "against", "neutral", "unstated"],
                                     "description": "Position, only if the minutes state it."},
                    }},
                },
                "outcome_summary": _s("One sentence on what council did with the item."),
            }},
        },
        "motions": {
            "type": "array",
            "description": "Every motion made, in order, including motions to approve the consent "
                           "agenda, amendments, and procedural motions.",
            "items": {"type": "object", "properties": {
                "agenda_item_number": _s("Agenda item the motion belongs to, as printed."),
                "motion_text": _s("The motion as written in the minutes."),
                "action_type": {"type": "string", "enum": ACTION_TYPES,
                                "description": "What kind of action the motion is."},
                "ordinance_or_resolution_numbers": _names_desc(
                    "Ordinance or resolution numbers the motion acts on."),
                "moved_by": _s("Member who made the motion."),
                "seconded_by": _s("Member who seconded the motion."),
                "vote_text": _s("The vote sentence exactly as written, e.g. 'The motion carried 7:2; "
                                "Council Members Ageton and Corson dissenting.'"),
                "result": {"type": "string", "enum": MOTION_RESULTS,
                           "description": "Outcome as stated."},
                "yes_count": {"type": ["integer", "null"], "description": "Number of yes votes if stated."},
                "no_count": {"type": ["integer", "null"], "description": "Number of no votes if stated."},
                "stated_unanimous": {"type": "boolean",
                                     "description": "True only if the minutes say unanimous / all "
                                                    "present voted yes / a count with zero no votes."},
                "yes_votes": _names_desc("Members the minutes name as voting yes. Empty if not named."),
                "no_votes": _names_desc("Members the minutes name as voting no or dissenting."),
                "abstained": _names_desc("Members the minutes name as abstaining or recused."),
                "absent_or_not_voting": _names_desc(
                    "Members the minutes name as absent, not present, or not voting for this motion."),
            }},
        },
        "call_up_items": _names_desc("Items listed as call-ups or call-up check-ins from boards "
                                     "and commissions."),
    },
    "required": ["meeting_date", "members_present", "motions"],
}


def schema_json() -> str:
    return json.dumps(SCHEMA)
