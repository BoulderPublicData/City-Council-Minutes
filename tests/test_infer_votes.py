from scripts.tidy import infer_votes

NINE = ["Toor", "Corson", "Eldridge", "Havlick", "Mock", "Morzel", "Poinsatte", "Riggle", "Ruzzin"]


def _votes(rows):
    return {m: (v, s) for m, v, s in rows}


def test_tally_with_named_dissenters_infers_yes():
    rows, label = infer_votes(NINE, [], {"vote_text": "carried 6:3, Havlick, Morzel and Riggle opposed",
                                         "yes_count": 6, "no_count": 3,
                                         "no_votes": ["Havlick", "Morzel", "Riggle"], "result": "passed"})
    v = _votes(rows)
    assert label == "inferred_from_roll_call"
    assert v["Havlick"] == ("no", "stated")
    assert v["Toor"] == ("yes", "inferred")
    assert sum(1 for x in v.values() if x[0] == "yes") == 6


def test_roll_call_absentee_is_inferred_absent():
    rows, label = infer_votes(NINE[:8], ["Ruzzin"], {"vote_text": "carried 8:0", "yes_count": 8,
                                                     "no_count": 0, "result": "passed"})
    assert label == "inferred_from_roll_call"
    assert _votes(rows)["Ruzzin"] == ("absent", "inferred")


def test_count_mismatch_refuses_to_infer():
    # Nine present but the minutes say 7:1 — someone left; don't guess who
    rows, label = infer_votes(NINE, [], {"vote_text": "carried 7:1, Mock opposed", "yes_count": 7,
                                         "no_count": 1, "no_votes": ["Mock"], "result": "passed"})
    assert label == "inconsistent_not_inferred"
    assert rows == [("Mock", "no", "stated")]


def test_explicit_partial_yes_list_is_not_completed():
    rows, label = infer_votes(NINE, [], {"vote_text": "Yes: Toor, Corson", "yes_votes": ["Toor", "Corson"],
                                         "result": "passed"})
    assert label == "partial_stated_only"
    assert {m for m, _, _ in rows} == {"Toor", "Corson"}


def test_no_vote_recorded():
    rows, label = infer_votes(NINE, [], {"motion_text": "BY MOTION REGULARLY ADOPTED, adjourned",
                                         "result": "passed"})
    assert label == "no_vote_recorded" and rows == []


def test_unanimous_with_named_no_is_inconsistent():
    _, label = infer_votes(NINE, [], {"vote_text": "unanimous", "stated_unanimous": True,
                                      "no_votes": ["Mock"], "result": "passed"})
    assert label == "inconsistent_not_inferred"


def test_item_level_recusal_beside_full_tally():
    eight = NINE[:8]
    m = {"vote_text": "Carried 8:0 ABSTAINED: Toor, Mock", "yes_count": 8, "no_count": 0,
         "abstained": ["Toor", "Mock"], "result": "passed"}
    rows, label = infer_votes(eight, ["Ruzzin"], m)
    assert label == "inferred_with_item_exceptions"
    v = _votes(rows)
    assert v["Toor"] == ("yes", "inferred") and v["Ruzzin"] == ("absent", "inferred")
    from scripts.tidy import item_exceptions
    assert item_exceptions(eight, ["Ruzzin"], m) == "Toor: abstain; Mock: abstain"


def test_item_level_nay_beside_unanimous_tally():
    rows, label = infer_votes(NINE, [], {"vote_text": "Carried 9:0 NAY: Mock on Item F",
                                         "yes_count": 9, "no_count": 0, "no_votes": ["Mock"],
                                         "result": "passed"})
    assert label == "inferred_with_item_exceptions"
    assert _votes(rows)["Mock"] == ("yes", "inferred")


# ── late arrivals and early departures (attendance notes) ───────────────────

def test_attendance_change_reads_notes():
    from scripts.tidy import attendance_change
    assert attendance_change("arrived at 6:45 p.m.") == "arrived"
    assert attendance_change("Late") == "arrived"
    assert attendance_change("joined the meeting at 6:26 p.m.") == "arrived"
    assert attendance_change("left the meeting at 8:20 p.m.") == "left"
    assert attendance_change("RECUSED herself from item 4B and left the meeting at 7:44 p.m.") == "left"
    assert attendance_change("present virtually") is None
    assert attendance_change("excused") is None
    assert attendance_change("did not arrive") is None
    assert attendance_change("has not yet arrived") is None
    assert attendance_change("not present at time of attendance; arrived at 6:16 p.m.") == "arrived"
    assert attendance_change("may need to step away for 15-20 minutes") is None
    assert attendance_change(None) is None


