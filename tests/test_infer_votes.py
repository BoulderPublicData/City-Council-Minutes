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
