import pandas as pd

from scripts import schema
from scripts.tidy import tidy_one

ENTRY = {"entry_id": 151897, "name": "Minutes - Apr-01-2003", "name_date": "2003-04-01",
         "name_meeting_type": None, "page_count": 6.0,
         "docview_url": "https://documents.bouldercolorado.gov/WebLink/DocView.aspx?id=151897&dbid=0&repo=LF8PROD2"}


def test_tidy_one_2003(extraction_2003):
    t = tidy_one(ENTRY, extraction_2003, "balanced", "test")
    m = t["meetings"][0]
    assert m["meeting_date"] == "2003-04-01"
    assert m["n_members_present"] == 9
    motions = pd.DataFrame(t["motions"])
    split = motions[motions["yes_count"] == 6].iloc[0]
    assert split["vote_inference"] == "inferred_from_roll_call"
    assert (split["n_yes"], split["n_no"]) == (6, 3)
    # the minutes' typo "Poinssatte" is snapped to the roll call spelling
    assert "Poinssatte" not in set(motions["seconded_by"].dropna())


def test_tidy_tables_validate(extraction_2003):
    t = tidy_one(ENTRY, extraction_2003, "balanced", "test")
    for name, sch in schema.TABLES.items():
        df = pd.DataFrame(t[name], columns=list(sch.columns) + (["_call_ups"] if name == "meetings" else []))
        df = df.drop(columns=["_call_ups"], errors="ignore")
        for col, c in sch.columns.items():
            if str(c.dtype) == "Int64":
                df[col] = df[col].astype("Int64")
        sch.validate(df)


def test_nested_export_has_no_nan(extraction_2003):
    import json

    from scripts.tidy import nested_meeting
    t = tidy_one(ENTRY, extraction_2003, "balanced", "test")
    tables = {name: pd.DataFrame(rows) for name, rows in t.items()}
    out = json.dumps(nested_meeting(tables, 151897))
    assert "NaN" not in out


def test_late_marker_on_roll_call_reaches_inference():
    # "Yates - Late" on the roll call; the consent agenda carried 8:0 with nine listed
    names = ["Weaver", "Friend", "Brockett", "Joseph", "Nagle", "Swetlik", "Wallach", "Young"]
    doc = {"meeting_date": "2022-04-05",
           "members_present": [{"name": n} for n in names] + [{"name": "Yates - Late"}],
           "members_absent": [],
           "motions": [{"vote_text": "Carried 8:0", "yes_count": 8, "no_count": 0,
                        "stated_unanimous": True, "result": "passed",
                        "action_type": "consent_agenda"},
                       {"vote_text": "Carried 9:0", "yes_count": 9, "no_count": 0,
                        "stated_unanimous": True, "result": "passed"}]}
    t = tidy_one(ENTRY, doc, "balanced", "test")
    att = {a["member"]: a["note"] for a in t["attendance"]}
    assert att["Yates"] == "Late"
    mot = {m["motion_seq"]: m for m in t["motions"]}
    assert mot[1]["vote_inference"] == "inferred_from_attendance_note"
    assert mot[2]["vote_inference"] == "inferred_from_roll_call"
    votes = pd.DataFrame(t["member_votes"])
    first = votes[votes["motion_seq"] == 1]
    assert "Yates" not in set(first["member"]) and len(first) == 8
    assert set(first["inference_basis"]) == {"attendance_note"}
    assert set(votes[votes["motion_seq"] == 2]["inference_basis"]) == {"roll_call"}
    schema.member_votes.validate(votes)


def test_member_votes_contract_requires_basis_on_inferred_rows():
    import pandera.errors
    import pytest
    bad = pd.DataFrame([{"entry_id": 1, "motion_seq": 1, "member": "Toor", "vote": "yes",
                         "vote_source": "inferred", "inference_basis": None}])
    with pytest.raises(pandera.errors.SchemaError):
        schema.member_votes.validate(bad)