def test_tally_lower_than_roll_call_with_late_arrival_infers_the_rest():
    # 8:0 with nine present at roll call; Toor's note says he arrived late
    m = {"vote_text": "Carried 8:0", "yes_count": 8, "no_count": 0, "stated_unanimous": True,
         "result": "passed"}
    rows, label = infer_votes(NINE, [], m, {"Toor": "arrived at 8:06 p.m."})
    v = _votes(rows)
    assert label == "inferred_from_attendance_note"
    assert "Toor" not in v
    assert all(v[x] == ("yes", "inferred") for x in NINE[1:])
    assert len(v) == 8


def test_tally_lower_than_roll_call_with_early_departure_and_named_nays():
    # 5:3 with nine present; Mock left early; the three nays are named
    m = {"vote_text": "carried 5:3, Havlick, Morzel and Riggle opposed", "yes_count": 5,
         "no_count": 3, "no_votes": ["Havlick", "Morzel", "Riggle"], "result": "passed"}
    rows, label = infer_votes(NINE, [], m, {"Mock": "left at 9:30 p.m."})
    v = _votes(rows)
    assert label == "inferred_from_attendance_note"
    assert "Mock" not in v
    assert v["Havlick"] == ("no", "stated")
    assert sum(1 for x in v.values() if x == ("yes", "inferred")) == 5


def test_tally_lower_one_late_one_left_gap_two():
    m = {"vote_text": "carried 7:0", "yes_count": 7, "no_count": 0, "result": "passed"}
    rows, label = infer_votes(NINE, [], m, {"Toor": "Late", "Ruzzin": "left the meeting at 10 p.m."})
    v = _votes(rows)
    assert label == "inferred_from_attendance_note"
    assert set(v) == set(NINE) - {"Toor", "Ruzzin"}


def test_tally_higher_than_roll_call_counts_late_absentee_present():
    # Ruzzin was absent at roll call, arrived later, and the tally is 9:0
    m = {"vote_text": "carried 9:0", "yes_count": 9, "no_count": 0, "result": "passed"}
    rows, label = infer_votes(NINE[:8], ["Ruzzin"], m, {"Ruzzin": "arrived at 7:15 p.m."})
    v = _votes(rows)
    assert label == "inferred_from_attendance_note"
    assert v["Ruzzin"] == ("yes", "inferred")
    assert len(v) == 9 and all(x == ("yes", "inferred") for x in v.values())


def test_tally_higher_keeps_other_absentees_absent():
    m = {"vote_text": "carried 8:0", "yes_count": 8, "no_count": 0, "result": "passed"}
    rows, label = infer_votes(NINE[:7], ["Riggle", "Ruzzin"], m, {"Riggle": "arrived late"})
    v = _votes(rows)
    assert label == "inferred_from_attendance_note"
    assert v["Riggle"] == ("yes", "inferred") and v["Ruzzin"] == ("absent", "inferred")


def test_tally_higher_without_an_arrival_note_still_declines():
    m = {"vote_text": "carried 9:0", "yes_count": 9, "no_count": 0, "result": "passed"}
    rows, label = infer_votes(NINE[:8], ["Ruzzin"], m, {"Ruzzin": "excused"})
    assert label == "inconsistent_not_inferred" and rows == []


def test_gap_not_matching_noted_members_declines():
    # 7:0 with nine present but only one member noted: someone else is unaccounted for
    m = {"vote_text": "carried 7:0", "yes_count": 7, "no_count": 0, "result": "passed"}
    rows, label = infer_votes(NINE, [], m, {"Toor": "arrived at 6:45 p.m."})
    assert label == "inconsistent_not_inferred" and rows == []


