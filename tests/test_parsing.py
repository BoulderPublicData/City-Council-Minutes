from datetime import date

from scripts.discover import name_meeting_type, parse_name_date
from scripts.tidy import item_key, strip_meta


def test_parse_name_date_across_eras():
    assert parse_name_date("Minutes - Apr-01-2003") == date(2003, 4, 1)
    assert parse_name_date("City Council Minutes - 2018-12-04") == date(2018, 12, 4)
    assert parse_name_date("City Council Minutes - 12.01.20") == date(2020, 12, 1)
    assert parse_name_date("City Council Minutes - 12.14.2021") == date(2021, 12, 14)
    assert parse_name_date("Special Meeting January 5, 2010") == date(2010, 1, 5)
    assert parse_name_date("City Council Minutes - 2017 -10-24") == date(2017, 10, 24)
    assert parse_name_date("Index") is None


def test_name_meeting_type():
    assert name_meeting_type("Special Meeting Minutes - 2010-01-05") == "special"
    assert name_meeting_type("City Council Minutes - 12.01.20") is None


def test_item_key():
    assert item_key("5.A.") == item_key("5A") == item_key("5 (a)") == "5A"
    assert item_key(None) is None


def test_strip_meta():
    assert strip_meta({"a": 1, "a_citations": [], "a_meta": {}, "b": [{"c": 2, "c_meta": {}}]}) == \
        {"a": 1, "b": [{"c": 2}]}


def test_zip_member_names_match_entry_names():
    from scripts.fetch import name_key
    assert name_key("Minutes - Apr-09-2007.pdf") == name_key("Minutes - Apr-09-2007")
    assert name_key("ExportedContents/City Council Minutes - 12.01.20.PDF") == \
        name_key("City Council Minutes - 12.01.20")
    assert name_key("Minutes - Apr-09-2007") != name_key("Minutes - Aug-07-2007")
