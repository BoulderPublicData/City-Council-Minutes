"""Normalize council member names as printed in the minutes.

The minutes print members many ways: "Mayor Toor", "Councilmember Mock",
"Council Members Ageton and Corson", "Mayor Pro Tem Brockett", and OCR or
typing slips such as "Poinssatte" for Poinsatte. A member's key is their last
name, title-cased. Within one meeting, names are snapped to that meeting's own
roll call (present + absent) by fuzzy match, which repairs most slips without a
global roster. `data/lookups/member_aliases.csv` handles anything left over
(e.g. a member whose name changed, or two members sharing a last name).
"""

from __future__ import annotations

import difflib
import re
from functools import lru_cache

import pandas as pd

from scripts.config import MEMBER_ALIASES_CSV

_TITLES = re.compile(
    r"\b(mayor\s+pro\s+tem(?:pore)?|deputy\s+mayor|mayor|council\s*members?|council\s*women|"
    r"council\s*woman|council\s*men|council\s*man|council|members?|mr|mrs|ms|dr)\b\.?",
    re.IGNORECASE,
)


@lru_cache(maxsize=1)
def _aliases() -> dict[str, str]:
    if not MEMBER_ALIASES_CSV.exists():
        return {}
    df = pd.read_csv(MEMBER_ALIASES_CSV)
    return {str(a).strip().lower(): str(c).strip() for a, c in zip(df["alias"], df["member"], strict=True)}


def split_names(text: str | None) -> list[str]:
    """'Ageton and Corson' / 'Havlick, Morzel and Riggle' → separate names."""
    if not text:
        return []
    parts = re.split(r",|;|\band\b|&", text)
    return [p.strip() for p in parts if p.strip()]


_NOTE_DASH = re.compile(r"\s+[-–—]\s+")


def name_note(raw: str | None) -> str | None:
    """The note printed beside a roll-call name, if any: 'Yates - Late' → 'Late',
    'Folkerts – arrived 6:15' → 'arrived 6:15', 'Folkerts (virtual)' → 'virtual'.
    `member_key` drops these notes; tidy keeps them as the attendance note so vote
    inference can see late arrivals."""
    if not raw:
        return None
    parts = _NOTE_DASH.split(raw.strip(), maxsplit=1)
    if len(parts) == 2 and parts[1].strip():
        return parts[1].strip()
    paren = re.search(r"\(([^)]*)\)", parts[0])
    return (paren.group(1).strip() or None) if paren else None


def member_key(raw: str | None) -> str | None:
    """Last name, title-cased, with titles and punctuation removed."""
    if not raw:
        return None
    # Drop trailing notes: "Yates - Late", "Folkerts – arrived 6:15" (see `name_note`)
    s = _NOTE_DASH.split(raw.strip(), maxsplit=1)[0]
    s = _TITLES.sub(" ", s)
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"[^A-Za-z'\-\s]", " ", s)
    tokens = [t for t in s.split() if t.lower() not in {"pro", "tem", "the", "of"}]
    if not tokens:
        return None
    last = tokens[-1].strip("'-")
    if not last:
        return None
    key = last[0].upper() + last[1:].lower() if not last.isupper() else last.title()
    return _aliases().get(raw.strip().lower(), _aliases().get(key.lower(), key))


def snap(key: str | None, roster: list[str], cutoff: float = 0.8) -> str | None:
    """Snap a name to the meeting's roll call when it's a near miss (typos, OCR)."""
    if key is None or not roster or key in roster:
        return key
    match = difflib.get_close_matches(key, roster, n=1, cutoff=cutoff)
    return match[0] if match else key


def normalize_list(values: list[str] | None, roster: list[str]) -> list[str]:
    out: list[str] = []
    for v in values or []:
        for part in split_names(v):
            k = snap(member_key(part), roster)
            if k and k not in out:
                out.append(k)
    return out