def test_ambiguous_tie_declines():
    # 4:4 tie with nine present, nays named; two members are noted (one late, one left)
    # but the gap is one, so either could have been the one missing: don't guess
    m = {"vote_text": "failed 4:4; Corson, Eldridge, Havlick and Mock opposed", "yes_count": 4,
         "no_count": 4, "no_votes": ["Corson", "Eldridge", "Havlick", "Mock"], "result": "failed"}
    notes = {"Toor": "arrived at 6:45 p.m.", "Ruzzin": "left at 9:30 p.m."}
    rows, label = infer_votes(NINE, [], m, notes)
    assert label == "inconsistent_not_inferred"
    assert all(src == "stated" for _, _, src in rows) and len(rows) == 4


def test_tie_with_unnamed_nays_declines():
    # A 4:4 tie that names no one can't be split between yes and no, notes or not
    m = {"vote_text": "failed 4:4", "yes_count": 4, "no_count": 4, "result": "failed"}
    rows, label = infer_votes(NINE, [], m, {"Toor": "Late"})
    assert label == "inconsistent_not_inferred" and rows == []


def test_notes_do_not_change_motions_that_already_reconcile():
    # 9:0 with nine present: the late arrival must have voted, as before
    m = {"vote_text": "carried 9:0", "yes_count": 9, "no_count": 0, "result": "passed"}
    notes = {"Toor": "arrived at 6:45 p.m.", "Mock": "left at 9:30 p.m."}
    assert infer_votes(NINE, [], m, notes) == infer_votes(NINE, [], m)
    rows, label = infer_votes(NINE, [], m, notes)
    assert label == "inferred_from_roll_call" and _votes(rows)["Toor"] == ("yes", "inferred")
    # and the other existing labels are unchanged too
    m2 = {"vote_text": "Carried 9:0 NAY: Mock on Item F", "yes_count": 9, "no_count": 0,
          "no_votes": ["Mock"], "result": "passed"}
    assert infer_votes(NINE, [], m2, notes) == infer_votes(NINE, [], m2)
    m3 = {"vote_text": "carried 6:3, Havlick, Morzel and Riggle opposed", "yes_count": 6,
          "no_count": 3, "no_votes": ["Havlick", "Morzel", "Riggle"], "result": "passed"}
    assert infer_votes(NINE, [], m3, notes) == infer_votes(NINE, [], m3)


def test_unanimous_with_named_no_still_inconsistent_with_notes():
    _, label = infer_votes(NINE, [], {"vote_text": "unanimous", "stated_unanimous": True,
                                      "yes_count": 8, "no_votes": ["Mock"], "result": "passed"},
                           {"Toor": "Late"})
    assert label == "inconsistent_not_inferred"


def test_late_member_who_moved_the_motion_is_not_away():
    # 6:0 with seven present; Toor is noted as arriving late but moved this motion, so
    # the missing vote is someone else's: decline (2003-08-05, entry 151899)
    m = {"vote_text": "carried 6:0", "yes_count": 6, "no_count": 0, "moved_by": "Toor",
         "seconded_by": "Corson", "result": "passed"}
    rows, label = infer_votes(NINE[:7], NINE[7:], m, {"Toor": "arrived at 7:10 p.m."})
    assert label == "inconsistent_not_inferred" and rows == []


def test_away_notes_uses_other_motions_as_evidence():
    from scripts.tidy import away_notes
    notes = {"Toor": "arrived at 7:10 p.m.", "Mock": "left at 9:30 p.m.",
             "Ruzzin": "arrived at 8 p.m."}
    motions = [{"moved_by": "Corson"},                       # 1: Toor not seen yet
               {"moved_by": "Toor", "seconded_by": "Mock"},   # 2: Toor has arrived; Mock still here
               {"no_votes": ["Havlick"]},                     # 3: Toor here; Mock not seen again
               {}]
    out = away_notes(motions, NINE[:8], ["Ruzzin"], notes)
    assert set(out[0]) == {"Toor", "Ruzzin"}            # Mock acts later: hasn't left yet
    # the motion's own mover/seconder are left to infer_votes, which sees the motion
    assert set(out[1]) == {"Toor", "Mock", "Ruzzin"}
    assert set(out[2]) == {"Mock", "Ruzzin"}             # Toor moved motion 2: has arrived
    assert set(out[3]) == {"Mock", "Ruzzin"}
    # roll-call absentees keep their arrival notes for the tally-higher case
    assert all("Ruzzin" in o for o in out)