def test_late_arrival_seen_acting_earlier_is_not_left_out():
    # 2003-08-05 (entry 151899): Morzel "arrived at 7:10 p.m.", moved motion 1, and
    # motion 2 still carried 6:0 with seven present. The gap isn't hers: decline.
    names = ["Corson", "Havlick", "Mock", "Poinsatte", "Riggle", "Ruzzin"]
    doc = {"meeting_date": "2003-08-05",
           "members_present": [{"name": n} for n in names]
           + [{"name": "Morzel", "attendance_note": "arrived at 7:10 p.m."}],
           "members_absent": [{"name": "Toor"}, {"name": "Eldridge"}],
           "motions": [{"vote_text": "The motion carried 6:0, Eldridge and Toor absent",
                        "yes_count": 6, "no_count": 0, "moved_by": "Morzel", "seconded_by": "Corson",
                        "absent_or_not_voting": ["Eldridge", "Toor"], "result": "passed"},
                       {"vote_text": "The motion carried 6 0; Eldridge and Toor absent.",
                        "yes_count": 6, "no_count": 0, "moved_by": "Corson", "seconded_by": "Riggle",
                        "absent_or_not_voting": ["Eldridge", "Toor"], "result": "passed"}]}
    t = tidy_one(ENTRY, doc, "balanced", "test")
    assert [m["vote_inference"] for m in t["motions"]] == ["inconsistent_not_inferred"] * 2


# ── roll-call plausibility ──────────────────────────────────────────────────

COUNCIL_2022 = ["Brockett", "Benjamin", "Folkerts", "Friend", "Joseph", "Speer", "Wallach",
                "Winer", "Yates"]


def test_non_members_drops_uncorroborated_names():
    from scripts.tidy import non_members
    present = [{"name": n, "title": "Council Member"} for n in COUNCIL_2022]
    absent = [{"name": "Fred Bratman", "note": "DID NOT SHOW"},
              {"name": "Kate Weiner", "note": "DID NOT SHOW"},   # near 'Winer', who is here
              {"name": "Joseph"}]                                # no title, but known nearby
    drop = non_members(present, absent, [], nearby=set(COUNCIL_2022))
    assert set(drop) == {"Bratman", "Weiner"}


def test_non_members_keeps_misspellings_actors_and_titles():
    from scripts.tidy import non_members
    nearby = {"Morzel", "Corson", "Toor", "Eldridge"}
    present = [{"name": "Corson"}, {"name": "Moizel"},              # OCR slip for Morzel
               {"name": "Greenlee", "title": "Councilmembers"},     # titled
               {"name": "Riggle"}]                                  # moves a motion
    absent = [{"name": "Toor"}]
    motions = [{"moved_by": "Riggle", "seconded_by": "Corson"}]
    assert non_members(present, absent, motions, nearby) == {}


def test_non_members_drops_other_bodies_by_title():
    from scripts.tidy import non_members
    present = [{"name": "Gray", "title": "Planning Board Member"},
               {"name": "Brockett", "title": "Mayor"}]
    drop = non_members(present, [], [], nearby={"Gray", "Brockett"})
    assert set(drop) == {"Gray"} and "another body" in drop["Gray"]


def test_tidy_one_drops_speakers_from_roll_call_and_votes():
    doc = {"meeting_date": "2022-04-05",
           "members_present": [{"name": n, "title": "Council Member"} for n in COUNCIL_2022],
           "members_absent": [{"name": "John Walker", "note": "DID NOT SHOW"}],
           "motions": [{"vote_text": "Carried 9:0", "yes_count": 9, "no_count": 0,
                        "stated_unanimous": True, "result": "passed"}]}
    kept = tidy_one(ENTRY, doc, "balanced", "test")  # no roster context: nothing dropped
    assert "Walker" in {a["member"] for a in kept["attendance"]}
    t = tidy_one(ENTRY, doc, "balanced", "test", nearby=set(COUNCIL_2022))
    assert "Walker" not in {a["member"] for a in t["attendance"]}
    assert "Walker" not in {v["member"] for v in t["member_votes"]}
    assert t["meetings"][0]["n_members_absent"] == 0
    assert [x["member"] for x in t["excluded_roll_call"]] == ["Walker"]
    assert t["motions"][0]["vote_inference"] == "inferred_from_roll_call"
