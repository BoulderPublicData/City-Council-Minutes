from scripts.names import member_key, normalize_list, snap, split_names


def test_member_key_strips_titles():
    assert member_key("Mayor Toor") == "Toor"
    assert member_key("Councilmember Mock") == "Mock"
    assert member_key("Mayor Pro Tem Brockett") == "Brockett"
    assert member_key("Council Member Speer") == "Speer"
    assert member_key("Brockett,") == "Brockett"
    assert member_key("") is None


def test_split_names():
    assert split_names("Havlick, Morzel and Riggle") == ["Havlick", "Morzel", "Riggle"]


def test_snap_repairs_typos_to_roll_call():
    assert snap("Poinssatte", ["Poinsatte", "Toor"]) == "Poinsatte"
    assert snap("Nobody", ["Poinsatte", "Toor"]) == "Nobody"


def test_normalize_list_dedupes_and_splits():
    assert normalize_list(["Ageton and Corson", "Corson"], ["Ageton", "Corson"]) == ["Ageton", "Corson"]
